#!/usr/bin/env python3
"""Prepare time-aligned V2V inputs and strict side-by-side comparisons (ffmpeg).

Usage (run from workspace root):
  python scripts/v2v_compare.py prepare --source SOURCE.mp4 \
    --start 240 --out OUTPUT_DIR --fps 16 --frames 81
  python scripts/v2v_compare.py compare --reference reference.mp4 \
    --result generated.mp4 --out comparison.mp4

prepare preserves source motion/speed, samples CFR frames, saves first/mid/last
images, a Canny control clip and provenance. compare rejects timing/size mismatch;
it never silently retimes, pads, stabilizes, warps or interpolates AI results.
Requires ffmpeg/ffprobe on PATH. No network or model inference.
"""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def probe(path):
    data = json.loads(run([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
        "-show_streams", "-show_format", "-of", "json", str(path),
    ]))
    if not data.get("streams"):
        raise ValueError(f"No video: {path}")
    stream = data["streams"][0]
    fps = Fraction(stream["avg_frame_rate"])
    rate = Fraction(stream["r_frame_rate"])
    return dict(width=stream["width"], height=stream["height"], fps=str(fps),
                nominal_fps=str(rate), frames=int(stream["nb_read_frames"]),
                duration=float(stream.get("duration", data["format"]["duration"])))


def ffmpeg(args):
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", *args])


def encode_args():
    return ["-an", "-map_metadata", "-1", "-c:v", "libx264", "-preset", "fast",
            "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def check_spec(spec, width, height, fps, frames):
    if (spec["width"], spec["height"], Fraction(spec["fps"]), spec["frames"]) != (
            width, height, Fraction(fps), frames):
        raise ValueError(f"Unexpected output specification: {spec}")


def prepare(args):
    source = Path(args.source).resolve()
    if not source.is_file():
        raise ValueError(f"Missing source: {source}")
    if args.frames < 5 or (args.frames - 1) % 4:
        raise ValueError("--frames must be 4n+1, at least 5")
    if args.fps <= 0 or args.start < 0 or min(args.width, args.height) < 16:
        raise ValueError("Invalid start/fps/size")
    if args.width % 16 or args.height % 16:
        raise ValueError("Dimensions must be divisible by 16")
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    clip = out / "reference.mp4"
    # Resize to cover, then one fixed central crop; no stabilization or speed change.
    filters = (f"fps={args.fps},scale={args.width}:{args.height}:"
               f"force_original_aspect_ratio=increase,crop={args.width}:{args.height},"
               "setsar=1,setpts=PTS-STARTPTS")
    ffmpeg(["-ss", str(args.start), "-i", str(source), "-vf", filters,
            "-frames:v", str(args.frames), *encode_args(), str(clip)])
    spec = probe(clip)
    check_spec(spec, args.width, args.height, args.fps, args.frames)
    picks = [("first", 0), ("middle", args.frames // 2), ("last", args.frames - 1)]
    for name, index in picks:
        ffmpeg(["-i", str(clip), "-vf", f"select=eq(n\\,{index})", "-frames:v", "1",
                "-update", "1", str(out / f"{name}.png")])
    # Technical guide only: a Canny control sequence, not a night transformation.
    ffmpeg(["-i", str(clip), "-vf",
            "format=gray,edgedetect=low=0.08:high=0.20:mode=wires,format=yuv420p",
            "-frames:v", str(args.frames), *encode_args(), str(out / "control_canny.mp4")])
    control = probe(out / "control_canny.mp4")
    check_spec(control, args.width, args.height, args.fps, args.frames)
    metadata = dict(source=str(source), source_start_seconds=args.start,
                    source_last_sample_seconds=args.start + (args.frames - 1) / args.fps,
                    sampling="CFR, unchanged playback speed; fixed centered crop; audio removed",
                    reference=spec, sha256=hashlib.sha256(clip.read_bytes()).hexdigest(),
                    control="FFmpeg Canny, low=0.08 high=0.20, lossy H264 preview/control",
                    artifacts=["reference.mp4", "control_canny.mp4", "first.png", "middle.png", "last.png"])
    (out / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


def compare(args):
    ref, result, out = map(lambda x: Path(x).resolve(), (args.reference, args.result, args.out))
    if out in (ref, result):
        raise ValueError("Output must differ from both inputs")
    left, right = probe(ref), probe(result)
    for key in ("width", "height", "fps", "frames"):
        if left[key] != right[key]:
            raise ValueError(f"Mismatch {key}: reference={left[key]} result={right[key]}. "
                             "Export the matching generated frame sequence; no automatic retiming.")
    fps = Fraction(left["fps"])
    # Check decoded frame cadence too, so VFR is not silently made CFR below.
    for path in (ref, result):
        raw = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
                   "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(path)])
        stamps = [float(f["best_effort_timestamp_time"]) for f in json.loads(raw)["frames"]]
        if any(abs((b - a) - 1 / float(fps)) > 0.002 for a, b in zip(stamps, stamps[1:])):
            raise ValueError(f"Variable frame cadence: {path}")
    out.parent.mkdir(parents=True, exist_ok=True)
    # PTS reset only removes container timestamp origin; frame indices/speed stay intact.
    filters = ("[0:v]setpts=PTS-STARTPTS,setsar=1[l];"
               "[1:v]setpts=PTS-STARTPTS,setsar=1[r];"
               "[l][r]hstack=inputs=2,pad=iw:ih+48:0:48:black[base];"
               "[base][2:v]overlay=0:0:eof_action=repeat[v]")
    # Pillow header works with ffmpeg builds that omit libfreetype/drawtext.
    with tempfile.TemporaryDirectory(prefix="v2v-compare-") as tmp:
        header = Path(tmp) / "labels.png"
        banner = Image.new("RGB", (left["width"] * 2, 48), "black")
        draw = ImageDraw.Draw(banner)
        font = ImageFont.load_default(size=24)
        draw.text((16, 10), "SOURCE", font=font, fill="white")
        draw.text((left["width"] + 16, 10), args.result_label, font=font, fill="white")
        banner.save(header)
        ffmpeg(["-i", str(ref), "-i", str(result), "-i", str(header),
                "-filter_complex", filters, "-map", "[v]", "-frames:v", str(left["frames"]),
                "-r", str(fps), *encode_args(), str(out)])
    rendered = probe(out)
    check_spec(rendered, left["width"] * 2, left["height"] + 48, fps, left["frames"])
    report = dict(reference=str(ref), result=str(result), output=str(out),
                  reference_spec=left, result_spec=right, comparison_spec=rendered,
                  alignment="frame n left versus frame n right; no temporal correction",
                  semantic_alignment="Not guaranteed: inspect landmarks and motion visually")
    out.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = parser.add_subparsers(dest="command", required=True)
    prep = subs.add_parser("prepare", help="Extract reference/control clips and provenance")
    prep.add_argument("--source", required=True)
    prep.add_argument("--start", type=float, required=True)
    prep.add_argument("--out", required=True)
    prep.add_argument("--fps", type=int, default=16)
    prep.add_argument("--frames", type=int, default=81)
    prep.add_argument("--width", type=int, default=832)
    prep.add_argument("--height", type=int, default=480)
    prep.set_defaults(func=prepare)
    comp = subs.add_parser("compare", help="Render strictly aligned SOURCE / RESULT")
    comp.add_argument("--reference", required=True)
    comp.add_argument("--result", required=True)
    comp.add_argument("--out", required=True)
    comp.add_argument("--result-label", default="RESULT", help="Header label; use CONTROL for previews")
    comp.set_defaults(func=compare)
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + ("\n" + exc.stderr[-2000:] if isinstance(exc, subprocess.CalledProcessError) else "") + "\n")


if __name__ == "__main__":
    main()

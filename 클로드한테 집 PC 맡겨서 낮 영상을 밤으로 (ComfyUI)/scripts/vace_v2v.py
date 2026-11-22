"""Wan2.1 VACE 1.3B로 영상→영상(밤 변환 등)을 ComfyUI API에 한 건 제출하고 결과·지표를 저장한다.

두 방식을 옵션으로 조합한다.
  --first-frame IMG : 0번 프레임을 IMG로 고정(mask 0), 나머지 프레임은 --control(mask 1)로 생성
  --source VID --denoise 0.65 : 원본 영상을 VAE 인코딩한 latent에서 시작(저-denoise V2V)
둘 다 주면 첫 프레임 고정 + 원본 latent 시작. --control은 항상 필요(Canny 등 제어 영상).

사용법 (이 폴더에서, ComfyUI가 127.0.0.1:8188에서 실행 중):
  python scripts/vace_v2v.py --name A_ff --control ctrl.mp4 \\
      --first-frame night.png --prompt-file p.txt --negative-file n.txt --out results/dir
  python scripts/vace_v2v.py --name B_v2v --control ctrl.mp4 \\
      --source src.mp4 --denoise 0.65 --prompt-file p.txt --negative-file n.txt --out results/dir
  --compare REF.mp4 를 주면 scripts/v2v_compare.py로 좌우 비교 영상과 대표 프레임을 만든다.

같은 --name의 metrics 파일이 있으면 중복 제출을 거부한다. 큐가 비어 있지 않으면 제출하지 않는다.
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from comfy_api import upload  # noqa: E402
from v2v_compare import probe  # noqa: E402


def call(host, path, data=None):
    req = urllib.request.Request(host + path, json.dumps(data).encode() if data is not None else None,
                                 {'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(exc.read().decode()) from exc


def make_mask_video(path, frames, width, height, fps):
    """0번 프레임 검정(유지), 나머지 흰색(생성)인 무손실 마스크 영상."""
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y',
        '-f', 'lavfi', '-i', f'color=c=black:s={width}x{height}:r={fps}',
        '-f', 'lavfi', '-i', f'color=c=white:s={width}x{height}:r={fps}',
        '-filter_complex', f'[0]trim=end_frame=1[a];[1]trim=end_frame={frames - 1}[b];[a][b]concat=n=2:v=1[v]',
        '-map', '[v]', '-c:v', 'libx264', '-qp', '0', '-pix_fmt', 'yuv444p', str(path)], check=True)


def build_graph(a, names, frames):
    g = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': a.unet, 'weight_dtype': 'default'}},
        '2': {'class_type': 'ModelSamplingSD3', 'inputs': {'shift': a.shift, 'model': ['1', 0]}},
        '3': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': a.clip, 'type': 'wan', 'device': 'default'}},
        '4': {'class_type': 'VAELoader', 'inputs': {'vae_name': a.vae}},
        '5': {'class_type': 'CLIPTextEncode', 'inputs': {'text': a.prompt, 'clip': ['3', 0]}},
        '6': {'class_type': 'CLIPTextEncode', 'inputs': {'text': a.negative, 'clip': ['3', 0]}},
        '10': {'class_type': 'LoadVideo', 'inputs': {'file': names['control']}},
        '11': {'class_type': 'GetVideoComponents', 'inputs': {'video': ['10', 0]}},
    }
    vace = {'width': a.width, 'height': a.height, 'length': frames, 'batch_size': 1, 'strength': a.strength,
            'positive': ['5', 0], 'negative': ['6', 0], 'vae': ['4', 0], 'control_video': ['11', 0]}
    if a.first_frame:
        g['12'] = {'class_type': 'LoadImage', 'inputs': {'image': names['first_frame']}}
        g['13'] = {'class_type': 'ImageFromBatch', 'inputs': {'image': ['11', 0], 'batch_index': 1, 'length': frames - 1}}
        g['14'] = {'class_type': 'ImageBatch', 'inputs': {'image1': ['12', 0], 'image2': ['13', 0]}}
        g['15'] = {'class_type': 'LoadVideo', 'inputs': {'file': names['mask']}}
        g['16'] = {'class_type': 'GetVideoComponents', 'inputs': {'video': ['15', 0]}}
        g['17'] = {'class_type': 'ImageToMask', 'inputs': {'image': ['16', 0], 'channel': 'red'}}
        vace.update(control_video=['14', 0], control_masks=['17', 0])
    g['20'] = {'class_type': 'WanVaceToVideo', 'inputs': vace}
    latent = ['20', 2]
    if a.source:
        g['21'] = {'class_type': 'LoadVideo', 'inputs': {'file': names['source']}}
        g['22'] = {'class_type': 'GetVideoComponents', 'inputs': {'video': ['21', 0]}}
        g['23'] = {'class_type': 'VAEEncode', 'inputs': {'pixels': ['22', 0], 'vae': ['4', 0]}}
        latent = ['23', 0]
    g['30'] = {'class_type': 'KSampler', 'inputs': {
        'seed': a.seed, 'steps': a.steps, 'cfg': a.cfg, 'sampler_name': 'uni_pc', 'scheduler': 'simple',
        'denoise': a.denoise, 'model': ['2', 0], 'positive': ['20', 0], 'negative': ['20', 1], 'latent_image': latent}}
    g['31'] = {'class_type': 'TrimVideoLatent', 'inputs': {'samples': ['30', 0], 'trim_amount': ['20', 3]}}
    g['32'] = {'class_type': 'VAEDecode', 'inputs': {'samples': ['31', 0], 'vae': ['4', 0]}}
    g['33'] = {'class_type': 'CreateVideo', 'inputs': {'images': ['32', 0], 'fps': a.fps}}
    g['34'] = {'class_type': 'SaveVideo', 'inputs': {'video': ['33', 0], 'filename_prefix': f'{a.prefix}/{a.name}',
                                                     'format': 'auto', 'format.codec': 'auto'}}
    return g


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--name', required=True, help='결과 파일 이름 앞부분')
    p.add_argument('--control', required=True, help='제어 영상(Canny 등), 프레임 수 = 생성 길이')
    p.add_argument('--first-frame', help='0번 프레임으로 고정할 이미지')
    p.add_argument('--source', help='저-denoise 시작점이 될 원본 영상')
    p.add_argument('--denoise', type=float, default=1.0)
    p.add_argument('--strength', type=float, default=1.0)
    p.add_argument('--prompt-file', required=True)
    p.add_argument('--negative-file', required=True)
    p.add_argument('--out', required=True, help='결과·지표 저장 폴더')
    p.add_argument('--compare', help='좌우 비교에 쓸 원본 영상')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--steps', type=int, default=20)
    p.add_argument('--cfg', type=float, default=6.0)
    p.add_argument('--shift', type=float, default=8.0)
    p.add_argument('--width', type=int, default=832)
    p.add_argument('--height', type=int, default=480)
    p.add_argument('--fps', type=int, default=16)
    p.add_argument('--prefix', default='vace_v2v', help='ComfyUI output 하위 폴더')
    p.add_argument('--unet', default='wan2.1_vace_1.3B_fp16.safetensors')
    p.add_argument('--clip', default='umt5_xxl_fp8_e4m3fn_scaled.safetensors')
    p.add_argument('--vae', default='wan_2.1_vae.safetensors')
    p.add_argument('--host', default='http://127.0.0.1:8188')
    a = p.parse_args()
    if a.source is None and a.denoise < 1.0:
        p.error('--denoise < 1 은 --source 와 함께 써야 함')

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / f'{a.name}_metrics.json').exists():
        raise SystemExit(f'{a.name}_metrics.json 이 이미 있음: 기존 결과를 확인하고 다른 --name 을 쓸 것')
    q = call(a.host, '/queue')
    if q['queue_running'] or q['queue_pending']:
        raise SystemExit('ComfyUI 큐가 비어 있지 않음')

    spec = probe(Path(a.control))
    frames = int(spec['frames'])
    if (spec['width'], spec['height']) != (a.width, a.height) or (frames - 1) % 4:
        raise SystemExit(f'제어 영상 규격 불일치 또는 프레임 수가 4n+1 아님: {spec}')
    if a.source:
        s = probe(Path(a.source))
        if (s['width'], s['height'], int(s['frames'])) != (a.width, a.height, frames):
            raise SystemExit(f'원본 영상 규격이 제어 영상과 다름: {s}')
    a.prompt = Path(a.prompt_file).read_text(encoding='utf-8').strip()
    a.negative = Path(a.negative_file).read_text(encoding='utf-8').strip()

    names = {'control': upload(a.host, a.control)}
    if a.first_frame:
        names['first_frame'] = upload(a.host, a.first_frame)
        mask = out / f'{a.name}_mask.mp4'
        make_mask_video(mask, frames, a.width, a.height, a.fps)
        names['mask'] = upload(a.host, mask)
    if a.source:
        names['source'] = upload(a.host, a.source)

    graph = build_graph(a, names, frames)
    (out / f'{a.name}_api.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding='utf-8')
    pid = call(a.host, '/prompt', {'prompt': graph})['prompt_id']
    print(f'{a.name}: queued {pid}', flush=True)

    start, peak_gpu = time.monotonic(), 0
    while True:
        try:  # nvidia-smi가 없는 PC(다른 컴퓨터에서 --host로 제출)면 GPU 메모리는 0으로 남김
            smi = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
            if smi.returncode == 0 and smi.stdout.split():
                peak_gpu = max(peak_gpu, int(smi.stdout.split()[0]))
        except (FileNotFoundError, ValueError):
            pass
        hist = call(a.host, f'/history/{pid}')
        if pid in hist:
            break
        time.sleep(2)
    record = hist[pid]
    metrics = {'name': a.name, 'prompt_id': pid, 'seconds': round(time.monotonic() - start, 1), 'peak_gpu_mib': peak_gpu,
               'frames': frames, 'first_frame': bool(a.first_frame), 'source': bool(a.source), 'denoise': a.denoise,
               'strength': a.strength, 'seed': a.seed, 'status': record['status']['status_str']}
    if metrics['status'] != 'success':
        (out / f'{a.name}_metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
        raise SystemExit(json.dumps(record['status'], ensure_ascii=False))

    files = [f for v in record['outputs']['34'].values() if isinstance(v, list)
             for f in v if isinstance(f, dict) and f.get('type') == 'output']
    dest = out / files[0]['filename']
    urllib.request.urlretrieve(a.host + '/view?' + urllib.parse.urlencode(
        {k: files[0][k] for k in ['filename', 'subfolder', 'type']}), dest)
    metrics['output'] = str(dest)
    metrics['spec'] = probe(dest)
    (out / f'{a.name}_metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    if a.compare:
        cmp_path = out / f'{a.name}_comparison.mp4'
        subprocess.run([sys.executable, str(HERE / 'v2v_compare.py'), 'compare', '--reference', a.compare,
                        '--result', str(dest), '--out', str(cmp_path)], check=True, stdout=subprocess.DEVNULL)
        if not cmp_path.is_file():
            raise SystemExit('비교 영상이 만들어지지 않음')
        for i in [0, frames // 2, frames - 1]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(cmp_path), '-vf', f'select=eq(n\\,{i})',
                            '-frames:v', '1', str(out / f'{a.name}_{i}.jpg')], check=True)
    print(json.dumps(metrics, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()

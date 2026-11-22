"""ComfyUI HTTP API 도우미 (표준 라이브러리만). vace_v2v.py가 불러 씀, 직접 실행하지 않음."""
import json
import urllib.request
import uuid
from pathlib import Path


def upload(host, path, kind="image"):
    """로컬 파일을 ComfyUI input 폴더에 올리고 서버 쪽 파일 이름을 돌려준다. 영상도 /upload/image로 올라감."""
    b = uuid.uuid4().hex
    data = Path(path).read_bytes()
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{Path(path).name}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + data + \
           f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode()
    r = urllib.request.Request(f"{host}/upload/{kind}", body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(r))["name"]


def resolve_input(host, name_or_path):
    """로컬에 있는 파일이면 올리고, 아니면 ComfyUI input 폴더의 파일 이름으로 그대로 쓴다."""
    return upload(host, name_or_path) if Path(name_or_path).is_file() else name_or_path

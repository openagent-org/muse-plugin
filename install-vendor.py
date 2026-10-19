#!/usr/bin/env python3
"""Muse 安装阶段补齐官方 COS SDK 压缩归档；业务上传不调用此工具。"""

import argparse
import errno
import gzip
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import socket
import ssl
import tempfile
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/scripts/cos_sdk.cjs.gz"
FALLBACK_URL = "https://gitee.com/openagent-org/muse-plugin/raw/rel/skills/openagent-run-agent/scripts/cos_sdk.cjs.gz"


class ArchiveRedirectHandler(urllib.request.HTTPRedirectHandler):
    """仅允许 Gitee Raw 向官方 CDN 同路径跳转一次，跟随前核验。"""

    def redirect_request(self, request, response, code, message, headers, new_url):
        target = urllib.parse.urlsplit(new_url)
        if (request.full_url != FALLBACK_URL
                or target.scheme != "https" or target.netloc != "raw.giteeusercontent.com"
                or target.path != urllib.parse.urlsplit(FALLBACK_URL).path or target.fragment
                or "\\" in new_url or any(ord(char) <= 32 or ord(char) == 127 for char in new_url)):
            raise ValueError("COS SDK 归档下载地址发生不受信任的跳转")
        return super().redirect_request(request, response, code, message, headers, new_url)


def is_network_failure(error: Exception) -> bool:
    """只对连接、传输及 5xx 失败换源；认证、证书和本地错误不重试。"""
    if isinstance(error, urllib.error.HTTPError):
        return 500 <= error.code <= 599
    if isinstance(error, urllib.error.URLError):
        error = error.reason
    if isinstance(error, ssl.SSLEOFError):
        return True
    if isinstance(error, ssl.SSLError):
        return False
    return (isinstance(error, (TimeoutError, socket.timeout, ConnectionError, socket.gaierror, http.client.IncompleteRead))
            or isinstance(error, OSError) and error.errno in {errno.ENETUNREACH, errno.EHOSTUNREACH})


def download_archive(url: str) -> bytes:
    opener = urllib.request.build_opener(ArchiveRedirectHandler())
    with opener.open(url, timeout=30) as response:
        return response.read()


def download_with_fallback() -> bytes:
    try:
        return download_archive(BASE_URL)
    except (OSError, http.client.HTTPException) as error:
        if not is_network_failure(error):
            raise
    return download_archive(FALLBACK_URL)


def write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(data)
        staged = Path(temporary.name)
    try:
        staged.chmod(0o644)
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)


def verify_archive(data: bytes, archive: dict) -> None:
    """安装前同时校验压缩包与解压后 bundle，不执行下载代码。"""
    if len(data) != archive["size"] or hashlib.sha256(data).hexdigest() != archive["sha256"]:
        raise ValueError("COS SDK 归档摘要不符")
    content = gzip.decompress(data)
    if (len(content) != archive["uncompressed_size"]
            or hashlib.sha256(content).hexdigest() != archive["uncompressed_sha256"]):
        raise ValueError("COS SDK 解压摘要不符")


def install_vendor(scripts: Path) -> int:
    """校验固定归档后原子安装；已有归档复用，保留解压缓存及其他文件。"""
    scripts = Path(os.path.abspath(scripts))
    if scripts.resolve() != scripts or not scripts.is_dir():
        raise ValueError("执行 Skill 的 scripts 目录不存在或包含符号链接")
    skill = scripts.parent / "SKILL.md"
    if not re.search(r"^name:\s*openagent-run-agent\s*$", skill.read_text(encoding="utf-8"), re.MULTILINE):
        raise ValueError("目标不是已确认来源的 openagent-run-agent Skill")
    lock_path = scripts / "cos_sdk.lock.json"
    if lock_path.resolve() != lock_path:
        raise ValueError("锁定清单不能是符号链接")
    lock = json.loads(lock_path.read_bytes())
    archive = lock.get("bundle", {})
    digest = archive.get("sha256")
    if (lock.get("format") != "openagent-cos-node-sdk-v1" or lock.get("minimum_node") != 20
            or lock.get("sdk", {}).get("name") != "cos-nodejs-sdk-v5"
            or archive.get("file") != "cos_sdk.cjs.gz"
            or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)):
        raise ValueError("COS SDK 归档路径或摘要无效")
    for prefix in ("", "uncompressed_"):
        digest, size = archive.get(prefix + "sha256"), archive.get(prefix + "size")
        if (not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)
                or type(size) is not int or size <= 0):
            raise ValueError("COS SDK 归档路径或摘要无效")
    digest = archive["sha256"]
    target = scripts / archive["file"]
    if target.resolve() != target or (target.exists() and not target.is_file()):
        raise ValueError("COS SDK 归档目标路径冲突")
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == digest:
        verify_archive(target.read_bytes(), archive)
        return 1
    data = download_with_fallback()
    verify_archive(data, archive)
    write_file(target, data)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts-dir", required=True, type=Path, help="已确认的执行 Skill scripts 绝对路径")
    args = parser.parse_args()
    if not args.scripts_dir.is_absolute():
        parser.error("--scripts-dir 必须为真实绝对路径")
    count = install_vendor(args.scripts_dir)
    print(f"SDK_ARCHIVE_READY files={count}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, http.client.HTTPException) as error:
        raise SystemExit(f"COS SDK 归档安装未完成：{error}") from None

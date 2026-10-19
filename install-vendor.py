#!/usr/bin/env python3
"""Muse 安装阶段补齐官方 COS SDK 压缩归档；业务上传不调用此工具。"""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.request


BASE_URL = "https://oasn-ow.haimawan.com/install-assets/muse/skills/openagent-run-agent/scripts/cos_sdk.cjs.gz"


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
    with urllib.request.urlopen(BASE_URL, timeout=30) as response:
        if response.geturl() != BASE_URL:
            raise ValueError("COS SDK 归档下载地址发生跳转")
        data = response.read()
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
    except (OSError, ValueError, TypeError) as error:
        raise SystemExit(f"COS SDK 归档安装未完成：{error}") from None

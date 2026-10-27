from __future__ import annotations

import os
import stat
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

IGNORED_DIRS = {"mods", "libraries", "plugins", "config", "versions"}
CORE_KEYWORDS = ("server", "paper", "spigot", "forge", "fabric", "velocity", "neoforge")
MAX_MEMBERS = 100_000


def safe_member_path(root: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"非法归档路径: {member_name}")
    target = (root / Path(*pure.parts)).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise ValueError(f"非法归档路径: {member_name}")
    return target


def is_special_or_unsafe(mode: int) -> bool:
    kind = stat.S_IFMT(mode)
    return kind not in (0, stat.S_IFREG, stat.S_IFDIR)


def extract_zip(archive: Path, destination: Path) -> int:
    count = 0
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            count += 1
            if count > MAX_MEMBERS:
                raise ValueError("归档文件包含过多条目")
            target = safe_member_path(destination, info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if is_special_or_unsafe(mode):
                continue
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(info, "r") as input_file, target.open("wb") as output_file:
                while chunk := input_file.read(1024 * 1024):
                    output_file.write(chunk)
            os.chmod(target, 0o640)
    return count


def extract_tar_gz(archive: Path, destination: Path) -> int:
    count = 0
    with tarfile.open(archive, "r:gz") as source:
        for member in source:
            count += 1
            if count > MAX_MEMBERS:
                raise ValueError("归档文件包含过多条目")
            target = safe_member_path(destination, member.name)
            if is_special_or_unsafe(member.mode) or member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                continue
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted = source.extractfile(member)
            if extracted is None:
                continue
            with extracted, target.open("wb") as output_file:
                while chunk := extracted.read(1024 * 1024):
                    output_file.write(chunk)
            os.chmod(target, 0o640)
    return count


def extract_archive(archive: Path, destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    name = archive.name.lower()
    if name.endswith(".zip"):
        return extract_zip(archive, destination)
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        return extract_tar_gz(archive, destination)
    raise ValueError("仅支持 .zip 或 .tar.gz 整合包")


def find_core_candidates(root: Path) -> list[dict]:
    candidates: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part.lower() in IGNORED_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        relative = path.relative_to(root).as_posix()
        if path.name.lower() in {"start.sh", "start.bat"} and path.parent == root:
            candidates.append({"path": relative, "kind": "script", "size": path.stat().st_size, "recommended": True})
        elif path.suffix.lower() == ".jar" and path.parent == root:
            lowered = path.name.lower()
            score = sum(10 for keyword in CORE_KEYWORDS if keyword in lowered) + min(path.stat().st_size // (1024 * 1024), 5)
            candidates.append({"path": relative, "kind": "jar", "size": path.stat().st_size, "score": score, "recommended": False})
    if candidates:
        scripts = [item for item in candidates if item["kind"] == "script"]
        if scripts:
            for item in scripts:
                item["recommended"] = True
        else:
            best = max(candidates, key=lambda item: item.get("score", 0))
            best["recommended"] = True
    return candidates

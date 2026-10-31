from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METADATA = json.loads((ROOT / "desktop/version.json").read_text(encoding="utf-8"))
VERSION = METADATA["version"]
REPOSITORY = METADATA["repository"]
RELEASES_URL = f"https://github.com/{REPOSITORY}/releases"


class PortableDirUnwritable(RuntimeError):
    """数据目录只能放在 EXE 旁边，而该目录不可写。"""


def writable(directory: Path) -> bool:
    """能建目录、能写探针、能删探针，才算可写。

    不用 os.access：UAC 虚拟化下它对 Program Files 会返回可写，实际写入被重定向。
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".wb-write-probe-{os.getpid()}"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def data_dir() -> Path:
    """运行期产物的根目录：打包后就是 EXE 所在目录（便携）。

    优先级：``WORKBUDDY_DESKTOP_DATA`` > EXE 同级目录。
    EXE 放在不可写位置（Program Files、只读盘）时抛 ``PortableDirUnwritable``，
    由桌面入口弹窗要求换目录 —— 不回退到用户目录，否则「便携」就是假的。
    源码运行（未冻结）仍走用户目录，避免构建 / 调试把仓库写脏。
    """
    override = (os.environ.get("WORKBUDDY_DESKTOP_DATA") or "").strip()
    if override:
        path = Path(override)
    elif getattr(sys, "frozen", False):
        # onedir 下 __file__ 在 _internal/ 里，sys.executable 才是 EXE 本身。
        path = Path(sys.executable).resolve().parent
        if not writable(path):
            raise PortableDirUnwritable(f"EXE 所在目录不可写：{path}")
    else:
        path = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WorkBuddy2API"
    path.mkdir(parents=True, exist_ok=True)
    return path


def atomic_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)

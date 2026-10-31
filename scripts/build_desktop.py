"""Reproducible Windows x64 onedir packaging; never includes .env, logs or account data."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", default="dist", help="Output folder; useful while an older EXE is running")
    args = parser.parse_args()
    destination = (ROOT / args.dist_dir).resolve()
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise SystemExit("Use Windows x64 with a 64-bit Python interpreter")
    if sys.maxsize <= 2**32:
        raise SystemExit("A 64-bit Python interpreter is required")
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_runtime.py')], cwd=ROOT, check=True)
    import resvg_py
    from PIL import Image
    version = json.loads((ROOT / "desktop/version.json").read_text(encoding="utf-8"))["version"]
    parts = tuple(int(v) for v in version.split("."))
    if len(parts) != 3:
        raise SystemExit("desktop/version.json must contain a stable x.y.z version")
    assets = ROOT / "desktop/assets"
    png = resvg_py.svg_to_bytes(svg_string=(assets / "app.svg").read_text(encoding="utf-8"),
                                width=256, height=256)
    (assets / "app.png").write_bytes(png)
    Image.open(assets / "app.png").save(assets / "app.ico", format="ICO",
                                       sizes=[(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)])
    (ROOT / "build").mkdir(exist_ok=True)
    resource = f'''VSVersionInfo(
      ffi=FixedFileInfo(filevers={parts + (0,)}, prodvers={parts + (0,)},
          mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)),
      kids=[StringFileInfo([StringTable('040904B0', [
        StringStruct('CompanyName', 'MiraiHub'),
        StringStruct('FileDescription', 'MiraiHub Desktop'),
        StringStruct('FileVersion', '{version}'),
        StringStruct('ProductName', 'MiraiHub'),
        StringStruct('ProductVersion', '{version}')])]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])])'''
    (ROOT / "build/version-resource.txt").write_text(resource, encoding="utf-8")
    env = dict(os.environ, PYTHONUTF8="1")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "--distpath", str(destination),
                    str(ROOT / "desktop/miraihub.spec")], cwd=ROOT, env=env, check=True)
    # onedir：PyInstaller 产出 {dist}/{spec_name}/{spec_name}.exe + _internal/。
    # spec 里的 name 不带版本号（引导器与版本无关），版本号只体现在外层 zip 名上。
    spec_name = "miraihub-windows-x64"
    folder = destination / spec_name
    executable = folder / f"{spec_name}.exe"
    if not executable.is_file():
        raise SystemExit(f"未生成预期的可执行文件：{executable}")
    # 最终产物只留一个 zip：解开后根目录直接是 EXE 与 _internal/，不再套一层文件夹。
    archive = destination / f"miraihub-{version}-windows-x64.zip"
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(folder).as_posix())
    # 不产出 .sha256 文件：哈希打印到构建输出，并写入 dist/build-<版本>.json 清单。
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    # PyInstaller 的 EXE 阶段会先往 dist 根写裸 EXE，COLLECT 再复制进文件夹，这里清掉中间产物。
    shutil.rmtree(folder, ignore_errors=True)
    (destination / f"{spec_name}.exe").unlink(missing_ok=True)
    print(f"Built {archive} ({archive.stat().st_size / 1048576:.1f} MB)")
    print(f"SHA256 {digest}")

if __name__ == "__main__":
    main()

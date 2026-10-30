"""Build build/agenda-parser.zip for Lambda (Linux wheels, no Docker needed)."""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
build = root / "build" / "parser"
out = root / "build" / "agenda-parser.zip"

shutil.rmtree(build, ignore_errors=True)
build.mkdir(parents=True)

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "--quiet",
    "--target", str(build),
    "--platform", "manylinux2014_x86_64",
    "--implementation", "cp",
    "--python-version", "3.12",
    "--only-binary=:all:",
    "pydantic==2.9.2", "pyjwt[crypto]",
])

shutil.copytree(
    root / "backend" / "app" / "ai",
    build / "app" / "ai",
    ignore=shutil.ignore_patterns("__pycache__"),
)
(build / "app" / "__init__.py").touch()

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in build.rglob("*"):
        if p.is_file():
            z.write(p, p.relative_to(build).as_posix())

print(out, out.stat().st_size // 1024, "KB")
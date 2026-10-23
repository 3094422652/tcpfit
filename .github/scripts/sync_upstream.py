#!/usr/bin/env python3
"""
Automatically patches upstream Kylin010/tcpfit files for 3094422652/tcpfit:
1. Replaces Kylin010/tcpfit with 3094422652/tcpfit in tcpfit.sh, install.sh, README.md
2. Disables external telemetry ping in tcpfit.sh
3. Injects version-pinned installation command in README.md
4. Recomputes SHA256SUMS for tcpfit.sh and install.sh
"""

import hashlib
import pathlib
import re
import sys

REPO_OWNER_NAME = "3094422652/tcpfit"
UPSTREAM_OWNER_NAME = "Kylin010/tcpfit"

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def patch_tcpfit_sh(path: pathlib.Path) -> str:
    text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    m = re.search(r'^VERSION="([^"]+)"', text, flags=re.MULTILINE)
    if not m:
        raise RuntimeError("Could not find VERSION in tcpfit.sh")
    version = m.group(1)

    text = text.replace(UPSTREAM_OWNER_NAME, REPO_OWNER_NAME)

    # Disable telemetry_off by ensuring `return 0` is the first statement
    if not re.search(r"telemetry_off\(\)\{\s*return 0", text):
        text, n = re.subn(
            r"(telemetry_off\(\)\{\n)",
            r"\1  return 0\n",
            text,
            count=1,
        )
        if n == 0:
            raise RuntimeError("Could not patch telemetry_off() in tcpfit.sh")

    path.write_bytes(text.encode("utf-8"))
    return version


def patch_install_sh(path: pathlib.Path) -> None:
    text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    text = text.replace(UPSTREAM_OWNER_NAME, REPO_OWNER_NAME)
    path.write_bytes(text.encode("utf-8"))


def patch_readme(path: pathlib.Path, version: str) -> None:
    text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    text = text.replace(UPSTREAM_OWNER_NAME, REPO_OWNER_NAME)

    install_section = (
        f"## 安装\n\n"
        f"**方式一：指定版本号安装（推荐，当前版本 `v{version}`）**\n"
        f"> 如果后续同步的新版本不好用，直接把下方命令里的 `v{version}` 改成上一个版本号（例如 `v0.5.8` 或任意历史标签）即可直接运行并退回该版本：\n\n"
        f"```bash\n"
        f"bash <(curl -fsSL https://raw.githubusercontent.com/{REPO_OWNER_NAME}/v{version}/tcpfit.sh)\n"
        f"```\n\n"
        f"**方式二：始终安装最新 `main` 分支**\n\n"
        f"```bash\n"
        f"bash <(curl -fsSL https://raw.githubusercontent.com/{REPO_OWNER_NAME}/main/tcpfit.sh)\n"
        f"```"
    )

    # Replace existing ## 安装 block up to the next paragraph "跑完直接出菜单"
    pattern = re.compile(
        r"## 安装\n+.*?(?=\n\n跑完直接出菜单)",
        flags=re.DOTALL,
    )
    if pattern.search(text):
        text = pattern.sub(install_section, text, count=1)

    path.write_bytes(text.encode("utf-8"))


def update_sha256sums(root: pathlib.Path) -> None:
    h_tcpfit = hashlib.sha256((root / "tcpfit.sh").read_bytes()).hexdigest()
    h_install = hashlib.sha256((root / "install.sh").read_bytes()).hexdigest()
    content = f"{h_tcpfit}  tcpfit.sh\n{h_install}  install.sh\n"
    (root / "SHA256SUMS").write_bytes(content.encode("utf-8"))


def main() -> int:
    tcpfit_path = ROOT / "tcpfit.sh"
    install_path = ROOT / "install.sh"
    readme_path = ROOT / "README.md"

    version = patch_tcpfit_sh(tcpfit_path)
    if install_path.exists():
        patch_install_sh(install_path)
    if readme_path.exists():
        patch_readme(readme_path, version)
    if tcpfit_path.exists() and install_path.exists():
        update_sha256sums(ROOT)

    print(f"Patched successfully for version v{version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

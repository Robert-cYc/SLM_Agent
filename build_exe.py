"""
Packaging script for SmolLM Assistant using PyInstaller.
Builds a standalone Windows executable.
"""

import sys
import subprocess
import shutil
from pathlib import Path

# Fix Windows console encoding for UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def kill_existing_process():
    if sys.platform.startswith("win"):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "SmolLMAssistant.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def build():
    print("=" * 60)
    print("[*] Starting PyInstaller build for SmolLM Assistant...")
    print("=" * 60)

    kill_existing_process()

    project_dir = Path(__file__).parent.resolve()
    entry_point = project_dir / "app.py"

    # Clean previous build directories to prevent stale cache errors
    for folder in ["build", "dist"]:
        p = project_dir / folder
        if p.exists():
            try:
                shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--name=SmolLMAssistant",
        "--windowed",  # No console window (GUI app)
        "--onedir",
        # Collect Hugging Face and PyTorch dependencies
        "--collect-all=transformers",
        "--collect-all=tokenizers",
        "--collect-all=huggingface_hub",
        "--collect-all=safetensors",
        "--collect-all=torch",
        # Hidden imports for GUI and core libraries
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=regex",
        "--hidden-import=tqdm",
        "--hidden-import=requests",
        "--hidden-import=fsspec",
        "--hidden-import=urllib3",
        # Add local helper modules
        f"--add-data={project_dir / 'styles.py'};.",
        f"--add-data={project_dir / 'model_worker.py'};.",
        str(entry_point),
    ]

    print("Executing command:")
    print(" ".join(args))
    print("-" * 60)

    result = subprocess.run(args, cwd=str(project_dir))

    # Remove temporary build/ directory so users won't click into build/ by mistake
    temp_build = project_dir / "build"
    if temp_build.exists():
        try:
            shutil.rmtree(temp_build, ignore_errors=True)
        except Exception:
            pass

    if result.returncode == 0:
        exe_path = project_dir / "dist" / "SmolLMAssistant" / "SmolLMAssistant.exe"
        print("=" * 60)
        print("[+] Build successfully finished!")
        print(f"[!] Please run the executable from 'dist' (NOT 'build'):")
        print(f"    {exe_path}")
        print("=" * 60)
    else:
        print(f"[-] Build failed with return code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()

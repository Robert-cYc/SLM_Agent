"""
Packaging script for SmolLM Assistant using PyInstaller.
Builds a standalone Windows executable.
"""

import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding for UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def build():
    print("=" * 60)
    print("[*] Starting PyInstaller build for SmolLM Assistant...")
    print("=" * 60)

    project_dir = Path(__file__).parent.resolve()
    entry_point = project_dir / "app.py"

    # PyInstaller arguments
    # Using --onedir is strongly recommended for PyTorch/Transformers to avoid
    # massive extraction latency at every startup.
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name=SmolLMAssistant",
        "--windowed",  # No console window (GUI app)
        "--onedir",
        # Collect all assets and submodules
        "--collect-all=transformers",
        "--collect-all=tokenizers",
        "--collect-all=huggingface_hub",
        "--collect-all=safetensors",
        "--collect-all=torch",
        "--collect-all=PyQt6",
        # Hidden imports
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

    if result.returncode == 0:
        exe_path = project_dir / "dist" / "SmolLMAssistant" / "SmolLMAssistant.exe"
        print("=" * 60)
        print(f"[+] Build successfully finished!")
        print(f"Executable location: {exe_path}")
        print("=" * 60)
    else:
        print(f"[-] Build failed with return code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()

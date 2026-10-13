"""
Packaging script for SmolLM Assistant using PyInstaller.
Builds a standalone Windows executable.

Uses local temp directory (C: drive) during build to prevent Google Drive / cloud
file-locking issues and WinError 3 / WinError 5 during compilation.
"""

import os
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


def remove_dir_safely(dir_path: Path):
    if not dir_path.exists():
        return
    import stat
    import time

    def on_rm_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    for _ in range(5):
        try:
            shutil.rmtree(dir_path, onerror=on_rm_error)
            if not dir_path.exists():
                return
        except Exception:
            pass
        time.sleep(0.5)


def copy_vc_runtimes(target_internal_dir: Path):
    """Ensure VCRUNTIME140.dll and VCRUNTIME140_1.dll are bundled with _internal."""
    py_dir = Path(sys.executable).parent
    for dll_name in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]:
        src = py_dir / dll_name
        if src.exists():
            dest = target_internal_dir / dll_name
            try:
                shutil.copy2(src, dest)
                print(f"[+] Bundled runtime DLL: {dll_name}")
            except Exception as e:
                print(f"[!] Warning bundling {dll_name}: {e}")


def build():
    print("=" * 60)
    print("[*] Starting PyInstaller build for SmolLM Assistant...")
    print("=" * 60)

    kill_existing_process()

    project_dir = Path(__file__).parent.resolve()
    entry_point = project_dir / "app.py"

    # Use local temporary directory on C: drive for fast & error-free compilation
    local_temp = Path(os.environ.get("TEMP", "C:/Windows/Temp")) / "SmolLM_Packaging"
    work_dir = local_temp / "work"
    dist_dir = local_temp / "dist"

    print(f"[*] Local compilation workspace: {local_temp}")
    remove_dir_safely(local_temp)
    work_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Clean local dist folder
    project_dist = project_dir / "dist"
    project_build = project_dir / "build"
    remove_dir_safely(project_dist)
    remove_dir_safely(project_build)

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--name=SmolLMAssistant",
        "--windowed",  # No console window (GUI app)
        "--onedir",
        f"--workpath={work_dir}",
        f"--distpath={dist_dir}",
        f"--specpath={local_temp}",
        # Collect Hugging Face and PyTorch dependencies
        "--collect-all=transformers",
        "--collect-all=tokenizers",
        "--collect-all=huggingface_hub",
        "--collect-all=safetensors",
        "--collect-all=torch",
        "--collect-all=markdown",
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
        "--hidden-import=markdown",
        # Add local helper modules
        f"--add-data={project_dir / 'styles.py'};.",
        f"--add-data={project_dir / 'model_worker.py'};.",
        f"--add-data={project_dir / 'chat_renderer.py'};.",
        f"--add-data={project_dir / 'widgets.py'};.",
        str(entry_point),
    ]

    print("Executing command:")
    print(" ".join(args))
    print("-" * 60)

    result = subprocess.run(args, cwd=str(project_dir))

    if result.returncode != 0:
        print(f"[-] PyInstaller build failed with return code {result.returncode}")
        sys.exit(result.returncode)

    # Copy VC runtime DLLs into local output before transferring to project
    compiled_app = dist_dir / "SmolLMAssistant"
    internal_dir = compiled_app / "_internal"
    if internal_dir.exists():
        copy_vc_runtimes(internal_dir)

    # Transfer finished build to project dist directory
    print("[*] Copying completed build to project dist directory...")
    target_app = project_dist / "SmolLMAssistant"
    shutil.copytree(compiled_app, target_app)

    # Clean up local temporary files and ensure no build/ exists in project root
    remove_dir_safely(local_temp)
    remove_dir_safely(project_build)

    final_exe = target_app / "SmolLMAssistant.exe"
    if final_exe.exists():
        print("=" * 60)
        print("[+] Build successfully finished!")
        print(f"[!] Executable ready at:")
        print(f"    {final_exe}")
        print("=" * 60)
    else:
        print("[-] Build output file not found.")
        sys.exit(1)


if __name__ == "__main__":
    build()

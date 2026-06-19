import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
VENV_DIR = BASE_DIR / "venv"
REQUIREMENTS = BASE_DIR / "requirements.txt"
FLASK_APP = "run.py"


def log(msg):
    print(f"[AI Task Manager] {msg}")


def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd or BASE_DIR, capture_output=True, text=True)


def check_python():
    if sys.version_info >= (3, 10):
        return sys.executable
    python = shutil.which("python") or shutil.which("python3")
    if python:
        ver = subprocess.run([python, "-c", "import sys; print(sys.version_info[:2])"], capture_output=True, text=True)
        if ver.returncode == 0 and eval(ver.stdout.strip()) >= (3, 10):
            return python
    log("Python 3.10+ not found. Please install Python 3.10 or later.")
    log("Download: https://www.python.org/downloads/")
    input("Press Enter to exit...")
    sys.exit(1)


def setup_venv(python):
    if not VENV_DIR.exists():
        log("Creating virtual environment...")
        run_cmd([python, "-m", "venv", str(VENV_DIR)])
    if os.name == "nt":
        pip = str(VENV_DIR / "Scripts" / "pip.exe")
        python_venv = str(VENV_DIR / "Scripts" / "python.exe")
    else:
        pip = str(VENV_DIR / "bin" / "pip")
        python_venv = str(VENV_DIR / "bin" / "python")
    if not (VENV_DIR / ".deps_installed").exists():
        log("Installing dependencies...")
        run_cmd([pip, "install", "-r", str(REQUIREMENTS)])
        (VENV_DIR / ".deps_installed").touch()
    return python_venv


def init_db(python_venv):
    db_file = BASE_DIR / "instance" / "app.db"
    if db_file.exists():
        return
    log("Setting up database...")
    db_dir = BASE_DIR / "instance"
    db_dir.mkdir(exist_ok=True)
    if not (BASE_DIR / "migrations").exists():
        run_cmd([python_venv, "-m", "flask", "db", "init"], cwd=BASE_DIR)
    run_cmd([python_venv, "-m", "flask", "db", "migrate", "-m", "init"], cwd=BASE_DIR)
    run_cmd([python_venv, "-m", "flask", "db", "upgrade"], cwd=BASE_DIR)


def launch(python_venv):
    log("Starting server...")
    env = os.environ.copy()
    env["FLASK_APP"] = FLASK_APP
    env["FLASK_DEBUG"] = "0"
    proc = subprocess.Popen(
        [python_venv, "-m", "flask", "run", "--port", "5000"],
        cwd=BASE_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000")
    log("Server running at http://127.0.0.1:5000")
    log("Press Ctrl+C to stop.")
    try:
        for line in proc.stdout:
            print(line.decode().strip())
    except KeyboardInterrupt:
        proc.terminate()
        log("Server stopped.")


if __name__ == "__main__":
    import shutil
    python = check_python()
    python_venv = setup_venv(python)
    init_db(python_venv)
    launch(python_venv)

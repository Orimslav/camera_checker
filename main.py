import os
import subprocess
import sys
from pathlib import Path

from dahuawin.app import main


def _project_venv_python() -> Path | None:
    root = Path(__file__).resolve().parent
    candidates = [
        root / "venv" / "Scripts" / "python.exe",
        root / ".venv" / "Scripts" / "python.exe",
        root / "venv" / "bin" / "python",
        root / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _running_in_project_venv(venv_python: Path | None) -> bool:
    if venv_python is None:
        return True
    try:
        return Path(sys.executable).resolve() == venv_python.resolve()
    except OSError:
        return False


def _relaunch_in_project_venv() -> None:
    if os.environ.get("DAHUAWIN_VENV_BOOTSTRAPPED") == "1":
        return

    venv_python = _project_venv_python()
    if _running_in_project_venv(venv_python):
        return

    env = os.environ.copy()
    env["DAHUAWIN_VENV_BOOTSTRAPPED"] = "1"
    subprocess.run([str(venv_python), __file__, *sys.argv[1:]], check=True, env=env)
    raise SystemExit(0)


if __name__ == "__main__":
    _relaunch_in_project_venv()
    main(sys.argv[1:])

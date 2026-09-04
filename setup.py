"""Automatyczna konfiguracja MatrixCommand"""

import subprocess
import sys
import os
from pathlib import Path

REPO_DIR = Path(__file__).parent
VENV_DIR = REPO_DIR / ".venv"
REQUIREMENTS = REPO_DIR / "requirements.txt"


def run(cmd, **kwargs):
    """Uruchom komendę subprocess."""
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"BŁĄD: {' '.join(cmd)}")
        print(result.stderr)
        sys.exit(1)
    return result


def check_python():
    """Sprawdź wersję Pythona."""
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Wymagane Python 3.10+")
        sys.exit(1)
    print("✅ Python OK")


def create_venv():
    """Stwórz środowisko wirtualne."""
    if VENV_DIR.exists():
        print("✅ Środowisko wirtualne istnieje")
        return True

    print("📦 Tworzenie venv...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    print("✅ Venv utworzony")
    return True


def install_deps():
    """Zainstaluj zależności."""
    pip_path = VENV_DIR / "bin" / "pip"
    if not pip_path.exists():
        pip_path = VENV_DIR / "Scripts" / "pip"

    print("📥 Instalacja zależności...")
    run([str(pip_path), "install", "--upgrade", "pip"])
    run([str(pip_path), "install", "-r", str(REQUIREMENTS)])
    print("✅ Zależności zainstalowane")


def install_extra():
    """Dodatkowe pakiety."""
    pip_path = VENV_DIR / "bin" / "pip"
    if not pip_path.exists():
        pip_path = VENV_DIR / "Scripts" / "pip"

    print("🔧 Instalacja paków dodatkowych...")
    run([str(pip_path), "install", "pytest", "pytest-asyncio"])
    run([str(pip_path), "install", "black", "ruff"])
    print("✅ Pakiety dodatkowe zainstalowane")


def run_app():
    """Uruchom aplikację."""
    print("🚀 Uruchamianie MatrixCommand...")
    python_path = VENV_DIR / "bin" / "python"
    if not python_path.exists():
        python_path = VENV_DIR / "Scripts" / "python"

    run([str(python_path), str(REPO_DIR / "app.py")])


def main():
    print("=" * 50)
    print("MatrixCommand - Automatyczna konfiguracja")
    print("=" * 50)

    check_python()
    create_venv()
    install_deps()
    install_extra()

    print("\n" + "=" * 50)
    print("✅ Konfiguracja zakończona pomyślnie!")
    print("=" * 50)
    print("\nAby uruchomić: source .venv/bin/activate && python3 app.py")
    print("Lub: make run")
    print("\nAby aktywować venv: source .venv/bin/activate")


if __name__ == "__main__":
    main()
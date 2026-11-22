#!/usr/bin/env python3
"""One entry point for local NeoCam development on Ubuntu and Windows."""
import argparse
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".workspace"
STATE = WORK / "developer.json"
VENV = WORK / "dev-venv"
SDK_VERSION = "v6.0.1"
TARGET = "esp32s3"
BUILD = "_build/esp32s3"
SDK_REPO = "https://github.com/espressif/esp-idf.git"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(args, *, env=None, capture=False, cwd=None):
    result = subprocess.run([str(arg) for arg in args], cwd=cwd or ROOT, env=env,
                            capture_output=capture, text=True, encoding="utf-8", errors="replace")
    require(result.returncode == 0, f"{Path(str(args[0])).name} failed (exit {result.returncode})")
    return result.stdout.strip() if capture else ""


def git(*args):
    command = ["git", *map(str, args)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode and "could not resolve proxy" in result.stderr.lower():
        print("Git proxy could not be resolved; retrying this command with http.proxy=.", flush=True)
        result = subprocess.run(["git", "-c", "http.proxy=", *command[1:]], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
    require(result.returncode == 0, "Git failed; check authentication, repository access and network/proxy")
    return result.stdout.strip()


def python_in(path):
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def public_pip_environment(environment):
    result = dict(environment)
    result["PIP_CONFIG_FILE"] = os.devnull
    result["PIP_INDEX_URL"] = os.environ.get("NEOCAM_PIP_INDEX", "https://pypi.org/simple")
    result.pop("PIP_EXTRA_INDEX_URL", None)
    return result


def state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save(data):
    WORK.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(STATE)


def ubuntu_prerequisites():
    release = Path("/etc/os-release")
    if sys.platform != "linux" or not release.exists() or '\nID=ubuntu\n' not in '\n' + release.read_text() + '\n':
        return
    require(sys.version_info >= (3, 12), "Use Python 3.12+; Ubuntu 24.04 provides it by default")
    packages = ("git", "make", "python3-venv", "build-essential", "flex", "bison", "gperf",
                "libffi-dev", "libssl-dev", "python3-dev", "libusb-1.0-0")
    missing = []
    for package in packages:
        result = subprocess.run(["dpkg-query", "-W", "-f=${db:Status-Abbrev}", package],
                                capture_output=True, text=True)
        if result.returncode or not result.stdout.startswith("ii"):
            missing.append(package)
    if missing:
        print("Installing Ubuntu prerequisites: " + ", ".join(missing), flush=True)
        prefix = [] if os.geteuid() == 0 else ["sudo"]
        run([*prefix, "apt-get", "update"])
        run([*prefix, "apt-get", "install", "-y", *missing])


def bootstrap(arguments):
    """Keep project dependencies out of system Python and the firmware SDK venv."""
    require(sys.version_info >= (3, 12), "Install Python 3.12 or newer, then run this command again")
    require(shutil.which("git"), "Install Git, then run this command again")
    python = python_in(VENV)
    if not python.exists():
        print("Preparing the project's Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(VENV)
    dependencies = ROOT / "TOOLCONF/requirements-dev.txt"
    digest = hashlib.sha256(dependencies.read_bytes()).hexdigest()
    stamp = WORK / "developer-dependencies.sha256"
    if not stamp.exists() or stamp.read_text() != digest:
        run([python, "-m", "pip", "install", "-r", dependencies], env=public_pip_environment(os.environ))
        stamp.write_text(digest, encoding="utf-8")
    if Path(sys.prefix).resolve() != VENV.resolve():
        environment = dict(os.environ)
        environment["NEOCAM_BASE_PYTHON"] = getattr(sys, "_base_executable", sys.executable)
        return subprocess.call([str(python), str(Path(__file__).resolve()), *arguments], cwd=ROOT, env=environment)
    return None


def apply_exports(text, environment):
    result = dict(environment)
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if separator and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            if key == "PATH":
                value = value.replace("%PATH%", environment.get("PATH", "")).replace("$PATH", environment.get("PATH", ""))
            result[key] = value
    return result


def sdk_environment():
    data = state()
    cache = Path(os.environ.get("NEOCAM_TOOLCHAIN_DIR", str(Path.home() / ".neocam/toolchains"))).expanduser().resolve()
    candidates = []
    if data.get("sdk"):
        candidates.append((Path(data["sdk"]), Path(data["tools"])))
    if os.environ.get("IDF_PATH"):
        candidates.append((Path(os.environ["IDF_PATH"]), Path(os.environ.get("IDF_TOOLS_PATH", str(Path.home() / ".espressif")))))
    candidates += [(ROOT.parent / ".toolchain/esp-idf", ROOT.parent / ".toolchain/tools"),
                   (cache / f"esp-idf-{SDK_VERSION}", cache / f"tools-{SDK_VERSION}")]
    selected = None
    for sdk, tools in candidates:
        if (sdk / "tools/idf_tools.py").exists():
            try:
                if git("-C", sdk, "describe", "--tags", "--exact-match", "HEAD") == SDK_VERSION:
                    selected = (sdk.resolve(), tools.resolve())
                    break
            except RuntimeError:
                continue
    if selected is None:
        sdk, tools = candidates[-1]
        require(not sdk.exists(), f"SDK cache is incomplete or has another version: {sdk}. Inspect it before retrying")
        sdk.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading ESP-IDF {SDK_VERSION} and submodules (first setup only)...", flush=True)
        git("clone", "--branch", SDK_VERSION, "--depth", "1", "--recurse-submodules", "--shallow-submodules",
            "--jobs", "8", SDK_REPO, sdk)
        selected = (sdk.resolve(), tools.resolve())
    sdk, tools = selected
    if sdk == candidates[-1][0].resolve():
        marker = sdk / ".git/neocam-submodules-ready"
        if not marker.exists():
            git("-C", sdk, "submodule", "update", "--init", "--recursive", "--depth", "1", "--jobs", "8")
            marker.touch()
    environment = public_pip_environment(dict(os.environ, IDF_PATH=str(sdk), IDF_TOOLS_PATH=str(tools), IDF_TARGET=TARGET))
    environment.pop("IDF_PYTHON_ENV_PATH", None)
    environment.pop("VIRTUAL_ENV", None)
    base = os.environ.get("NEOCAM_BASE_PYTHON", getattr(sys, "_base_executable", sys.executable))
    tool = [base, str(sdk / "tools/idf_tools.py"), "--idf-path", str(sdk)]

    def export():
        return subprocess.run([*tool, "export", "--format=key-value"], env=environment, cwd=ROOT,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    result = export()
    if result.returncode:
        print(f"Installing the {TARGET} compiler tools and SDK Python environment...", flush=True)
        run([*tool, "install", f"--targets={TARGET}"], env=environment)
        run([*tool, "install-python-env", "--features=core"], env=environment)
        result = export()
    require(result.returncode == 0, "SDK environment is not ready; check installation output and OS prerequisites")
    environment = apply_exports(result.stdout, environment)
    sdk_python = python_in(Path(environment.get("IDF_PYTHON_ENV_PATH", "")))
    require(sdk_python.is_file(), "SDK Python environment was not found after installation")
    data.update(sdk=str(sdk), tools=str(tools))
    save(data)
    return sdk_python, environment


def sources(force=False):
    import yaml
    data = state()
    local = ROOT / "packages.local.yml"
    use_local = local.exists() and data.get("use_overrides", True)
    manifest = ROOT / "packages.yml"
    signature = hashlib.sha256(manifest.read_bytes() + (local.read_bytes() if use_local else b"baseline")).hexdigest()
    packages = yaml.safe_load(manifest.read_text(encoding="utf-8"))["packages"]
    missing = any(not (ROOT / package["dest"]).exists() for package in packages.values())
    if force or missing or not (WORK / "state.json").exists() or data.get("assembly") != signature:
        command = [sys.executable, ROOT / "TOOLCONF/workspace.py", "fetch"]
        if use_local:
            command += ["--overrides", local]
        run(command)
        data["assembly"] = signature
        save(data)


def develop(module):
    import yaml
    packages = yaml.safe_load((ROOT / "packages.yml").read_text(encoding="utf-8"))["packages"]
    require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", module) and module in packages,
            "Choose a package key from packages.yml, for example: dev WifiStack")
    checkout = ROOT.parent / "modules" / module
    if not checkout.exists():
        checkout.parent.mkdir(parents=True, exist_ok=True)
        print(f"Cloning the independent {module} checkout...", flush=True)
        git("clone", "--", packages[module]["repo"], checkout)
    require((checkout / ".git").exists(), f"Expected an independent Git checkout at {checkout}")
    path = ROOT / "packages.local.yml"
    document = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {"overrides": {}}
    require(isinstance(document, dict) and isinstance(document.get("overrides", {}), dict), "Invalid packages.local.yml")
    document.setdefault("overrides", {})[module] = {"path": f"../modules/{module}"}
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    data = state()
    data["use_overrides"] = True
    save(data)
    sources(force=True)
    print(f"Live development: {checkout}. Its current branch and edits were preserved.")


def build():
    sources()
    python, environment = sdk_environment()
    print(f"Building NeoCam with ESP-IDF {SDK_VERSION} ({TARGET})...", flush=True)
    run([python, Path(environment["IDF_PATH"]) / "tools/idf.py", "-B", BUILD, "build"], env=environment)
    run([sys.executable, ROOT / "TOOLCONF/check_build.py", BUILD])


def tests():
    sources()
    require(shutil.which(os.environ.get("CC", "cc")),
            "Host tests need a native C compiler. Ubuntu: install build-essential. Windows: install MinGW-w64 and put cc on PATH (or set CC)")
    run([sys.executable, ROOT / "test/run_host_tests.py"])


def ports():
    if os.name == "nt":
        run(["powershell", "-NoProfile", "-Command",
             "Get-PnpDevice -Class Ports -Status OK | Select-Object FriendlyName,InstanceId"])
    else:
        found = sorted(glob.glob("/dev/serial/by-id/*")) or sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
        print("\n".join(found) if found else "No USB serial devices found")


def board(command):
    port = os.environ.get("PORT") or state().get("port")
    require(port, "Select your board once: neo port COM3 (Windows) or make port PORT=/dev/serial/by-id/... (Ubuntu)")
    if command != "monitor":
        build()
    python, environment = sdk_environment()
    actions = ["monitor"] if command == "monitor" else ["flash"]
    if command in ("flash-monitor", "full"):
        actions += ["monitor"]
    run([python, Path(environment["IDF_PATH"]) / "tools/idf.py", "-B", BUILD, "-p", port, *actions], env=environment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="help", choices=(
        "help", "setup", "dev", "fetch", "baseline", "status", "build", "test", "check", "ports", "port",
        "flash", "monitor", "flash-monitor", "full", "clean", "menuconfig", "doctor"))
    parser.add_argument("value", nargs="?", default="")
    args = parser.parse_args()
    if args.command == "help":
        print("NeoCam: make <command> on Ubuntu; .\\neo.cmd <command> on Windows\n"
              "  setup       Prepare packages, pinned ESP-IDF and Python tools\n"
              "  dev MODULE  Link a module checkout (make dev MODULE=WifiStack)\n"
              "  build       Assemble if needed, activate SDK, build and verify\n"
              "  test/check  Host tests / host tests plus firmware build\n"
              "  fetch       Refresh selected package snapshots and links\n"
              "  baseline    Use pinned packages; retain local override configuration\n"
              "  status      Show selected package revisions and development links\n"
              "  ports/port  List devices / remember one device (make port PORT=...)\n"
              "  flash/monitor/flash-monitor/full  Use the saved board port\n"
              "  clean/menuconfig/doctor           Build maintenance and environment info")
        return 0
    try:
        if args.command == "setup":
            ubuntu_prerequisites()
        result = bootstrap(sys.argv[1:])
        if result is not None:
            return result
        if args.command == "setup":
            sources()
            python, environment = sdk_environment()
            run([python, Path(environment["IDF_PATH"]) / "tools/idf.py", "--version"], env=environment)
            print("Ready. Next: make build (Ubuntu) or .\\neo.cmd build (Windows).")
        elif args.command == "dev":
            develop(args.value)
        elif args.command == "baseline":
            data = state()
            data["use_overrides"] = False
            save(data)
            sources(force=True)
        elif args.command == "fetch":
            sources(force=True)
        elif args.command == "status":
            run([sys.executable, ROOT / "TOOLCONF/workspace.py", "status"])
        elif args.command == "build":
            build()
        elif args.command in ("test", "check"):
            tests()
            if args.command == "check":
                build()
        elif args.command == "ports":
            ports()
        elif args.command == "port":
            valid = re.fullmatch(r"COM[1-9][0-9]*", args.value, re.IGNORECASE) if os.name == "nt" else args.value.startswith("/dev/")
            require(valid, "Pass an explicit board device, for example COM3 or /dev/serial/by-id/...")
            data = state()
            data["port"] = args.value
            save(data)
            print(f"Saved board port: {args.value}")
        elif args.command in ("flash", "monitor", "flash-monitor", "full"):
            board(args.command)
        elif args.command in ("clean", "menuconfig"):
            require((ROOT / BUILD).resolve().is_relative_to(ROOT.resolve()), "Build directory escapes this workspace")
            python, environment = sdk_environment()
            run([python, Path(environment["IDF_PATH"]) / "tools/idf.py", "-B", BUILD,
                 "fullclean" if args.command == "clean" else "menuconfig"], env=environment)
        elif args.command == "doctor":
            python, environment = sdk_environment()
            print(json.dumps({"sdk": environment["IDF_PATH"], "sdk_version": SDK_VERSION,
                              "sdk_python": str(python), "tools": environment["IDF_TOOLS_PATH"],
                              "build_directory": str(ROOT / BUILD), "port": state().get("port"),
                              "host_compiler": shutil.which(os.environ.get("CC", "cc")),
                              "use_local_overrides": state().get("use_overrides", True)}, indent=2))
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f"NeoCam: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

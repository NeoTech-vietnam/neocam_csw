#!/usr/bin/env python3
"""Select trusted CI firmware and flash its existing binaries, without building."""
import argparse
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ESPTOOL_VERSION = "5.6.0"
FILES = {"0x0": "bootloader/bootloader.bin",
         "0x8000": "partition_table/partition-table.bin", "0x10000": "neocam_csw.bin"}
SETTINGS = {"flash_mode": "dio", "flash_size": "8MB", "flash_freq": "80m"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def github_get(path):
    token = os.environ.get("GITHUB_TOKEN", "")
    require(token, "GITHUB_TOKEN is required to read private build artifacts")
    request = Request("https://api.github.com/" + path, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "neocam-hardware-flash"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        raise ValueError(f"GitHub API returned HTTP {error.code}; check Actions read access and run ID") from None
    except URLError:
        raise ValueError("GitHub API connection failed; check runner network/proxy configuration") from None


def validate_run(run, repository, workflow_id):
    require(run.get("workflow_id") == workflow_id, "Source must be a NeoCam integration run")
    require(run.get("head_branch") == "main", "Source build must be on main")
    require(run.get("event") in ("push", "workflow_dispatch"), "PR builds cannot be flashed")
    require(run.get("head_repository", {}).get("full_name") == repository,
            "Source build must originate in this repository")
    require(run.get("status") == "completed" and run.get("conclusion") == "success",
            "Source build must have completed successfully")
    require(re.fullmatch(r"[0-9a-f]{40}", run.get("head_sha", "")), "Missing source commit SHA")


def select_source(repository, run_id="", get=github_get):
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "Invalid repository")
    require(not run_id or re.fullmatch(r"[1-9][0-9]*", run_id), "Run ID must be a positive integer")
    base = f"repos/{repository}/actions"
    workflow = get(f"{base}/workflows/integration.yml")
    if not run_id:
        # Skip successful PR runs and retain GitHub's newest-first run ordering.
        for page in range(1, 11):
            runs = get(f"{base}/workflows/integration.yml/runs?branch=main&status=success&per_page=100&page={page}")["workflow_runs"]
            for candidate in runs:
                try:
                    validate_run(candidate, repository, workflow["id"])
                except ValueError:
                    continue
                run_id = str(candidate["id"])
                break
            if run_id or len(runs) < 100:
                break
        require(run_id, "No successful main integration build found; run NeoCam integration first")
    run = get(f"{base}/runs/{run_id}")
    validate_run(run, repository, workflow["id"])
    artifacts = get(f"{base}/runs/{run_id}/artifacts?per_page=100")["artifacts"]
    name = f"firmware-esp32s3-{run_id}"
    matches = [item for item in artifacts if item["name"] == name and not item["expired"]]
    require(len(matches) == 1, f"Expected one available {name} artifact; rebuild if missing or expired")
    return {"run_id": str(run_id), "artifact_id": str(matches[0]["id"]),
            "source_sha": run["head_sha"], "repository": repository,
            "source_url": run["html_url"], "artifact_name": name}


def firmware_files(root):
    root = root.resolve(strict=True)
    build = (root / "_build/esp32s3").resolve(strict=True)
    require(build.is_relative_to(root), "Build directory escapes artifact root")
    manifest = build / "flasher_args.json"
    require(manifest.resolve().is_relative_to(build), "Flash manifest escapes build directory")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    require(data.get("flash_files") == FILES, "Unexpected firmware files/offsets for NeoCam")
    require(data.get("flash_settings") == SETTINGS, "Expected 8MB DIO 80MHz NeoCam flash configuration")
    require(data.get("extra_esptool_args") == {
        "chip": "esp32s3", "before": "default-reset", "after": "hard-reset", "stub": True},
        "Expected unencrypted ESP32-S3 firmware with normal reset settings")
    for name in ("bootloader", "partition-table", "app"):
        require(data.get(name, {}).get("encrypted") == "false", "Encrypted flashing is unsupported")
    files = []
    offsets = sorted(int(offset, 16) for offset in FILES) + [8 * 1024 * 1024]
    for index, (offset, name) in enumerate(FILES.items()):
        path = (build / name).resolve(strict=True)
        require(path.is_relative_to(build) and path.is_file(), "Firmware file escapes build directory")
        size = path.stat().st_size
        require(0 < size <= offsets[index + 1] - offsets[index], "Empty, overlapping or oversized binary")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"offset": offset, "file": name, "size": size,
                      "sha256": digest,
                      "path": str(path)})
    return files


def flash(args):
    files = firmware_files(Path(args.artifact_root))
    command = [sys.executable, "-m", "esptool", "--chip", "esp32s3", "--port", args.port,
               "--baud", args.baud, "--before", "default-reset", "--after", "hard-reset",
               "write-flash", "--flash-mode", SETTINGS["flash_mode"],
               "--flash-size", SETTINGS["flash_size"], "--flash-freq", SETTINGS["flash_freq"]]
    for item in files:
        command += [item["offset"], item["path"]]
    report = {"source_run_id": args.source_run, "source_sha": args.source_sha,
              "repository": os.environ.get("GITHUB_REPOSITORY", ""), "port": args.port,
              "baud": args.baud, "files": files, "result": "dry-run", "command": command}
    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(shlex.join(command), flush=True)
        if args.execute:
            report["result"] = "failed"
            require(sys.platform == "linux", "Hardware flashing requires the configured Linux runner")
            require(args.port.startswith("/dev/"), "Specify an explicit /dev/ serial port")
            port = Path(args.port).resolve(strict=True)
            require(re.fullmatch(r"/dev/tty(?:ACM|USB)[0-9]+", str(port)),
                    "Port must resolve to a USB serial device (/dev/ttyACM* or /dev/ttyUSB*)")
            require(stat.S_ISCHR(port.stat().st_mode), "Serial port is not a character device")
            require(os.access(port, os.R_OK | os.W_OK), "Runner user needs serial access (dialout group)")
            require(version("esptool") == ESPTOOL_VERSION, f"Install esptool=={ESPTOOL_VERSION} in the flashing venv")
            subprocess.run(command, check=True, timeout=300)
            report["result"] = "flashed-and-verified"
    finally:
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['result']}: report saved to {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    select = commands.add_parser("select", help="Resolve a successful main integration artifact")
    select.add_argument("--run-id", default="")
    flashing = commands.add_parser("flash", help="Validate binaries; only --execute writes to hardware")
    flashing.add_argument("--artifact-root", required=True)
    flashing.add_argument("--port", required=True)
    flashing.add_argument("--baud", choices=("115200", "460800", "921600"), default="460800")
    flashing.add_argument("--source-run", default="")
    flashing.add_argument("--source-sha", default="")
    flashing.add_argument("--report", default="_out/hardware-flash.json")
    flashing.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "select":
            source = select_source(os.environ.get("GITHUB_REPOSITORY", ""), args.run_id)
            if os.environ.get("GITHUB_OUTPUT"):
                with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
                    for key in ("run_id", "artifact_id", "source_sha"):
                        stream.write(f"{key}={source[key]}\n")
            if os.environ.get("GITHUB_STEP_SUMMARY"):
                with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
                    stream.write(f"Firmware: [{source['run_id']}]({source['source_url']})\n\nCommit: `{source['source_sha']}`\n")
            print(json.dumps(source, indent=2))
        else:
            flash(args)
    except (ValueError, OSError, KeyError, TypeError, PackageNotFoundError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Flash setup failed: {error}\n")


if __name__ == "__main__":
    main()

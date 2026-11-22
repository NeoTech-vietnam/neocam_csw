#!/usr/bin/env python3
"""Run portable C/backend-fake regressions and Python tooling tests (Pillow needed)."""
import argparse
import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "test/.build"
INCLUDES = [
    "NeoContracts", "Conf/CUCEL", "Conf/__CONFIG",
    "CUCEL/Platform", "CUCEL/Standard",
    "CUCEL/MemMap", "BootCtrl",
    "BswLib/MediaBuf", "CamIo",
    "CamPipe",
    "EbOs", "LocalTime",
    "WifiStack/WifiMgr", "WifiStack/WifiIf",
    "HttpSrv", "Rte", "CamApp/ASW/CamHmi",
    "CamApp/ASW/CamDiag", "CamApp/DE/CamDev",
    "CamApp/ASV/CamSupv",
    "Conf/CamIo", "Conf/CamPipe", "Conf/BswLib", "Conf/WifiStack", "Conf/HttpSrv",
]
CASES = {
    "boot_ctrl": ["BootCtrl/BootCtrl.c"],
    "nvs": ["BootCtrl/BootCtrl_EspIdf.c"],
    "camera_buffers": ["CamIo/CamIo.c", "Conf/CamIo/CamIo_Cfg.c",
                       "BswLib/MediaBuf/MediaBuf.c", "GConf/CameraProfiles/Neo_Profiles.c"],
    "cam_pipe": ["CamPipe/CamPipe.c", "BswLib/MediaBuf/MediaBuf.c",
                 "GConf/CameraProfiles/Neo_Profiles.c"],
    "wifi_config": ["WifiStack/WifiMgr/WifiMgr_Config.c",
                    "Conf/WifiStack/WifiMgr_Cfg.c"],
    "wifi_manager": ["WifiStack/WifiMgr/WifiMgr.c", "WifiStack/WifiMgr/WifiMgr_Config.c",
                     "Conf/WifiStack/WifiMgr_Cfg.c"],
    "http_srv": ["HttpSrv/HttpSrv.c", "Conf/HttpSrv/HttpSrv_Cfg.c", "HttpSrv/HttpSrv_EspIdf.c"],
    "application": ["Rte/Rte.c", "CamApp/ASW/CamHmi/CamHmi.c",
                    "CamApp/ASW/CamDiag/CamDiag.c", "CamApp/DE/CamDev/CamDev.c",
                    "CamApp/ASV/CamSupv/CamSupv.c", "GConf/CameraProfiles/Neo_Profiles.c"],
}
TEST_OWNERS = {"boot_ctrl": "BootCtrl", "nvs": "BootCtrl", "wifi_config": "WifiStack",
               "wifi_manager": "WifiStack", "http_srv": "HttpSrv"}
BSW_FOLDERS = ("CUCEL", "NeoContracts", "BootCtrl", "BswLib", "EbOs", "LocalTime",
               "CamIo", "CamPipe", "WifiStack", "HttpSrv")


def architecture_checks(cc, flags, includes):
    forbidden = re.compile(r'\b(esp_err_t|camera_fb_t|httpd_req_t|TaskHandle_t|SemaphoreHandle_t|FILE)\b')
    public = []
    for folder in (*BSW_FOLDERS, "CamApp", "Rte", "Conf"):
        for header in (ROOT / folder).rglob("*.h"):
            if "test" in header.relative_to(ROOT / folder).parts:
                continue
            if header.name.endswith(("_Backend.h", "_Internal.h", "MemMap.h")):
                continue
            text = header.read_text()
            assert not forbidden.search(text), f"Native type in {header}"
            public.append(header)
    for folder in ("CamApp", *BSW_FOLDERS):
        for source in (ROOT / folder).rglob("*.[ch]"):
            if "test" in source.relative_to(ROOT / folder).parts:
                continue
            text = source.read_text()
            if folder == "CamApp":
                assert not re.search(r'#include\s*[<"](?:esp_|freertos/|CamIo|MediaBuf|Wifi|HttpSrv|EbOs|LocalTime)', text), source
            else:
                assert not re.search(r'#include\s*"(?:Rte|CamHmi|CamDiag|CamDev)', text), source
    for number, header in enumerate(public):
        source = BUILD / f"header_{number}.c"
        source.write_text(f'#include "{header}"\nint main(void) {{ return 0; }}\n')
        subprocess.run([cc, *flags, *includes, "-fsyntax-only", str(source)], check=True)
    source = BUILD / "platform_check.c"
    source.write_text('''#include "Neo_Types.h"
_Static_assert(sizeof(uint8)==1 && sizeof(uint16)==2 && sizeof(uint32)==4 && sizeof(uint64)==8, "integer widths");
_Static_assert(sizeof(float32)==4 && sizeof(float64)==8, "float widths");
_Static_assert(CPU_TYPE==CPU_TYPE_32 && CPU_BYTE_ORDER==LOW_BYTE_FIRST, "ESP32-S3 platform");
int main(void) { return E_OK; }
''')
    subprocess.run([cc, *flags, *includes, "-fsyntax-only", str(source)], check=True)
    for number, markers in enumerate((
        ("NEOCAM_STOP_SEC_CONST_UNSPECIFIED",),
        ("NEOCAM_START_SEC_CONST_UNSPECIFIED", "NEOCAM_START_SEC_VAR_CLEARED_UNSPECIFIED"),
        ("NEOCAM_START_SEC_CONST_UNSPECIFIED", "NEOCAM_STOP_SEC_VAR_CLEARED_UNSPECIFIED"),
    )):
        source = BUILD / f"invalid_memmap_{number}.c"
        source.write_text("".join(f'#define {marker}\n#include "MemMap.h"\n' for marker in markers))
        result = subprocess.run([cc, *flags, *includes, "-fsyntax-only", str(source)], capture_output=True)
        assert result.returncode != 0, f"Invalid section markers accepted: {markers}"
    print(f"PASS architecture and {len(public)} independent public headers", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanitize", action="store_true", help="enable address/undefined sanitizers")
    parser.add_argument("--case", choices=CASES, help="Run one module/integration case plus architecture checks")
    args = parser.parse_args()
    BUILD.mkdir(exist_ok=True)
    report_name = f"host-tests-{args.case}.json" if args.case else "host-tests.json"
    output = ROOT / "_out" / report_name
    output.unlink(missing_ok=True)
    cc = os.environ.get("CC", "cc")
    if os.name == "nt":
        # Keep this compiler's runtime DLLs ahead of unrelated MinGW installations.
        compiler = shutil.which(cc) or cc
        os.environ["PATH"] = str(Path(compiler).resolve().parent) + os.pathsep + os.environ.get("PATH", "")
    flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-g"]
    if os.name == "nt":
        flags += ["-D__USE_MINGW_ANSI_STDIO=1"]
    if args.sanitize:
        flags += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-no-pie"]
    includes = ["-I" + str(ROOT / folder) for folder in INCLUDES]
    architecture_checks(cc, flags, includes)
    completed = []
    for name, sources in CASES.items():
        if args.case and args.case != name:
            continue
        binary = BUILD / (name + (".exe" if os.name == "nt" else ""))
        fake_includes = ["-I" + str(ROOT / "HttpSrv/test/fakes_http")] if name in ("http_srv", "nvs") else []
        if name == "nvs": fake_includes.insert(0, "-I" + str(ROOT / "BootCtrl/test/fakes_nvs"))
        test_file = ROOT / TEST_OWNERS[name] / "test" / f"test_{name}.c" if name in TEST_OWNERS else ROOT / "test" / f"test_{name}.c"
        command = [cc, *flags, *fake_includes, *includes,
                   str(test_file), *[str(ROOT / p) for p in sources], "-o", str(binary)]
        subprocess.run(command, check=True)
        subprocess.run([str(binary)], check=True)
        print(f"PASS {name}", flush=True)
        completed.append(name)
    if not args.case:
        for name in ("performance", "benchmark_camera", "workspace", "hardware_flash", "module_ci"):
            subprocess.run([sys.executable, str(ROOT / f"test/test_{name}.py")], check=True)
            print(f"PASS {name} tooling", flush=True)
            completed.append(name)
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"passed": completed, "architecture": "passed", "sanitized": args.sanitize}, indent=2) + "\n")


if __name__ == "__main__":
    main()

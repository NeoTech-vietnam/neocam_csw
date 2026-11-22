"""Hardware-free checks for CI source selection and the flash write boundary."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hardware_flash", ROOT / "TOOLCONF/hardware_flash.py")
hardware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hardware)
REPO = "NeoTech-vietnam/neocam_csw"
RUN = {"id": 123, "workflow_id": 456, "head_branch": "main", "event": "push",
       "head_repository": {"full_name": REPO}, "status": "completed", "conclusion": "success",
       "head_sha": "a" * 40, "html_url": f"https://github.com/{REPO}/actions/runs/123"}


class HardwareFlashTests(unittest.TestCase):
    def get(self, path):
        if path.endswith("/integration.yml"):
            return {"id": 456}
        if "/integration.yml/runs?" in path:
            return {"workflow_runs": [dict(RUN, event="pull_request"), RUN]}
        if path.endswith("/runs/123"):
            return RUN
        if path.endswith("/runs/123/artifacts?per_page=100"):
            return {"artifacts": [{"id": 789, "name": "firmware-esp32s3-123", "expired": False}]}
        self.fail(f"Unexpected API endpoint: {path}")

    def test_select_explicit_and_latest(self):
        for run_id in ("", "123"):
            source = hardware.select_source(REPO, run_id, self.get)
            self.assertEqual((source["run_id"], source["artifact_id"], source["source_sha"]),
                             ("123", "789", "a" * 40))

    def test_reject_wrong_workflow_branch_origin_pr_or_unsuccessful_build(self):
        for field, value in (("workflow_id", 999), ("head_branch", "feature/wifi"),
                             ("head_repository", {"full_name": "fork/neocam_csw"}),
                             ("event", "pull_request"), ("event", "workflow_run"),
                             ("status", "in_progress"), ("conclusion", "failure"),
                             ("head_sha", "not-a-sha")):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                hardware.validate_run(dict(RUN, **{field: value}), REPO, 456)

    def test_reject_expired_missing_or_ambiguous_artifact(self):
        for artifacts in ([], [{"id": 789, "name": "firmware-esp32s3-123", "expired": True}],
                          [{"id": n, "name": "firmware-esp32s3-123", "expired": False} for n in (1, 2)]):
            def get(path):
                return {"artifacts": artifacts} if "/artifacts?" in path else self.get(path)
            with self.subTest(artifacts=artifacts), self.assertRaises(ValueError):
                hardware.select_source(REPO, "123", get)

    def test_reject_invalid_run_id_before_api(self):
        for run_id in ("--help", "1;echo bad", "0", "../123"):
            with self.subTest(run_id=run_id), self.assertRaises(ValueError):
                hardware.select_source(REPO, run_id, lambda _: self.fail("API must not be called"))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build = self.root / "_build/esp32s3"
        self.build.mkdir(parents=True)
        self.manifest = {"flash_files": hardware.FILES, "flash_settings": hardware.SETTINGS,
                         "extra_esptool_args": {"chip": "esp32s3", "before": "default-reset",
                                                "after": "hard-reset", "stub": True},
                         **{key: {"encrypted": "false"} for key in ("bootloader", "partition-table", "app")}}
        for name in hardware.FILES.values():
            path = self.build / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"firmware" * 32)
        self.write_manifest(self.manifest)

    def write_manifest(self, data):
        (self.build / "flasher_args.json").write_text(json.dumps(data), encoding="utf-8")

    def test_validate_all_binary_hashes(self):
        files = hardware.firmware_files(self.root)
        self.assertEqual([item["offset"] for item in files], ["0x0", "0x8000", "0x10000"])
        self.assertTrue(all(len(item["sha256"]) == 64 for item in files))

    def test_reject_unsafe_manifest(self):
        for field, value in (("flash_files", {"0x0": "../../outside.bin"}),
                             ("flash_settings", dict(hardware.SETTINGS, flash_size="16MB")),
                             ("extra_esptool_args", {"chip": "esp32c6"}),
                             ("app", {"encrypted": "true"})):
            data = copy.deepcopy(self.manifest)
            data[field] = value
            self.write_manifest(data)
            with self.subTest(field=field), self.assertRaises(ValueError):
                hardware.firmware_files(self.root)

    def test_reject_empty_missing_or_overlapping_binaries(self):
        path = self.build / "bootloader/bootloader.bin"
        for size in (0, 0x8001):
            path.write_bytes(b"x" * size)
            with self.subTest(size=size), self.assertRaises(ValueError):
                hardware.firmware_files(self.root)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            hardware.firmware_files(self.root)

    def test_dry_run_never_launches_esptool(self):
        args = type("Args", (), {"artifact_root": str(self.root), "port": "/dev/serial/by-id/test",
                                 "baud": "460800", "source_run": "123", "source_sha": "a" * 40,
                                 "execute": False, "report": str(self.root / "report.json")})()
        with patch.object(hardware.subprocess, "run") as run:
            hardware.flash(args)
        run.assert_not_called()
        report = json.loads(Path(args.report).read_text())
        self.assertEqual(report["result"], "dry-run")
        self.assertEqual(report["source_run_id"], "123")
        self.assertIn("write-flash", report["command"])
        self.assertNotIn("erase-flash", report["command"])

    def test_invalid_linux_port_never_launches_esptool(self):
        args = type("Args", (), {"artifact_root": str(self.root), "port": "socket://host:1234",
                                 "baud": "460800", "source_run": "123", "source_sha": "a" * 40,
                                 "execute": True, "report": str(self.root / "report.json")})()
        with patch.object(hardware.sys, "platform", "linux"), patch.object(hardware.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                hardware.flash(args)
        run.assert_not_called()
        self.assertEqual(json.loads(Path(args.report).read_text())["result"], "failed")


if __name__ == "__main__":
    unittest.main()

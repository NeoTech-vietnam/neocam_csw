"""Developer command policies: cached assembly, live overrides and isolated envs."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

spec = importlib.util.spec_from_file_location("dev", Path(__file__).resolve().parents[1] / "TOOLCONF/dev.py")
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


class DeveloperCommandsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.work = self.root / ".workspace"
        for key, value in {"ROOT": self.root, "WORK": self.work, "STATE": self.work / "developer.json"}.items():
            patcher = patch.object(dev, key, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.manifest = {"packages": {"WifiStack": {"repo": "https://github.com/NeoTech-vietnam/WifiStack.git",
                                                   "ref": "a" * 40, "dest": "WifiStack"}}}
        (self.root / "packages.yml").write_text(yaml.safe_dump(self.manifest), encoding="utf-8")

    def test_exports_expand_path_without_executing_shell_text(self):
        original = {"PATH": "old", "KEEP": "value"}
        win = dev.apply_exports("PATH=C:\\tools;%PATH%\nSDK=x\n", original)
        linux = dev.apply_exports("PATH=/tools:$PATH\nSDK=$(do-not-run)\n", original)
        self.assertEqual(win["PATH"], "C:\\tools;old")
        self.assertEqual(linux["PATH"], "/tools:old")
        self.assertEqual(linux["SDK"], "$(do-not-run)")
        self.assertEqual(original, {"PATH": "old", "KEEP": "value"})

    def test_pip_isolation_preserves_parent_and_network_environment(self):
        original = {"PIP_INDEX_URL": "old-mirror", "PIP_EXTRA_INDEX_URL": "extra", "HTTPS_PROXY": "proxy"}
        with patch.dict(os.environ, {}, clear=True):
            result = dev.public_pip_environment(original)
        self.assertEqual(result["PIP_INDEX_URL"], "https://pypi.org/simple")
        self.assertEqual(result["HTTPS_PROXY"], "proxy")
        self.assertNotIn("PIP_EXTRA_INDEX_URL", result)
        self.assertEqual(original["PIP_INDEX_URL"], "old-mirror")

    def test_repeat_build_assembly_does_not_refetch(self):
        (self.root / "WifiStack").mkdir()
        self.work.mkdir()
        (self.work / "state.json").write_text("{}")
        with patch.object(dev, "run") as run:
            dev.sources()
            dev.sources()
            self.assertEqual(run.call_count, 1)
            self.manifest["packages"]["WifiStack"]["ref"] = "b" * 40
            (self.root / "packages.yml").write_text(yaml.safe_dump(self.manifest), encoding="utf-8")
            dev.sources()
            self.assertEqual(run.call_count, 2)

    def test_develop_preserves_checkout_edits_and_existing_overrides(self):
        checkout = self.root.parent / "modules/WifiStack"
        (checkout / ".git").mkdir(parents=True)
        edited = checkout / "work.c"
        edited.write_text("uncommitted development")
        local = self.root / "packages.local.yml"
        local.write_text(yaml.safe_dump({"overrides": {"Other": {"path": "../other"}}}), encoding="utf-8")
        with patch.object(dev, "sources") as sources, patch.object(dev, "git") as git:
            dev.develop("WifiStack")
        git.assert_not_called()
        sources.assert_called_once_with(force=True)
        overrides = yaml.safe_load(local.read_text())["overrides"]
        self.assertIn("Other", overrides)
        self.assertEqual(overrides["WifiStack"]["path"], "../modules/WifiStack")
        self.assertEqual(edited.read_text(), "uncommitted development")

    def test_invalid_module_never_creates_external_checkout(self):
        for module in ("", "../outside", "Unknown"):
            with self.subTest(module=module), self.assertRaises(RuntimeError), patch.object(dev, "git") as git:
                dev.develop(module)
            git.assert_not_called()

    def test_baseline_omits_overrides_without_deleting_configuration(self):
        local = self.root / "packages.local.yml"
        content = "overrides:\n  WifiStack:\n    path: ../modules/WifiStack\n"
        local.write_text(content)
        dev.save({"use_overrides": False})
        with patch.object(dev, "run") as run:
            dev.sources(force=True)
        self.assertNotIn("--overrides", run.call_args.args[0])
        self.assertEqual(local.read_text(), content)

    def test_flash_requires_saved_or_explicit_port_before_build(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(dev, "build") as build:
            with self.assertRaises(RuntimeError):
                dev.board("flash")
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()

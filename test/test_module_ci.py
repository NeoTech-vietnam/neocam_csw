"""Receiver restrictions are independent of the module's editable target YAML."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("module_ci", Path(__file__).resolve().parents[1] / "TOOLCONF/module_ci.py")
module_ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module_ci)
PACKAGES = {"WifiStack": {"repo": "https://github.com/NeoTech-vietnam/WifiStack.git"}}
SHA = "a" * 40


class ReceiverTests(unittest.TestCase):
    def validate(self, **overrides):
        args = dict(packages=PACKAGES, package="WifiStack", sha=SHA, source_repository="NeoTech-vietnam/WifiStack",
                    ref="refs/heads/feat/wifistack", default_branch="main")
        args.update(overrides)
        return module_ci.validate(**args)

    def test_development_branch_and_exact_revision_accepted(self):
        report = self.validate()
        self.assertEqual(report["module_sha"], SHA)
        self.assertEqual(report["project_branch"], "feat/wifistack")

    def test_main_default_branch_tags_and_aliases_rejected(self):
        for ref in ("refs/heads/main", "main", "refs/heads/master", "refs/tags/feat/wifi", SHA,
                    "refs/heads/feat/../main", "refs/heads/feat/wifi.lock"):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                self.validate(ref=ref)
        with self.assertRaises(ValueError):
            self.validate(default_branch="feat/wifistack")

    def test_mutable_revision_or_wrong_module_rejected(self):
        for overrides in ({"sha": "main"}, {"sha": "v1.0.0"}, {"package": "Unknown"},
                          {"source_repository": "NeoTech-vietnam/CamIo"}, {"source_repository": "outside/WifiStack"}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.validate(**overrides)


if __name__ == "__main__":
    unittest.main()

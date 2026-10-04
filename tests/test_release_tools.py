"""Portable release and configuration behavior, independent of workspace paths."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def module(self, relative, name):
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"Release tool missing: {relative}")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_snapshot_check_is_portable_by_default(self):
        module = self.module("tools/verify_sources.py", "release_sources")
        result = module.verify()
        self.assertTrue(result["preserved"])
        self.assertEqual(result["bundled_snapshots_checked"], 4)
        self.assertEqual(result["original_files_checked"], 0)

    def test_configs_distinguish_general_and_k2(self):
        module = self.module("examples/run_config.py", "release_config")
        general = module.load_config(ROOT / "configs/general_k.json")
        special = module.load_config(ROOT / "configs/k2.json")
        self.assertEqual(general["projection"]["method"], "general")
        self.assertEqual(special["projection"]["method"], "k2")
        self.assertEqual(special["projection"]["k"], 2)

    def test_misspelled_config_option_is_rejected(self):
        module = self.module("examples/run_config.py", "release_config")
        config = {"format_version": 1, "input": {"kind": "random", "shape": [4, 4], "seed": 7},
                  "projection": {"raduis": 1, "k": 2, "method": "k2", "hermitian": False},
                  "output_dir": "../outputs"}
        with self.assertRaises(ValueError):
            module.validate_config(config)


if __name__ == "__main__":
    unittest.main()

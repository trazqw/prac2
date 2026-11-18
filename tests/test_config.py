import tempfile
import unittest
from pathlib import Path

from src.main import load_config, main, validate_config


class ConfigTests(unittest.TestCase):

    def setUp(self):
        self.config = load_config()

    def test_example_configuration_is_valid(self):
        self.assertEqual(validate_config(self.config), [])

    def test_three_demonstration_configs_are_valid(self):
        for name in ("b", "c"):
            path = Path("examples") / f"config_{name}.xml"
            with self.subTest(path=path):
                config = load_config(path)
                self.assertEqual(validate_config(config), [])

    def test_empty_package_name_is_rejected(self):
        self.config["package_name"] = ""
        self.assertTrue(validate_config(self.config))

    def test_lowercase_test_package_is_rejected(self):
        self.config["package_name"] = "test"
        self.assertTrue(validate_config(self.config))

    def test_empty_version_is_rejected(self):
        self.config["package_version"] = ""
        self.assertTrue(validate_config(self.config))

    def test_invalid_version_is_rejected(self):
        self.config["package_version"] = "latest"
        self.assertTrue(validate_config(self.config))

    def test_bad_url_is_rejected(self):
        self.config["repository_url"] = "https://"
        self.assertTrue(validate_config(self.config))

    def test_bad_url_port_is_rejected(self):
        self.config["repository_url"] = "https://example.org:invalid"
        self.assertTrue(validate_config(self.config))

    def test_bad_test_mode_is_rejected(self):
        self.config["test_mode"] = "sometimes"
        self.assertTrue(validate_config(self.config))

    def test_missing_test_repository_is_rejected(self):
        self.config["test_repository_path"] = "no-such-file.json"
        self.assertTrue(validate_config(self.config))

    def test_non_svg_output_is_rejected(self):
        self.config["output_file"] = "graph.png"
        self.assertTrue(validate_config(self.config))

    def test_negative_depth_is_rejected(self):
        self.config["max_depth"] = "-1"
        self.assertTrue(validate_config(self.config))

    def test_non_numeric_depth_is_rejected(self):
        self.config["max_depth"] = "many"
        self.assertTrue(validate_config(self.config))

    def test_zero_depth_is_allowed(self):
        self.config["max_depth"] = "0"
        self.assertEqual(validate_config(self.config), [])

    def test_empty_filter_is_allowed(self):
        self.config["filter_substring"] = ""
        self.assertEqual(validate_config(self.config), [])

    def test_missing_configuration_fails_with_nonzero_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "not_found.xml"
            self.assertEqual(main(["--config", str(path)]), 1)

    def test_malformed_xml_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.xml"
            path.write_text("<configuration>", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_missing_required_xml_element_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.xml"
            path.write_text("<configuration/>", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()

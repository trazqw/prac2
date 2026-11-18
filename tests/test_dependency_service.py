
import unittest
from unittest.mock import patch

from src.dependency_service import (
    get_direct_dependencies,
    get_latest_version,
)


class DependencyServiceTests(unittest.TestCase):

    @patch("src.dependency_service._get_json")
    def test_direct_dependencies_use_exact_version(self, get_json):
        get_json.return_value = {"dependencies": [{"crate_id": "foo"}]}
        dependencies = get_direct_dependencies(
            "https://crates.io/api/v1", "serde", "1.0.188"
        )
        self.assertEqual(dependencies, [{"crate_id": "foo"}])
        get_json.assert_called_once_with(
            "https://crates.io/api/v1/crates/serde/1.0.188/dependencies"
        )

    @patch("src.dependency_service._get_json")
    def test_latest_version(self, get_json):
        get_json.return_value = {"crate": {"max_version": "2.0.0"}}
        self.assertEqual(
            get_latest_version("https://crates.io/api/v1", "foo"),
            "2.0.0",
        )

    @patch("src.dependency_service._get_json")
    def test_bad_api_response_raises(self, get_json):
        get_json.return_value = {"something_else": []}
        with self.assertRaises(ValueError):
            get_direct_dependencies("https://example.org", "foo", "1.0.0")


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.graph_service import (
    build_graph,
    find_reverse_dependencies,
    load_test_graph,
)

class GraphServiceTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.graph_path = Path(self.temp_dir.name) / "graph.json"
        self.graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D", "E"],
            "D": ["A"],
            "E": ["F"],
            "F": [],
        }
        self.graph_path.write_text(
            json.dumps(self.graph), encoding="utf-8"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def build(self, package="A", depth=3, filter_text=""):
        return build_graph(
            package_name=package,
            package_version="1.0.0",
            repository_url="https://crates.io/api/v1",
            max_depth=depth,
            filter_substring=filter_text,
            test_mode=True,
            test_repository_path=str(self.graph_path),
        )

    def test_bfs_builds_transitive_graph(self):
        result = self.build()
        self.assertEqual(result, {
            "A": ["B", "C"], "B": ["D"], "C": ["D", "E"],
            "D": ["A"], "E": ["F"], "F": [],
        })

    def test_filter_excludes_matching_package(self):
        result = self.build(filter_text="E")
        self.assertNotIn("E", result["C"])
        self.assertEqual(result["C"], ["D"])
        self.assertNotIn("F", result)

    def test_zero_depth_returns_root(self):
        self.assertEqual(self.build(depth=0), {"A": []})

    def test_wide_recursive_bfs_avoids_per_node_recursion(self):
        packages = [
            chr(65 + left) + chr(65 + right) + chr(65 + last)
            for left in range(2)
            for right in range(26)
            for last in range(26)
        ]
        self.graph = {"A": packages}
        self.graph.update({name: [] for name in packages})
        self.graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
        result = self.build(depth=1)
        self.assertEqual(len(result), len(packages) + 1)
        self.assertEqual(
            len(find_reverse_dependencies(result, packages[0])), 1
        )

    def test_cycles_do_not_repeat_nodes(self):
        result = self.build(depth=10)
        self.assertEqual(set(result), set(self.graph))

    def test_reverse_dependencies_are_transitive(self):
        found = find_reverse_dependencies(self.graph, "D")
        self.assertEqual(set(found), {"A", "B", "C"})

    def test_reverse_dependencies_handle_cycle(self):
        found = find_reverse_dependencies(self.graph, "A")
        self.assertEqual(set(found), {"B", "C", "D"})

    def test_missing_package_raises(self):
        with self.assertRaises(ValueError):
            self.build(package="Z")

    def test_invalid_test_graph_is_rejected(self):
        self.graph_path.write_text(
            '{"A": ["bad-name"]}', encoding="utf-8"
        )
        with self.assertRaises(ValueError):
            load_test_graph(str(self.graph_path))

    def test_real_mode_uses_requested_root_version(self):
        with patch(
            "src.graph_service.get_direct_dependencies",
            return_value=[],
        ) as get_dependencies:
            result = build_graph(
                "serde", "1.0.0", "https://crates.io/api/v1",
                1, "", False, "",
            )
        self.assertEqual(result, {"serde": []})
        get_dependencies.assert_called_once_with(
            "https://crates.io/api/v1", "serde", "1.0.0"
        )


if __name__ == "__main__":
    unittest.main()

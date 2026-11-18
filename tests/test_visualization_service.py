
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.visualization_service import (
    generate_mermaid,
    save_graph_visualization,
)


class VisualizationTests(unittest.TestCase):

    def test_mermaid_includes_isolated_nodes_and_edges(self):
        diagram = generate_mermaid({"A": ["B"], "B": [], "C": []})
        self.assertTrue(diagram.startswith("flowchart TD\n"))
        self.assertIn('node_0["A"]', diagram)
        self.assertIn('node_2["C"]', diagram)
        self.assertIn("node_0 --> node_1", diagram)

    def test_non_svg_output_is_rejected(self):
        with self.assertRaises(ValueError):
            save_graph_visualization({"A": []}, "graph.png")

    @patch("src.visualization_service._find_mmdc", return_value=None)
    def test_missing_renderer_has_clear_error(self, _find_mmdc):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "graph.svg"
            with self.assertRaisesRegex(ValueError, "npm install"):
                save_graph_visualization({"A": []}, output)
            self.assertTrue(output.with_suffix(".mmd").is_file())


if __name__ == "__main__":
    unittest.main()

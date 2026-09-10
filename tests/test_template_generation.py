"""Generation tests for the Cookiecutter template."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]


class TemplateGenerationTest(unittest.TestCase):
    """Verify generated projects retain the template's key invariants."""

    def test_ci_uses_github_hosted_runners_for_each_visibility(self) -> None:
        """Both public and private projects use only hosted Ubuntu runners."""
        cookiecutter = shutil.which("cookiecutter")
        if cookiecutter is None:
            raise AssertionError(
                "cookiecutter must be installed to run generation tests"
            )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory)
            for open_source in ("y", "n"):
                project_name = f"generated_project_{open_source}"
                context = {
                    "project_name": project_name,
                    "project_description": "A generated test project",
                    "author_name": "Template Test",
                    "email": "template@example.com",
                    "github_org": "example-org",
                    "open_source": open_source,
                    "include_frontend": "n",
                    "include_database": "n",
                    "python_version": "3.12",
                }
                command = [
                    cookiecutter,
                    str(TEMPLATE_ROOT),
                    "--no-input",
                    "--output-dir",
                    str(output_root),
                    *(f"{key}={value}" for key, value in context.items()),
                ]
                subprocess.run(command, check=True, cwd=TEMPLATE_ROOT)

                project_root = output_root / project_name
                workflow_files = list(
                    (project_root / ".github" / "workflows").glob("*")
                )
                self.assertTrue(workflow_files)
                for workflow_file in workflow_files:
                    workflow = workflow_file.read_text()
                    self.assertNotIn("self-hosted", workflow.lower())

                ci_workflow = (
                    project_root / ".github" / "workflows" / "ci.yaml"
                ).read_text()
                self.assertIn("runs-on: ubuntu-latest", ci_workflow)
                self.assertIn("os: [ubuntu-latest]", ci_workflow)

                self.assertEqual(
                    (project_root / "LICENSE").exists(),
                    open_source == "y",
                )


if __name__ == "__main__":
    unittest.main()

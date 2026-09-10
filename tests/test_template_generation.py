"""Generation tests for the Cookiecutter template."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
HOSTED_RUNNERS = frozenset({"windows-latest", "macos-latest", "ubuntu-latest"})
MATRIX_RUNNER = "${{ matrix.os }}"


class TemplateGenerationTest(unittest.TestCase):
    """Verify generated projects retain the template's key invariants."""

    def test_ci_uses_github_hosted_runners_for_each_visibility(self) -> None:
        """Both visibility variants configure only GitHub-hosted runners."""
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
                rendered_workflow = yaml.safe_load(ci_workflow)
                if not isinstance(rendered_workflow, dict):
                    self.fail("Rendered CI workflow must be a mapping")
                expected_matrix = (
                    ["windows-latest", "macos-latest", "ubuntu-latest"]
                    if open_source == "y"
                    else ["ubuntu-latest"]
                )
                self._assert_hosted_runners(
                    workflow=rendered_workflow,
                    expected_matrix=expected_matrix,
                )

                self.assertEqual(
                    (project_root / "LICENSE").exists(),
                    open_source == "y",
                )

    def _assert_hosted_runners(
        self,
        workflow: dict[str, object],
        expected_matrix: list[str],
    ) -> None:
        """Assert every job resolves to an expected GitHub-hosted runner."""
        jobs = workflow.get("jobs")
        if not isinstance(jobs, dict):
            self.fail("CI workflow must define jobs as a mapping")

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                self.fail(f"Job {job_name!r} must be a mapping")

            strategy = job.get("strategy")
            matrix_os = None
            if strategy is not None:
                if not isinstance(strategy, dict):
                    self.fail(f"Job {job_name!r} strategy must be a mapping")
                matrix = strategy.get("matrix")
                if not isinstance(matrix, dict):
                    self.fail(f"Job {job_name!r} matrix must be a mapping")
                matrix_os = matrix.get("os")
                if "os" in matrix:
                    self.assertEqual(matrix_os, expected_matrix, job_name)

            runs_on = job.get("runs-on")
            if runs_on is None:
                self.fail(f"Job {job_name!r} must define runs-on")

            if runs_on == MATRIX_RUNNER:
                self.assertEqual(matrix_os, expected_matrix, job_name)
            elif isinstance(runs_on, str):
                self.assertIn(runs_on, HOSTED_RUNNERS, job_name)
            else:
                if not isinstance(runs_on, list) or not runs_on:
                    self.fail(f"Job {job_name!r} has invalid runs-on")
                for runner in runs_on:
                    if not isinstance(runner, str):
                        self.fail(f"Job {job_name!r} has an invalid runner label")
                    self.assertIn(runner, HOSTED_RUNNERS, job_name)


if __name__ == "__main__":
    unittest.main()

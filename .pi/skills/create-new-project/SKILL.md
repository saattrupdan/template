---
name: create-new-project
description: >-
  Create a new Python or full-stack project from saattrupdan/template with
  Cookiecutter. Use when asked to scaffold, bootstrap, or start a repository from
  this template, including choosing backend, Vue frontend, PostgreSQL, licensing,
  Python version, initial setup, and validation.
last-updated: 2026-09-06
---

# Create a new project

Use Cookiecutter to generate projects from `saattrupdan/template`. Never manually copy
or rename the template files: Cookiecutter renders conditional filenames, applies the
selected options, and runs the post-generation cleanup hook.

## 1. Check or install Cookiecutter

Check first:

```bash
command -v cookiecutter
cookiecutter --version
```

If `cookiecutter` is missing, explain that creating the project requires installing a
local command and get permission before changing the host. Install it without `sudo`,
using the first available option:

```bash
# Preferred when uv is available
uv tool install cookiecutter

# Otherwise, when pipx is available
pipx install cookiecutter

# Last resort: an isolated virtual environment, safe under PEP 668
python3 -m venv "$HOME/.local/share/cookiecutter-venv"
"$HOME/.local/share/cookiecutter-venv/bin/python" -m pip install cookiecutter
export PATH="$HOME/.local/share/cookiecutter-venv/bin:$PATH"
```

After installation, run `command -v cookiecutter` again. If the virtual-environment
fallback was used, either invoke its `cookiecutter` executable by absolute path or add
its `bin` directory to the shell's persistent `PATH` with the user's permission. Do not
replace or upgrade an existing installation merely because it is not the newest
version.

## 2. Gather the project choices

Determine these values before generation:

- `project_name`: valid Python package name in `snake_case`; also becomes the
  directory name.
- `project_description`: short, plain-text description.
- `author_name`: author's full name.
- `email`: author or maintainer email.
- `github_org`: GitHub user or organisation that will own the repository; not a URL.
- `open_source`: `y` adds public-project files such as LICENSE; otherwise `n`.
- `include_frontend`: `y` adds Vue, Vite, TypeScript, and a FastAPI backend;
  otherwise `n`.
- `include_database`: `y` adds PostgreSQL and Docker Compose support; otherwise
  `n`.
- `python_version`: normally the template default unless another version is
  requested.

Treat `open_source`, `include_frontend`, and `include_database` as user-visible scope.
Do not silently choose them when the request does not make the intended project shape
clear. Require exact lowercase `y` or `n`; values such as `Y` and `yes` silently behave
as `n` in this template.

Validate that `project_name`:

- matches `^[a-z][a-z0-9_]*$`;
- is a Python identifier and not a Python keyword;
- is neither `frontend` nor `scripts`, which collide with existing `src` directories;
  and
- does not already name a directory in the output location.

The template inserts text values directly into TOML, Python, and shell-bearing files
without context-aware escaping. Apply these checks before invoking Cookiecutter:

- Require `github_org` to match
  `^(?!.*--)[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$`. This prevents both
  invalid GitHub owners and shell metacharacters in the generated Makefile.
- Require `project_description`, `author_name`, and `email` to be single-line values
  containing no control characters, backslashes, double quotes, dollar signs,
  backticks, `{{`, or `{%`.
- Also reject `#` and `=` in `author_name` and `email`: both values pass through an
  unquoted `.env` file before Make expands them into shell recipes.
- Require `email` to have one non-empty local part, one `@`, and a dotted domain. Do not
  attempt to repair or shell-escape rejected input; ask for a safe equivalent.

Use the template's Python 3.12 default unless the user requires another version. A
custom version must use `major.minor` form and be supported by uv, the official Python
Docker images, GitHub Actions, and Ruff's corresponding `pyXY` target.

## 3. Choose the template source and output directory

Use the published template unless the user explicitly wants local, unreleased template
changes:

```text
gh:saattrupdan/template
```

When working from a checkout of the template itself, use its absolute repository root
only when local changes are intended:

```bash
git rev-parse --show-toplevel
```

Generate from the parent directory in which the new project should live, or pass that
parent with `--output-dir`. Inspect the destination first. Never use
`--overwrite-if-exists` or `-f` unless the user explicitly permits overwriting an
existing project; `-f` means overwrite, not "fetch the newest template."

## 4. Generate the project

### Interactive generation

Use this when a person is available to answer Cookiecutter's prompts:

```bash
cookiecutter gh:saattrupdan/template --output-dir '/path/to/parent'
```

If Cookiecutter asks whether to delete and re-download its cached template, answer yes
when the newest published template is required. Accept the template hook so unwanted
frontend directories can be removed correctly.

### Non-interactive generation

Agents should generally use an explicit, reproducible invocation after all choices are
known. Supply every public template value because the strings in `cookiecutter.json`
are prompts, not usable project defaults.

Do not interpolate user values into a shell command. Write the validated values to a
temporary JSON file using a JSON serializer or the agent's structured file-write tool:

```json
{
  "project_name": "my_project",
  "project_description": "Short description",
  "author_name": "Full Name",
  "email": "name@example.com",
  "github_org": "my-github-org",
  "open_source": "n",
  "include_frontend": "n",
  "include_database": "n",
  "python_version": "3.12"
}
```

Then pass every value to Cookiecutter as a subprocess argument, never through shell
re-parsing. Shell-quote the context and output paths themselves:

```bash
python3 - '/path/to/context.json' '/path/to/parent' <<'PY'
import json
import shutil
import subprocess
import sys
from pathlib import Path

context_path = Path(sys.argv[1])
context = json.loads(context_path.read_text())
cookiecutter = shutil.which("cookiecutter")
if cookiecutter is None:
    raise SystemExit("cookiecutter is not on PATH")

command = [
    cookiecutter,
    "gh:saattrupdan/template",
    "--no-input",
    "--output-dir",
    sys.argv[2],
]
command.extend(f"{key}={value}" for key, value in context.items())
subprocess.run(command, check=True)
context_path.unlink()
PY
```

`--no-input` re-downloads cached remote resources in current Cookiecutter releases.
Do not pass private `_...` version fields: the template owns those values.

## 5. Inspect before setup

Enter the generated directory and verify that rendering completed correctly:

```bash
cd '/path/to/parent/my_project'
git status --short --branch 2>/dev/null || true
rg --hidden -n '\{\{[[:space:]]*cookiecutter|\{%|cookiecutter\.' . \
  --glob '!.git/**' --glob '!uv.lock' --glob '!package-lock.json'
```

The second command should return no unresolved template expressions. Confirm that the
selected project shape is present:

- Backend-only projects have the Python package and a single `Dockerfile`.
- Frontend projects have `src/frontend`, `package.json`, Vite files, and separate
  backend/frontend Dockerfiles.
- Database or frontend projects have `docker-compose.yaml`.
- Public projects have LICENSE, CODE_OF_CONDUCT.md, CONTRIBUTING.md, and SECURITY.md.

If generation fails, report the error and inspect any retained output before retrying.
Do not merge a partial generation into an existing directory.

## 6. Install and initialise the generated project

Generation-only is the default stopping point. Read the generated `AGENTS.md` before
editing code or running setup. The Makefile setup is consequential: it can install Rust,
install or update uv, install Python, download project dependencies, run `npm install`,
set the global Git default branch to `main`, initialise a repository, create a commit,
and add an SSH `origin`. Explain these effects and get permission before proceeding.

After permission, choose the setup path:

```bash
# Interactive environment-variable setup
make install

# Non-interactive environment-variable setup; not side-effect-free
make install-non-interactive
```

Use `make install-non-interactive` for unattended work. For frontend projects, confirm
that `npm` exists before setup. Inspect the resulting git identity, commit, and remote
instead of assuming they are correct:

```bash
git log -1 --oneline
git remote -v
git config --local user.name
git config --local user.email
```

Creating the remote GitHub repository or pushing commits is a separate, consequential
action. Do it only when requested, using the GitHub workflow available to the agent.

## 7. Validate the result

Run the generated project's checks after installation:

```bash
make check
uv run pytest
```

For a frontend project, `make check` also runs the frontend checks. Do not use
`make test` merely for validation: it updates the README coverage badge and attempts to
create a commit. Report the generated path, chosen project shape, setup status, check
results, and any remaining step such as creating the remote repository.

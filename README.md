# code_review

Central hub for reusable GitHub Actions workflows. Other repositories call these workflows to get automated PR testing and AI-powered code review.

## What runs on every PR

| Check | Tool |
|---|---|
| Linting | [ruff](https://docs.astral.sh/ruff/) |
| Type checking (optional) | [mypy](https://mypy.readthedocs.io/) |
| Tests | [pytest](https://pytest.org/) |
| AI code review | Claude (Anthropic) |

## Quick start

### 1. Push this repo to GitHub

```bash
gh repo create YOUR_GITHUB_USERNAME/code_review --public --push
```

### 2. Add your Anthropic API key as a secret

In each target repo (or at the org level):

**GitHub → Settings → Secrets and Actions → New repository secret**

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your key from [console.anthropic.com](https://console.anthropic.com) |

### 3. Copy the caller template into a target repo

```bash
cp .github/workflows/example-caller.yml path/to/your-repo/.github/workflows/ci.yml
```

Then edit it:
- Replace `YOUR_GITHUB_USERNAME` with your GitHub username
- Adjust `install-command`, `test-command`, and `runs-on` as needed

### 4. Open a PR in the target repo

The lint, test, and AI review jobs will run automatically.

---

## Runner options

Three runner configurations are supported — switch with a single line change.

See [docs/runner-options.md](docs/runner-options.md) for setup instructions.

| Option | `runs-on` value | Notes |
|---|---|---|
| GitHub-hosted | `'"ubuntu-latest"'` | No setup needed |
| Self-hosted VPS | `'["self-hosted","linux"]'` | Register runner on your Ubuntu VPS |
| K8s ARC | `'["self-hosted","linux","k8s"]'` | Deploy ARC on your cluster |

---

## Repository layout

```
.github/
  workflows/
    reusable-lint-test.yml     # Reusable: ruff, mypy, pytest
    reusable-ai-review.yml     # Reusable: Claude PR review
    example-caller.yml         # Template — copy this into target repos
scripts/
  ai_review.py                 # Claude API call (stdlib only, no pip install)
docs/
  runner-options.md            # Runner comparison + setup guides
```

## Inputs reference

### `reusable-lint-test.yml`

| Input | Default | Description |
|---|---|---|
| `python-version` | `3.12` | Python version |
| `runs-on` | `'"ubuntu-latest"'` | Runner (JSON-encoded) |
| `working-directory` | `.` | Project root |
| `install-command` | `pip install -e ".[dev]"` | Dependency install |
| `lint-command` | `ruff check . && ruff format --check .` | Lint command |
| `type-check` | `false` | Enable mypy |
| `test-command` | `pytest --tb=short` | Test command |
| `upload-coverage` | `false` | Upload htmlcov artifact |

### `reusable-ai-review.yml`

| Input | Default | Description |
|---|---|---|
| `runs-on` | `'"ubuntu-latest"'` | Runner (JSON-encoded) |
| `model` | `claude-sonnet-4-6` | Claude model ID |
| `max-diff-bytes` | `50000` | Truncate diff at this size |

| Secret | Required | Description |
|---|---|---|
| `anthropic-api-key` | Yes | Anthropic API key |

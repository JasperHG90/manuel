alias s := setup
alias t := test
alias p := pre_commit
alias b := build
alias v := version

# Install python dependencies
install:
  uv sync --all-extras

# Install pre-commit hooks
pre_commit_setup:
  uv run pre-commit install

# Install python dependencies and pre-commit hooks
setup: install pre_commit_setup

# Run pre-commit
pre_commit:
 uv run pre-commit run -a

# Run pytest
test:
  uv run pytest tests

# Add scripts
add_scripts:
  uv add --script scripts/this.py 'typer>=0.12.5'
  uv add --script scripts/that.py 'typer>=0.12.5'

# Build dockerfile for DAG
build target:
  docker build -t dags/{{target}} --build-arg PACKAGE={{target}} .

# Get the latest version of the package
version:
  GIT_VERSION_ROOT_DIR=/home/vscode/workspace
  GIT_VERSION_PYPROJECT_PATH=/home/vscode/workspace/pyproject.toml
  uv run scripts/git_version.py version

# Run dagster in development model
dagster_dev:
    #!/usr/bin/env bash
    set -eo pipefail
    mkdir -p .dagster
    cp dagster.yaml .dagster/dagster.yaml
    export DAGSTER_HOME=$(pwd)/.dagster
    uv run packages/luchtmeetnet/dagster_dev.py

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "gitpython==3.1.43",
#     "pydantic==2.9.1",
#     "typer==0.12.5",
# ]
# ///

"""
Python script that returns a version string based on the git history of a repository.

Some of the code has been copied or adapted from <https://gitlab.com/rocshers/python/poetry-git-version-plugin/-/tree/release?ref_type=heads>.
Since this repository does not use poetry, I wanted a standalone script that can be used to version a python repository in a similar way.

### Usage

The script is intended to be used as a CLI tool, and can be run with the following command:

```bash
python git_version.py version \
    path/to/git/repo \
    --path-to-pyproject path/to/pyproject.toml
```

The script will automatically parse configuration options from a `pyproject.toml` file in the current working directory if available.
You can pass a path to a `pyproject.toml` file with the `--path-to-pyproject` option.

You may also use environment variables:

```bash
export GIT_VERSION_ROOT_DIR=path/to/git/repo
export GIT_VERSION_PYPROJECT_PATH=path/to/pyproject.toml
python git_version.py version
```

To enable debug logging, use the `--debug` option:

```bash
python git_version.py --debug version ...
```

### Configuration

The configuration options are limited. This script will either:
- Parse a tag name from a git source and return the version string
- Parse a tag name from a git source and return the version string, with the distance from the last tag and optionally the commit hash

You can also specify a pyproject.toml file with a `tool.git-version` section to configure the script:

```toml
[tool.git-version]
pre_release_commit_hash = true # Set to false if you don't want to include the commit hash in the version string
```
"""

import dataclasses
import logging
import os
import pathlib as plb
import re
import tomllib
import typing

import pydantic
import typer
from git import Repo, Tag
from git.objects import Commit
from typing_extensions import Annotated, TypedDict

logger = logging.getLogger("git-version")
handler = logging.StreamHandler()
format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


REGEX_PATTERN = re.compile(
    r"^[v]?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<pre_release>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<build_metadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


VersionDict = TypedDict(
    "VersionDict",
    {
        "major": int,
        "minor": int,
        "patch": int,
        "pre_release": str,
        "build_metadata": str,
    },
)


class GitVersionConfig(pydantic.BaseModel):
    pre_release_commit_hash: bool


default_conf = GitVersionConfig(pre_release_commit_hash=False)


def get_version_config(
    path_to_pyproject: typing.Optional[plb.Path] = None,
) -> GitVersionConfig:
    """Parse git version config from a pyproject.toml file

    Args:
        path_to_pyproject (typing.Optional[str], optional): Explicit path to a pyproject.toml. Defaults to None, in which
         case we look for a pyproject.toml file in the current working directory.

    Returns:
        GitVersionConfig: A pydantic model with the parsed configuration
    """
    if path_to_pyproject is not None:
        path = plb.Path(path_to_pyproject)
    else:  # Use current wd
        logger.debug(f"Using current working directory to parse options: {os.getcwd()}")
        path = plb.Path(os.getcwd()) / "pyproject.toml"
    logger.debug(f"Path to pyproject.toml: {path}")
    conf = default_conf.model_copy()
    if path.exists() and path.is_file():
        logger.debug(f"Found file at {path}")
        with path.open("rb") as inFile:
            pyproject_def = tomllib.load(inFile)
        if pyproject_def.get("tool"):
            if pyproject_def["tool"].get("git-version"):
                logger.debug("Found git-version config in pyproject.toml")
                logger.debug(f"Config: {pyproject_def['tool']['git-version']}")
                conf = GitVersionConfig(**pyproject_def["tool"]["git-version"])
    else:
        logger.debug(f"No file found at {path}")
        logger.debug(f"Returning default config: {conf}")
    return conf


class GitRepo:
    """
    Class to handle git repository operations for versioning
    """

    def __init__(self, repo: Repo):
        """
        Args:
            path (str): Path to git repository
        """
        self.repo = repo

    @property
    def commits(self) -> typing.List[Commit]:
        return [*self.repo.iter_commits()]

    @property
    def head_commit(self) -> Commit:
        return self.repo.head.commit

    @property
    def tags(self) -> typing.List[Tag]:
        return [*reversed([*self.repo.tags])]

    def current_tag(self) -> typing.Optional[Tag]:
        for tag in self.tags:
            if tag.commit == self.head_commit:
                return tag
        return None

    def get_last_tag(self) -> typing.Optional[Tag]:
        tag_dict = {tag.commit: tag for tag in self.tags}

        for commit in self.commits:
            if commit in tag_dict:
                return tag_dict[commit]

        return None

    def get_commit_short_hash(self, commit: Commit) -> str:
        return commit.hexsha[:7]

    def get_distance(self, from_commit: Commit, to_commit: Commit) -> int:
        return len(
            [*self.repo.iter_commits(f"{from_commit.hexsha}...{to_commit.hexsha}")]
        )


@dataclasses.dataclass
class VersionInfo:
    major: int
    minor: int
    patch: int
    distance: int
    commit_hash_short: typing.Optional[str]
    pre_release: str
    build_metadata: str

    def fmt(self) -> str:
        """Format version information into <MAJOR>.<MINOR>.<PATCH> possible with
         distance and commit hash

        Returns:
            str: Formatted version string
        """
        ver = f"{self.major}.{self.minor}.{self.patch}"
        if self.distance > 0:
            ver += (
                f"a{self.distance}+{self.commit_hash_short}"
                if self.commit_hash_short
                else f"a{self.distance}"
            )
        return ver


def parse_tag(tag: typing.Optional[Tag]) -> VersionDict:
    """Parse a git tag into a dictionary with version information

    Args:
        tag (typing.Optional[Tag]): Git Tag object to parse. If None, returns a dictionary with default info

    Returns:
        typing.Dict[str, typing.Union[str, int]]: Dictionary with version information
    """

    if tag is None:
        return {
            "major": 0,
            "minor": 0,
            "patch": 0,
            "pre_release": "",
            "build_metadata": "",
        }
    else:
        reg = REGEX_PATTERN.search(tag.name)
        reg_dict = {}

        if reg is not None:
            reg_dict = reg.groupdict()
        else:
            logger.warning(f"Could not parse tag {tag.name}. Returning default values")

        return {
            "major": int(reg_dict.get("major", 0)),
            "minor": int(reg_dict.get("minor", 0)),
            "patch": int(reg_dict.get("patch", 0)),
            "pre_release": reg_dict.get("pre_release", ""),
            "build_metadata": reg_dict.get("build_metadata", ""),
        }


def get_version_info(
    parsed_tag: VersionDict,
    distance: int,
    commit_hash_short: typing.Optional[str] = None,
) -> VersionInfo:
    """Create a VersionInfo object from parsed tag information

    Args:
        parsed_tag (VersionDict): Dictionary with parsed tag information
        distance (int): Distance from last tag, i.e. number of commits since last tag
        commit_hash_short (typing.Optional[str], optional): Git commit SHA, shortened to 8 characters.
            If given, will be added to version information Defaults to None.

    Returns:
        VersionInfo: VersionInfo object
    """
    return VersionInfo(
        **parsed_tag, distance=distance, commit_hash_short=commit_hash_short
    )


class Versioner:

    def __init__(self, repo_info: GitRepo, config: GitVersionConfig):
        """Main class to handle versioning from a git repository

        Args:
            repo_info (GitRepo): GitRepo object with repository information
            config (GitVersionConfig): Configuration object
        """
        self.repo = repo_info
        self.config = config
        self.version_info = self._get_version()

    @property
    def version(self) -> str:
        return self.version_info.fmt()

    def _get_version(self) -> VersionInfo:

        last_tag = self.repo.get_last_tag()
        last_tag_commit = (
            last_tag.commit if last_tag is not None else self.repo.commits[-1]
        )
        distance = self.repo.get_distance(self.repo.head_commit, last_tag_commit)
        commit_hash_short = self.repo.get_commit_short_hash(self.repo.head_commit)

        return get_version_info(
            parse_tag(last_tag),
            distance,
            commit_hash_short if self.config.pre_release_commit_hash else None,
        )


app = typer.Typer(
    name="git-version",
    no_args_is_help=True,
    help="A tool to handle versioning from git repositories",
    pretty_exceptions_show_locals=False,
)


@app.callback()
def main(debug: bool = typer.Option(False, help="Enable debug logging.")):
    if debug:
        logger.setLevel(logging.DEBUG)


@app.command()
def version(
    path_to_repo: Annotated[
        plb.Path,
        typer.Argument(
            help="Path to git repository. Defaults to current working directory",
            envvar="GIT_VERSION_ROOT_DIR",
        ),
    ] = plb.Path.cwd().resolve(),
    path_to_pyproject: Annotated[
        typing.Optional[plb.Path],
        typer.Option(
            help="Path to pyproject.toml that contains a 'tool.git-version' configuration",
            envvar="GIT_VERSION_PYPROJECT_PATH",
        ),
    ] = None,
):
    """Get the current version of a git repository"""
    ver = Versioner(
        GitRepo(repo=Repo(path_to_repo)), get_version_config(path_to_pyproject)
    )
    typer.echo(ver.version)


if __name__ == "__main__":
    app()

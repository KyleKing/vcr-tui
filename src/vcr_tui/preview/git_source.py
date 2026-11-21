# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Read the files under a directory that differ from a git ref, and their old text."""

import shutil
import subprocess  # noqa: S404
from dataclasses import dataclass
from itertools import starmap
from pathlib import Path
from typing import Literal

ChangeStatus = Literal['added', 'deleted', 'modified']
_STATUS: dict[str, ChangeStatus] = {
    'A': 'added',
    'D': 'deleted',
    'M': 'modified',
    'T': 'modified',
}


class GitError(RuntimeError):
    """Raised when git is missing or a git command fails."""


@dataclass(frozen=True)
class ChangedFile:
    """A file under the directory whose working-tree content differs from the ref."""

    path: Path
    status: ChangeStatus


def _git(cwd: Path, *args: str) -> str:
    executable = shutil.which('git')
    if executable is None:
        msg = 'git is not installed or not on PATH'
        raise GitError(msg)
    result = subprocess.run(  # noqa: S603
        [executable, '-c', 'core.quotePath=false', *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or f'git {args[0]} exited with {result.returncode}'
        raise GitError(msg)
    return result.stdout


def _check_ref(ref: str) -> None:
    if not ref or ref.startswith('-'):
        msg = f'invalid git ref: {ref!r}'
        raise GitError(msg)


def repo_root(directory: Path) -> Path:
    """Return the top level of the git repository containing the directory."""
    return Path(_git(directory, 'rev-parse', '--show-toplevel').strip()).resolve()


def changed_files(directory: Path, ref: str) -> list[ChangedFile]:
    """List files under the directory that differ between the ref and the working tree.

    Includes untracked files (as added), so a freshly recorded cassette shows up
    before it is committed.

    Returns:
        The changed files with absolute paths, sorted by path.
    """
    _check_ref(ref)
    directory = directory.resolve()
    root = repo_root(directory)
    scope = str(directory)
    found: dict[Path, ChangeStatus] = {}

    tracked = _git(root, 'diff', '--name-status', '--no-renames', ref, '--', scope)
    for line in tracked.splitlines():
        code, _, name = line.partition('\t')
        status = _STATUS.get(code[:1])
        if status and name:
            found[root / name] = status

    untracked = _git(root, 'ls-files', '--others', '--exclude-standard', '--', scope)
    for name in untracked.splitlines():
        if name:
            found.setdefault(root / name, 'added')

    return list(starmap(ChangedFile, sorted(found.items())))


def read_at_ref(root: Path, path: Path, ref: str) -> str:
    """Return a file's content as of the ref, given the repository root from repo_root.

    A GitError propagates when the file did not exist at the ref.
    """
    _check_ref(ref)
    relative = path.resolve().relative_to(root).as_posix()
    return _git(root, 'show', f'{ref}:{relative}')

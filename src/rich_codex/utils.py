import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from git import Repo
from git.exc import InvalidGitRepositoryError
from jsonschema import Draft4Validator
from jsonschema.exceptions import ValidationError

# Importing codex_search at runtime would be circular
if TYPE_CHECKING:
    from rich_codex.codex_search import CodexSearch
    from rich_codex.rich_img import RichImg

log = logging.getLogger("rich-codex")


def relative_path(path: str | Path | None, base: Path | None = None) -> str:
    """Path relative to the working directory, or as given if it's outside it."""
    if path is None:
        return ""
    if base is None:
        base = Path.cwd()
    try:
        return str(Path(path).resolve().relative_to(base))
    except ValueError:
        log.debug(f"Couldn't find relative path for '{path}'")
        return str(path)


def clean_images(
    clean_img_paths_raw: str | None,
    img_obj: "RichImg | None",
    codex_obj: "CodexSearch | None",
) -> list[Path]:
    """Delete any images matching CLEAN_IMG_PATHS that were not generated.

    Useful to remove existing files when a target filename is changed.
    """
    clean_img_patterns = clean_list(clean_img_paths_raw.splitlines()) if clean_img_paths_raw else []

    if len(clean_img_patterns) == 0:
        log.debug("[dim]Nothing found to clean in 'clean_img_paths'")
        return []

    # Search glob patterns for images
    all_img_paths: set[Path] = set()
    for pattern in clean_img_patterns:
        for matched_path in Path.cwd().glob(pattern):
            all_img_paths.add(matched_path.resolve())
    if len(all_img_paths) == 0:
        log.debug("[dim]No files found matching 'clean_img_paths' glob patterns")
        return []

    # Collect list of generated images
    known_img_paths: set[Path] = set()
    if img_obj:
        for img_path in img_obj.img_paths:
            known_img_paths.add(Path(img_path).resolve())
    if codex_obj:
        for img in codex_obj.rich_imgs:
            for img_path in img.img_paths:
                known_img_paths.add(Path(img_path).resolve())

    # Paths found by glob that weren't generated, in a stable order
    clean_img_paths = sorted(all_img_paths - known_img_paths)
    if len(clean_img_paths) == 0:
        log.debug("[dim]All files found matching 'clean_img_paths' were generated in this run. Nothing to clean.")
        return []

    cwd = Path.cwd()
    for path in clean_img_paths:
        log.info(f"Deleting '{relative_path(path, cwd)}'")
        path.unlink()

    return clean_img_paths


def clean_list(unclean_lines: list[str]) -> list[str]:
    """Remove empty strings and comments from a list of config lines."""
    clean_lines: list[str] = []
    for line in unclean_lines:
        line = line.strip()
        if not line.startswith("#") and line:
            clean_lines.append(line)
    return clean_lines


def parse_extra_env(extra_env_raw: str) -> dict[str, str]:
    """Parse newline-separated 'KEY=value' pairs into a dict of environment variables."""
    extra_env: dict[str, str] = {}
    for line in clean_list(extra_env_raw.splitlines()):
        if "=" not in line:
            raise ValueError(f"Could not parse as 'KEY=value': '{line}'")
        key, value = line.split("=", 1)
        extra_env[key.strip()] = value.strip()
    return extra_env


def check_git_status() -> tuple[bool, str]:
    """Check if the working directory is a clean git repo."""
    try:
        repo = Repo(Path.cwd().resolve(), search_parent_directories=True)
        if repo.is_dirty(untracked_files=True):
            changedFiles = [item.a_path for item in repo.index.diff(None)]
            return (False, f"Found uncommitted changes: {changedFiles + repo.untracked_files}")
    except InvalidGitRepositoryError:
        return (False, "Does not appear to be a git repository")
    return (True, "Git repo looks good.")


def validate_config(
    schema: dict[str, Any],
    config: dict[str, Any],
    filename: str | Path,
    line_number: int | None = None,
) -> None:
    """Validate a config file string against the rich-codex JSON schema."""
    ln_text = f"line {line_number} " if line_number else ""
    v = Draft4Validator(schema)
    if not v.is_valid(config):
        err_msg = f"[red][✗] Rich-codex config in '{filename}' {ln_text}was invalid"

        for error in sorted(v.iter_errors(config), key=str):
            err_msg += f"\n - {error.message}"
            if len(error.context):
                err_msg += ":"
            for suberror in sorted(error.context, key=lambda e: e.schema_path):
                err_msg += f"\n     * {suberror.message}"
        raise ValidationError(err_msg)

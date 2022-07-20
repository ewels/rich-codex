import logging
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError
from jsonschema import Draft4Validator
from jsonschema.exceptions import ValidationError

log = logging.getLogger("rich-codex")


def clean_images(clean_img_paths_raw, img_obj, codex_obj):
    """Delete any images matching CLEAN_IMG_PATHS that were not generated.

    Useful to remove existing files when a target filename is changed.
    """
    clean_img_patterns = clean_img_paths_raw.splitlines() if clean_img_paths_raw else []

    if len(clean_img_patterns) == 0:
        log.debug("[dim]Nothing found to clean in 'clean_img_paths'")
        return []

    # Search glob patterns for images
    all_img_paths = set()
    for pattern in clean_img_patterns:
        for matched_path in Path.cwd().glob(pattern):
            all_img_paths.add(matched_path.resolve())
    if len(all_img_paths) == 0:
        log.debug("[dim]No files found matching 'clean_img_paths' glob patterns")
        return []

    # Collect list of generated images
    known_img_paths = set()
    if img_obj:
        for img_path in img_obj.img_paths:
            known_img_paths.add(Path(img_path).resolve())
    if codex_obj:
        for img in codex_obj.rich_imgs:
            for img_path in img.img_paths:
                known_img_paths.add(Path(img_path).resolve())

    # Paths found by glob that weren't generated
    clean_img_paths = all_img_paths - known_img_paths
    if len(clean_img_paths) == 0:
        log.debug("[dim]All files found matching 'clean_img_paths' were generated in this run. Nothing to clean.")
        return []

    for path in clean_img_paths:
        path_to_delete = Path(path).resolve()
        path_relative = path_to_delete.relative_to(Path.cwd())
        log.info(f"Deleting '{path_relative}'")
        path_to_delete.unlink()

    return clean_img_paths


def check_git_status():
    """Check if the working directory is a clean git repo."""
    try:
        repo = Repo(Path.cwd().resolve(), search_parent_directories=True)
        if repo.is_dirty():
            return (False, "Found uncommitted changes")
    except InvalidGitRepositoryError:
        return (False, "Does not appear to be a git repository")
    return (True, "Git repo looks good.")


def validate_config(schema, config, filename, line_number=None):
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
        raise ValidationError(err_msg, v)

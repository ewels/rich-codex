import logging
from glob import glob
from pathlib import Path

log = logging.getLogger("rich-codex")


def clean_images(clean_img_paths_raw, img_obj, codex_obj):
    """Delete any images matching CLEAN_IMG_PATHS that were not generated.

    Useful to remove existing files when a target filename is changed.
    """
    clean_img_patterns = clean_img_paths_raw.splitlines() if clean_img_paths_raw else []

    if len(clean_img_patterns) == 0:
        log.debug("[dim]Nothing found to clean in 'clean_img_paths'")
        return

    # Search glob patterns for images
    all_img_paths = set()
    for pattern in clean_img_patterns:
        all_img_paths |= set(glob(pattern, recursive=True))
    if len(all_img_paths) == 0:
        log.debug("[dim]No files found matching 'clean_img_paths' glob patterns")
        return

    # Collect list of generated images
    known_img_paths = []
    if img_obj:
        known_img_paths.extend(img_obj.img_paths)
    if codex_obj:
        for img in codex_obj.rich_imgs:
            known_img_paths.extend(img.img_paths)

    # Paths found by glob that weren't generated
    clean_img_paths = all_img_paths - set(known_img_paths)
    if len(clean_img_paths) == 0:
        log.debug("[dim]All files found matching 'clean_img_paths' were generated in this run. Nothing to clean.")
        return

    for path in clean_img_paths:
        log.debug(f"Deleting '{path}'")
        Path(path).unlink()

    log.info(f"Deleted {len(clean_img_paths)} images matching 'clean_img_paths' that were unaccounted for 💥")

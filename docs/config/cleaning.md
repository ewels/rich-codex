# Removing images

If you change the output filename of an image, a new file will be created.
However, the old one will remain which is probably not what you intended.

To avoid this rich-codex can "clean" an image path, deleting any matching files that were not generated during a run.

This is done using `--clean-img-paths` / `$CLEAN_IMG_PATHS` / `clean_img_paths` (CLI, env/markdown, action/config). One or more filename glob patterns (separated by newlines) can be given. At the end of the run, all matching files that were not generated will be deleted.

<!-- prettier-ignore-start -->
!!! warning
    Rich-codex will clean _all_ files matching your pattern. Including your source code. Handle with care 🔥
<!-- prettier-ignore-end -->

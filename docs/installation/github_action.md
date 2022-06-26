---
title: GitHub Action
---

Rich-codex was primarily designed to run automatically with GitHub actions, to keep your screenshots up to date for you.

If there are changes to the images, the action can exit with an error (default) or automatically commit the updates.

<!-- prettier-ignore-start -->
!!! info
    For GitHub Actions to push commits to your repository, you'll need to set _Workflow permissions_ to _Read and write permissions_ under _Actions_ -> _General_ in the repo settings. See the [GitHub docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#configuring-the-default-github_token-permissions).
<!-- prettier-ignore-end -->

## Example workflow

This action looks for rich-codex content in the repo. It removes any SVG files found in `docs/img/` that don't match the outputs and generates the updated images. If there have been any changes, it pushes a new commit with the updated images.

```yaml
on: [push]
jobs:
  rich_codex:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repo
        uses: actions/checkout@v3

      - name: Install your custom tools
        run: pip install .

      - name: Generate terminal images with rich-codex
        uses: ewels/rich-codex@v1
        with:
          commit_changes: "true"
          clean_img_paths: docs/img/*.svg
```

For a more complex example, see [`.github/workflows/examples.yml`](https://github.com/ewels/rich-codex/blob/main/.github/workflows/examples.yml) in this repository.

## GitHub Action Inputs

For a description of the action inputs, please see the [configuration overview docs](../config/overview.md).

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

```yaml title=".github/workflows/screenshots.yml" linenums="1"
name: Rich-codex
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

## Triggers

In the above example, the workflow is triggered by the line `on: [push]`.
This means that new screenshots will be generated on every commit.

For some people this may be a little excessive, in which case you might prefer some of the following suggestions.

<!-- prettier-ignore-start -->
!!! warning
    If you have `commit_changes: "true"` set as in the example above, you should only run in environments where pushing a new commit is possible.
    For example, using this in a workflow triggered by a release will fail because the workflow will be running on a detached commit.
<!-- prettier-ignore-end -->

Note that GitHub has [extensive documentation](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow) on the different ways to trigger actions workflows.

<!-- prettier-ignore-start -->
!!! tip
    You can mix and match multiple different triggers!
<!-- prettier-ignore-end -->

### If specific files are edited

If you only want to re-render screenshots if certain files (or filetypes) are edited, you can [filter the `push` event with the `paths` key](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#running-your-workflow-based-on-files-changed-in-a-pull-request-1):

```yaml
on:
  push:
    paths:
      - "**.md"
      - .rich-codex.yml
      - src/myapp/cli-flags.py
```

### Specific branches

You can run on pushes to the `main` and `staging` branches only by using:

```yaml
on:
  push:
    - main
    - staging
```

### Manually running

You can manually run the workflow by [pressing a button in the GitHub website](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow#running-a-workflow). Just use:

```yaml
on: workflow_dispatch
```

### Filtering for commit message

You can filter by commit message by always running on every push, but then using an `if` statement on the job.

For example, we can take the main example above and add the following to only run when the commit message includes the string `[screenshots]`:

```yaml title=".github/workflows/screenshots.yml" linenums="1" hl_lines="5"
name: Rich-codex
on: [push]
jobs:
  rich_codex:
    if: "contains(github.event.head_commit.message, '[screenshots]')"
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

## GitHub Action Inputs

Basically everything that you can configure via the command line interface / config can also be configured within GitHub actions via the `with` key.

For a full description of all available inputs, please see the [configuration overview docs](../config/overview.md).

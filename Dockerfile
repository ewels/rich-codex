##################################################################
#
# NOTE: This image does not contain your custom software!
#
# Screenshots generated from commands will likely not work.
# Create your own Docker image based on this one or use this
# purely for code snippets.
#
##################################################################

FROM python:3.14-alpine

# Git for the repository safety checks. No fonts: rich-codex bundles its own and tells
# the rasteriser to ignore the machine's. build-base is needed because PyYAML and
# rapidfuzz have no musl wheels for this Python and are built from source.
RUN apk add --no-cache git build-base

# Install requirements
COPY . .
RUN pip install "."

# Prepare GitHub Action
ENTRYPOINT ["rich-codex"]

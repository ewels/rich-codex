##################################################################
#
# NOTE: This image does not contain your custom software!
#
# Screenshots generated from commands will likely not work.
# Create your own Docker image based on this one or use this
# purely for code snippets.
#
##################################################################

FROM python:3.10-alpine

# Install Cairo for SVG -> PNG / PDF conversion
# From: https://phauer.com/2018/install-cairo-cairosvg-alpine-docker/
RUN apk add --no-cache \
    git build-base cairo-dev cairo cairo-tools \
    # pillow dependencies
    jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev

# Install requirements
COPY . .
RUN pip install .

# Prepare GitHub Action
ENTRYPOINT ["rich-codex"]

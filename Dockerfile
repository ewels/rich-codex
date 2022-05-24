# Container image that runs your code
FROM python:3.10-alpine

# Install Cairo for SVG -> PNG / PDF conversion
RUN apk add --no-cache \
    build-base cairo-dev cairo cairo-tools \
    # pillow dependencies
    jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev

# Install requirements
COPY . .
RUN pip install .

# Prepare GitHub Action
ENTRYPOINT ["rich-codex"]

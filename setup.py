from setuptools import setup

setup(
    name="rich-codex",
    install_requires=[
        "rich>=12.4.3",
        "rich-click>=1.5",
        "rich-cli",  # For convience only
        "importlib-metadata; python_version < '3.8'",
        "pyyaml",
        "levenshtein>=0.18.1",
        "jsonschema",
        "GitPython",
    ],
    extras_require={
        "cairo": "CairoSVG>=2.5.2",
        "dev": "pre-commit",
    },
)

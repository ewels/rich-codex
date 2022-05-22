from setuptools import setup

setup(
    name="rich-codex",
    install_requires=[
        "rich>=12.4.1",
        "rich-cli>=1.8.0",
        "rich-click>=1.4",
        "importlib-metadata; python_version < '3.8'",
    ],
    extras_require={
        "cairo": "CairoSVG>=2.5.2",
        "dev": "pre-commit",
    },
)

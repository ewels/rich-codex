from setuptools import setup

setup(
    name="rich-codex",
    install_requires=[
        "rich>=12.4.3",
        # "rich-click>=1.5",
        "git+https://github.com/ewels/rich-click@master#egg=rich-click",
        "importlib-metadata; python_version < '3.8'",
    ],
    extras_require={
        "cairo": "CairoSVG>=2.5.2",
        "dev": "pre-commit",
    },
)

from setuptools import setup

requirements = open("requirements.txt").read().splitlines()

setup(
    name="rich-codex",
    install_requires=requirements,
)

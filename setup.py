from setuptools import setup

requirements = open("requirements.txt").read().splitlines()

setup(
    name="rich-img",
    install_requires=requirements,
)

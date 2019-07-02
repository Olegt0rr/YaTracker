#!/usr/bin/env python3
import pathlib
import re
import sys

from setuptools import find_packages, setup

try:
    from pip.req import parse_requirements
except ImportError:  # pip >= 10.0.0
    from pip._internal.req import parse_requirements

WORK_DIR = pathlib.Path(__file__).parent

# Check python version
MINIMAL_PY_VERSION = (3, 7)
if sys.version_info < MINIMAL_PY_VERSION:
    raise RuntimeError(
        "YaTracker works with Python {}+ only".format(".".join(map(str, MINIMAL_PY_VERSION)))
    )


def get_version():
    """
    Read version

    :return: str
    """
    txt = (WORK_DIR / "yatracker" / "__init__.py").read_text("utf-8")
    try:
        return re.findall(r"^__version__ = '([^']+)'\r?$", txt, re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")


def get_description():
    """
    Read full description from 'README.md'

    :return: description
    :rtype: str
    """
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


def get_requirements(filename=None):
    """
    Read requirements from 'requirements txt'

    :return: requirements
    :rtype: list
    """
    if filename is None:
        filename = "requirements.txt"

    file = WORK_DIR / filename

    install_reqs = parse_requirements(str(file), session="hack")
    return [str(ir.req) for ir in install_reqs]


setup(
    name="yatracker",
    version=get_version(),
    packages=find_packages(exclude=("tests", "tests.*", "examples.*")),
    url="https://github.com/Olegt0rr/YaTracker",
    license="MIT",
    author="Oleg A.",
    requires_python=">=3.7",
    author_email="oleg@trueweb.app",
    description="Fully asynchronous library for Yandex Tracker",
    long_description=get_description(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    install_requires=get_requirements(),
    package_data={"": ["requirements.txt"]},
    include_package_data=False,
)

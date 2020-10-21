from pathlib import Path

from setuptools import find_packages, setup

# The directory containing this file
HERE = Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


def get_version(relpath: str):
    try:
        for line in (HERE / relpath / "__init__.py").read_text().splitlines():
            if line.startswith("__version__"):
                return line.split('"')[1]
    except (OSError, IndexError):
        pass
    raise RuntimeError("Unable to find version string.")


setup(
    name="github_action_template",
    version=get_version("github_action_template"),
    description="A light template and boilerplate generator for GitHub actions written in Python 3.8+",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Talentia-Software/OSS-github-action-python-template",
    author="Talentia Software",
    author_email="grams@talentia-software.com",
    license="BSD-3-Clause",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Version Control :: Git",
        ],
    packages=find_packages(exclude=("tests",)),
    python_requires='>=3.8',
    install_requires=["github3.py>=1.3.0"],
    entry_points={
        'console_scripts': ['action-entrypoint=github_action_template.entrypoint:main'],
        }
    )

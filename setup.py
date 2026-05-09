"""Compatibility setup.py.

Used by older pip/setuptools that don't fully support pyproject.toml.
Reads configuration from pyproject.toml via setuptools.
"""
from setuptools import find_packages, setup

setup(
    name="quick_md5check",
    version="1.0.0",
    description="Multi-threaded MD5 checksum generator and verifier",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.8",
    author="lg10is1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    project_urls={
        "Homepage": "https://github.com/lg10is1/quick_md5check",
        "Repository": "https://github.com/lg10is1/quick_md5check",
        "Bug Tracker": "https://github.com/lg10is1/quick_md5check/issues",
    },
    install_requires=["tqdm>=4.60.0"],
    entry_points={
        "console_scripts": [
            "md5check=md5check.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Security :: Cryptography",
    ],
)

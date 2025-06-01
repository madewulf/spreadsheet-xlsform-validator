import os
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements-core.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="django-xlsform-validator",
    version="0.1.0",
    author="Martin De Wulf",
    author_email="mdewulf@bluesquarehub.com",
    description="A Django app for validating spreadsheet data against XLSForm specifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/madewulf/spreadsheet-xlsform-validator",
    project_urls={
        "Bug Tracker": "https://github.com/madewulf/spreadsheet-xlsform-validator/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
    ],
    packages=find_packages(exclude=["xlsform_validator*", "tests"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=requirements,
)

from setuptools import setup, find_packages

__title__ = 'chatgmail'
__version__ = '0.0.1'
__author__ = 'Lee Shiueh'
__email__ = 'lee.shiueh@gmail.com'


def read_files(files):
    data = []
    for file in files:
        with open(file, encoding='utf-8') as f:
            data.append(f.read())
    return "\n".join(data)


long_description = read_files(['README.md'])

with open('requirements.txt') as f:
    install_requires = f.read().split('\n')

setup(
    name=__title__,
    version=__version__,
    description="A Python CLI tool to interact with Gmail and GPT.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    url="https://github.com/slee124565",
    author=__author__,
    author_email=__email__,
    license="MIT",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=install_requires,
    python_requires='>=3.11',
    entry_points={
        "console_scripts": [
            "chatgmail=chatgmail.cli:chatgmailcli",
        ],
    },
)
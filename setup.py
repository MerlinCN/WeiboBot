import setuptools

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="WeiboBot",
    version="0.3.5",
    author="Merlin",
    author_email="merlin@merlinblog.cn",
    description="基于微博H5 API开发的机器人框架",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MerlinCN/WeiboBot",
    packages=setuptools.find_packages(),
    install_requires=["requests", "tinydb"],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

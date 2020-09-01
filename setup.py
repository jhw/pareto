"""
- https://stackoverflow.com/questions/50585246/pip-install-creates-only-the-dist-info-not-the-package
- https://stackoverflow.com/questions/32688688/how-to-write-setup-py-to-include-a-git-repo-as-a-dependency
- https://stackoverflow.com/questions/1612733/including-non-python-files-with-setup-py
"""

import os, setuptools

with open("README.md", "r") as fh:
    long_description=fh.read()

"""
- because setuptools.find_packages() is useless and broken
"""

def filter_packages(root):
    def filter_packages(root, packages):
        packages.append(root.replace("/", "."))
        for path in os.listdir(root):
            if path=="__pycache__":
                continue
            newpath="%s/%s" % (root, path)
            if os.path.isdir(newpath):
                filter_packages(newpath, packages)
    packages=[]
    filter_packages(root, packages)
    return packages

def filter_pip_dependencies(root="requirements.txt"):
    return [row for row in open(root).read().split("\n")
            if (row!='' and
                not row.startswith("git+"))]

setuptools.setup(
    name="pareto",
    version="1.1.5",
    author="jhw",
    author_email="justin.worrall@gmail.com",
    description="OTP for serverless",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhw/pareto",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=filter_packages("pareto"),
    install_requires=filter_pip_dependencies()
)


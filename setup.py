import setuptools

with open("README.md", "r") as fh:
    long_description=fh.read()

setuptools.setup(
    name="pareto",
    version="1.0.3",
    author="jhw",
    author_email="justin.worrall@gmail.com",
    description="OTP for serverless",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhw/pareto",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=['setuptools_scm'],
    install_requires=["awscli",
                      "botocore",
                      "boto3",
                      "gitpython",
                      "jsonschema",
                      "git+https://github.com/spulec/moto",
                      "pandas",
                      "pareto",
                      "requests",
                      "ruamel.yaml"]
    include_package_data=True

)


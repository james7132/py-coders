import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name="py-coders",
    version="1.0.0",
    author="James Liu",
    author_email="contact@jamessliu.com",
    description="A simple set of symmetric encoder/decoder classes for serializing to and from bytearrays.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/james7132/py-coders",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

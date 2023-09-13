from setuptools import find_packages, setup

setup(
    name="MuseBSL",
    version="0.1",
    description="Python package for streaming, recording, and visualizing data from the Muse EEG headset using the Brain Streaming Layer (BSL).",
    author="Dominique Makowski",
    author_email="D.Makowski@sussex.ac.uk",
    license="MIT",
    url="https://github.com/DominiqueMakowski/MuseBSL",
    entry_points={"console_scripts": ["MuseBSL=MuseBSL.__main__:main"]},
    install_requires=[
        "bleak",  # Bluetooth backend
        "bsl",  # Brain Streaming Layer (replaces lsl)
    ],
    packages=find_packages(),
)

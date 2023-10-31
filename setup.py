from setuptools import find_packages, setup

setup(
    name="MuseLSL2",
    version="0.2",
    description="Python package for streaming, recording, and visualizing data from the Muse EEG headset using mne-lsl (an updated implementation of LSL).",
    author="Dominique Makowski",
    author_email="D.Makowski@sussex.ac.uk",
    license="MIT",
    url="https://github.com/DominiqueMakowski/MuseLSL2",
    entry_points={"console_scripts": ["MuseLSL2=MuseLSL2.__main__:main"]},
    install_requires=[
        "numpy",
        "matplotlib",
        "mne_lsl",  # Replaces lsl
        "bleak",  # Bluetooth backend
        "bitstring",  # For decoding Muse packets
        "vispy",  # Visualization
        "PyQt6",  # Visualization
    ],
    dependency_links=[
        "https://github.com/mne-tools/mne-lsl/zipball/main",
    ],
    packages=find_packages(),
)

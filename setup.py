from setuptools import find_packages, setup

setup(
    name="MuseLSL2",
    version="0.2",
    description="Python package for streaming, recording, and visualizing data from the Muse EEG headset using mne-lsl (an updated implementation of LSL).",
    author="Dominique Makowski",
    author_email="D.Makowski@sussex.ac.uk",
    license="MIT",
    url="https://github.com/DominiqueMakowski/MuseLSL2",
    python_requires=">=3.9",
    entry_points={"console_scripts": ["MuseLSL2=MuseLSL2.__main__:main"]},
    packages=find_packages(),
    install_requires=[
        "numpy>=2.3.3",
        "matplotlib>=3.10.6",
        "mne-lsl",  # PyPI package name; import remains mne_lsl
        "bleak>=1.1.1",  # Bluetooth backend
        "bitstring>=4.3.1",  # For decoding Muse packets
        "vispy>=0.15.2",  # Visualization
        "PyQt6>=6.9.1",  # Visualization backend for VisPy
    ],
    extras_require={
        "data": [
            "pyxdf>=1.17.0",  # XDF loading utilities used by load_data.py
            "neurokit2>=0.2.12",  # Optional biosignal processing helpers
        ]
    },
)

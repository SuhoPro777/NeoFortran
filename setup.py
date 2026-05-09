from setuptools import setup, find_packages
setup(
    name="neofortran", version="1.0.0",
    description="NeoFortran — Modern Scientific Programming Language",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={"console_scripts": ["neofortran=neofortran.cli:main"]},
)

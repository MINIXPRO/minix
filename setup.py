from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in minix/__init__.py
from minix import __version__ as version

setup(
	name="minix",
	version=version,
	description="Meril",
	author="Meril",
	author_email="Nikhil.Pardesi@microcrispr.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

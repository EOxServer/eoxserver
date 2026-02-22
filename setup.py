from setuptools import setup
import subprocess


with open('requirements.txt', 'r', encoding="utf-8") as reqs:
    install_requires = [
        requirement.strip() for requirement in reqs
    ]

try:
    gdal_version = subprocess.check_output(
        ['gdal-config', '--version']
    ).decode('utf-8').strip()
except FileNotFoundError:
    gdal_version = subprocess.check_output(
        ['gdalinfo', '--version']
    ).decode('utf-8').split(' ')[1].strip(',')

install_requires.append(f'gdal=={gdal_version}')

if __name__ == "__main__":
    setup(install_requires=install_requires)

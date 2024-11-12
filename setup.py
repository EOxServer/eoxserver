from setuptools import setup
import subprocess
import pkg_resources


with open('requirements.txt', 'r') as reqs:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(reqs)
    ]

try:
    gdal_version = subprocess.check_output(['gdal-config','--version']).decode('utf-8').strip()
except FileNotFoundError:
    gdal_version = subprocess.check_output(['gdalinfo','--version']).decode('utf-8').split(' ')[1].strip(',')

install_requires.append(f'gdal=={gdal_version}')

if __name__ == "__main__":
    setup(install_requires=install_requires)

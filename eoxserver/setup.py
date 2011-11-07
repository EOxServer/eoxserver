#from setuptools import setup, find_packages

from distutils.core import setup
setup(
    name = 'EOxServer',
    version = '1.0',
    scripts = ["scripts/eoxserver-admin.py"],
    #packages = find_packages(),  # include all packages under src
    #package_dir = {'':'src'},   # tell distutils packages are under src
)

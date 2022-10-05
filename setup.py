# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import os
from setuptools import setup

# get version number
# from https://github.com/mapbox/rasterio/blob/master/setup.py#L55
init_py = os.path.join(os.path.dirname(__file__), 'eoxserver/__init__.py')
with open(init_py) as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            break


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


packages, data_files = [], []
for dirpath, dirnames, filenames in os.walk('eoxserver'):
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append(
            [dirpath, [os.path.join(dirpath, f) for f in filenames]]
        )


# On readthecods.org we don't want the reftools to be build
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if on_rtd:
    ext_modules = []

setup(
    name='EOxServer',
    version=version.replace(' ', '-'),
    packages=packages,
    data_files=data_files,
    include_package_data=True,
    scripts=[
        "eoxserver/scripts/eoxserver-admin.py",
        "eoxserver/scripts/eoxserver-instance.py",
        "tools/eoxserver-atpd.py",
        "tools/eoxserver-validate_xml.py",
        "tools/eoxserver-preprocess.py"
    ],
    install_requires=[
        'django<4',
        'python-dateutil',
        'django-model-utils<5.0.0',
        'zipstream',
        'psycopg2',
        'lxml',
        'pycql==0.0.8',
        'matplotlib',
        'pyows>=0.2.6',
        'jsonfield',
    ],
    extras_require={
        'dev': ['scipy'],
        ':python_version == "2.7"': ['futures']
    },
    zip_safe=False,

    # Metadata
    author="EOX IT Services GmbH",
    author_email="office@eox.at",
    maintainer="EOX IT Services GmbH",
    maintainer_email="packages@eox.at",

    description="EOxServer is a server for Earth Observation (EO) data",
    long_description=read("README.rst"),

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Other Audience',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Visualization',
    ],

    license="EOxServer Open License (MIT-style)",
    keywords="Earth Observation, EO, OGC, WCS, WMS",
    url="http://eoxserver.org/"
)

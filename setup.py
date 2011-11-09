import os

# Hack to remove setuptools "feature" which resulted in
# ignoring MANIFEST.in when code is in an svn repository.
# TODO find a nicer solution
from setuptools.command import sdist
del sdist.finders[:]

from setuptools import setup
from eoxserver import get_version

version = get_version()

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
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name='EOxServer',
    version=version.replace(' ', '-'),
    packages=packages,
    data_files=data_files,
    scripts=["eoxserver/scripts/eoxserver-admin.py"],
    
    install_requires=[
        'django>=1.3',
        'pysqlite>=2.5',
    ],
    
    # Metadata
    author="EOX IT Services GmbH",
    author_email="office@eox.at",
    
    description="",
    long_description="",
    
    classifiers=[
          'Development Status :: 3 - Alpha',
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
    keywords="Earth Observation",
    url="http://eoxserver.org/"
)

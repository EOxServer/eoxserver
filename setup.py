import os
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
    packages=packages,#find_packages("eoxserver"),
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
    
    classifiers=[ #TODO
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Communications :: Email',
          'Topic :: Office/Business',
          'Topic :: Software Development :: Bug Tracking',
    ],
    
    #package_dir={"eoxserver": "eoxserver"},
    
    license="MIT",
    keywords="Earth Observation",
    url="http://www.eoxserver.org/"
)

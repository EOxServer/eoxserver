#!/bin/sh -e

# Update all the installed packages
yum update -y

# Install packages
yum install -y gdal-eox gdal-eox-python postgis proj-epsg python-werkzeug \
               python-lxml mod_wsgi httpd postgresql-server \
               pytz python-dateutil libxml2 libxml2-python mapserver \
               mapserver-python python-pysqlite-eox unzip libspatialite

# Install some build dependencies
yum install -y gcc make gcc-c++ kernel-devel-`uname -r` zlib-devel \
               openssl-devel readline-devel perl wget httpd-devel pixman-devel \
               sqlite-devel libpng-devel libjpeg-devel libcurl-devel cmake \
               geos-devel fcgi-devel gdal-eox-devel python-devel \
               gdal-eox-driver-envisat gdal-eox-driver-netcdf \
               gdal-eox-driver-openjpeg2 libffi-devel

# Attention: Make sure to not install EOxServer from rpm packages!
# See development_installation.sh for installation.


# Install recent version of pip
yum install -y python-pip
pip install --upgrade pip

# Install pyOpenSSL to prevent urllib3 InsecurePlatformWarning
pip install pyopenssl ndg-httpsclient pyasn1

# Install recent version of Django (1.6, since 1.7+ requires Python 2.7)
pip install "django>=1.11,<1.12a0" --no-binary django --force-reinstall --upgrade
pip install django-extensions psycopg2 django-model-utils s2reader

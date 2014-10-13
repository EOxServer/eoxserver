#!/bin/sh -e

# Update all the installed packages
yum update -y

# Install packages
yum install -y gdal-eox gdal-eox-python postgis Django14 proj-epsg \
               python-django-extensions python-werkzeug
yum install -y python-lxml mod_wsgi httpd postgresql-server python-psycopg2 pytz
yum install -y libxml2 libxml2-python mapserver mapserver-python python-pysqlite-eox

# Install some build dependencies
yum install -y gcc make gcc-c++ kernel-devel-`uname -r` zlib-devel \
               openssl-devel readline-devel perl wget httpd-devel pixman-devel \
               sqlite-devel libpng-devel libjpeg-devel libcurl-devel cmake \
               geos-devel fcgi-devel gdal-eox-devel python-devel \
               gdal-eox-driver-envisat gdal-eox-driver-netcdf \
               gdal-eox-driver-openjpeg2

# Attention: Make sure to not install EOxServer from rpm packages!
# See development_installation.sh for installation.

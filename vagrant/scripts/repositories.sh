#!/bin/sh

# Install the EPEL repository
yum install -y http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

# Install the ELGIS repository
yum install -y http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-ELGIS

# Install the EOX repository
yum install -y http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
rpm --import /etc/pki/rpm-gpg/eox-package-maintainers.gpg
# Make sure only the stable repository is enabled
sed -e 's/^enabled=1/enabled=0/' -i /etc/yum.repos.d/eox-testing.repo

# Ignore TU Vienna CentOS mirror
sed -e 's/^#exclude=.*/exclude=gd.tuwien.ac.at/' /etc/yum/pluginconf.d/fastestmirror.conf > /etc/yum/pluginconf.d/fastestmirror.conf

# Set includepkgs in EOX Stable
if ! grep -Fxq "includepkgs=mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1 gdal-eox gdal-eox-devel gdal-eox-driver-envisat gdal-eox-driver-netcdf gdal-eox-driver-openjpeg2 gdal-eox-java gdal-eox-libs gdal-eox-python openjpeg2 python-pysqlite-eox" /etc/yum.repos.d/eox.repo ; then
    sed -e 's/^\[eox\]$/&\nincludepkgs=mapserver mapserver-python mapcache libxml2 libxml2-python libxerces-c-3_1 gdal-eox gdal-eox-devel gdal-eox-driver-envisat gdal-eox-driver-netcdf gdal-eox-driver-openjpeg2 gdal-eox-java gdal-eox-libs gdal-eox-python openjpeg2 python-pysqlite-eox/' -i /etc/yum.repos.d/eox.repo
fi

# Set exclude in CentOS-Base
if ! grep -Fxq "exclude=libxml2 libxml2-python" /etc/yum.repos.d/CentOS-Base.repo ; then
    sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
    sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
fi

# Disabled to be fully compatible with build environment
# Install Continuous Release (CR) repository
#yum install -y centos-release-cr

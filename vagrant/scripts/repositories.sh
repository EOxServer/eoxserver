#!/bin/sh

# Install the EPEL repository
if ! rpm -q --quiet epel-release ; then
    yum install -y epel-release
    rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
fi

# Install the ELGIS repository
if ! rpm -q --quiet elgis-release ; then
    yum install -y http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
    rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-ELGIS
fi

# Install the EOX repository
if ! rpm -q --quiet eox-release ; then
    yum install -y http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
else
    yum reinstall -y http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm
fi
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
if ! grep -Fxq "exclude=libxml2 libxml2-python libxerces-c-3_1" /etc/yum.repos.d/CentOS-Base.repo ; then
    sed -e 's/^\[base\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
    sed -e 's/^\[updates\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-Base.repo
fi

# Install Continuous Release (CR) repository
if ! rpm -q --quiet centos-release-cr ; then
    yum install -y centos-release-cr
    # Set exclude in CentOS-CR
    if ! grep -Fxq "exclude=libxml2 libxml2-python libxerces-c-3_1" /etc/yum.repos.d/CentOS-CR.repo ; then
        sed -e 's/^\[cr\]$/&\nexclude=libxml2 libxml2-python libxerces-c-3_1/' -i /etc/yum.repos.d/CentOS-CR.repo
    fi
fi

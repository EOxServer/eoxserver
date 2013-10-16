#!/bin/sh 
#-----------------------------------------------------------------------
#
# Description: 
#
#   Automatic installation and configuration on CentOS 
#   (applicable also to RHEL and its clones). 
#
#   The script install the EOxServer RPMs and setups the database templates 
#   and system users. 
#
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

set -x 
set -e 

#-------------------------------------------------------------------------------

HTTPUSER="apache"
INSTUSER="eoxserver"
INSTROOT="/srv/${INSTUSER}"
#DATAUSER="eodata"
#DATAROOT="/srv/${DATAUSER}"
PG_HBA="/var/lib/pgsql/data/pg_hba.conf"

#-------------------------------------------------------------------------------
# 1 installation 

rpm -q --quiet elgis-release || rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
rpm -q --quiet epel-release || rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
rpm -q --quiet eox-release || rpm -Uvh http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm

# uncomment for unstable releases  
#ex /etc/yum.repos.d/eox-testing.repo <<END
#1,\$g/enabled/s/0/1/g
#wq
#END

yum clean all

yum --assumeyes install EOxServer httpd mod_wsgi postgresql postgresql-server postgis python-psycopg2

#-------------------------------------------------------------------------------
# 1 HTTPD setup part 1 

chkconfig httpd on
service httpd start

# NOTE: Firewall setup should be excluded from the EOxServer Instance RPM!
iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT

service iptables save

#-------------------------------------------------------------------------------
# 2 DB setup part 1 

service postgresql initdb
chkconfig postgresql on
service postgresql start

sudo -u postgres createdb template_postgis
sudo -u postgres createlang plpgsql template_postgis
PG_SHARE=/usr/share/pgsql
sudo -u postgres psql -q -d template_postgis -f $PG_SHARE/contrib/postgis.sql
sudo -u postgres psql -q -d template_postgis -f $PG_SHARE/contrib/spatial_ref_sys.sql
sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"

#-------------------------------------------------------------------------------
# 3 create users 

# create users 
useradd -r -m -g "$HTTPUSER" -d "$INSTROOT" -c "EOxServer's administrator" "$INSTUSER"
#useradd -r -m -g "$HTTPUSER" -d "$DATAROOT" -c "EO data provider" "$DATAUSER"

#make the users directories world readable  

chmod a+rx "$INSTROOT"
#chmod a+rx "$DATAROOT"


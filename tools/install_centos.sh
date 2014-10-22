#!/bin/sh 
#-----------------------------------------------------------------------
#
# Description: 
#
#   Automatic installation on CentOS (applicable also to RHEL and its clones). 
#
#   The script install the EOxServer RPMs and setups and configures 
#   EOxServer instance.
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
# if not set the default HOSTNAME is used  

#HOSTNAME=<fill-your-hostname-or-IP-here>
INSTANCE="instance00"

HTTPUSER="apache"
INSTUSER="eoxserver"
INSTROOT="/srv/${INSTUSER}"
DATAUSER="eodata"
DATAROOT="/srv/${DATAUSER}"
SETTINGS="${INSTROOT}/${INSTANCE}/${INSTANCE}/settings.py"
INSTLOG="${INSTROOT}/${INSTANCE}/${INSTANCE}/logs/eoxserver.log"
INSTSTAT_URL="/${INSTANCE}_static" # DO NOT USE THE TRAILING SLASH!!!
INSTSTAT_DIR="${INSTROOT}/${INSTANCE}/${INSTANCE}/static"
WSGI="${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
EOXSCONF="${INSTROOT}/${INSTANCE}/${INSTANCE}/conf/eoxserver.conf"
DBENGINE="django.contrib.gis.db.backends.postgis"
DBNAME="eoxs_${INSTANCE}"
DBUSER="eoxs_admin_${INSTANCE}"
DBPASSWD="${INSTANCE}_admin_eoxs"
DBHOST=""
DBPORT=""
PG_HBA="/var/lib/pgsql/data/pg_hba.conf"
MNGCMD="${INSTROOT}/${INSTANCE}/manage.py"
SOCKET_PREFIX="run/wsgi"

#-------------------------------------------------------------------------------

if [ -z "$HOSTNAME" ] 
then 
    echo "Set the HOSTNAME variable!" 1>&1 
    exit 1 
fi 

#-------------------------------------------------------------------------------
# 1 installation 

rpm -q --quiet elgis-release || rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
rpm -q --quiet epel-release || yum install epel-release
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
useradd -r -m -g "$HTTPUSER" -d "$DATAROOT" -c "EO data provider" "$DATAUSER"

#make the users directories world readable  

chmod a+rx "$INSTROOT"
chmod a+rx "$DATAROOT"

#-------------------------------------------------------------------------------
# 4 create instance 

# ver.: 0.2
#sudo -u eoxserver eoxserver-admin.py create_instance "$INSTANCE" -d "$INSTROOT" 

# ver.: 0.3
sudo -u eoxserver mkdir -p "$INSTROOT/$INSTANCE"
sudo -u eoxserver eoxserver-admin.py create_instance "$INSTANCE" "$INSTROOT/$INSTANCE" 

#-------------------------------------------------------------------------------
# 5 DB setup part 2 

# 5.1 - create DB 
sudo -u postgres psql -q -c "CREATE USER $DBUSER WITH ENCRYPTED PASSWORD '$DBPASSWD' NOSUPERUSER NOCREATEDB NOCREATEROLE ;"
sudo -u postgres psql -q -c "CREATE DATABASE $DBNAME WITH OWNER $DBUSER TEMPLATE template_postgis ENCODING 'UTF-8' ;"

# prepend to the beginning of the acess list 
sudo -u postgres ex "$PG_HBA" <<END 
/#[	 ]*TYPE[	 ]*DATABASE[	 ]*USER[	 ]*CIDR-ADDRESS[	 ]*METHOD/a

# EOxServer instance: $INSTROOT/$INSTANCE
local	$DBNAME	$DBUSER	md5
local	$DBNAME	all	reject
.
wq
END

# you must restart the service 
service postgresql restart

# 4.2 DJango datadase backend 

sudo -u eoxserver ex "$SETTINGS" <<END
1,\$s/\('ENGINE'[	 ]*:[	 ]*'\).*\('[	 ]*,\)/\1$DBENGINE\2/
1,\$s/\('NAME'[	 ]*:[	 ]*'\).*\('[	 ]*,\)/\1$DBNAME\2/
1,\$s/\('USER'[	 ]*:[	 ]*'\).*\('[	 ]*,\)/\1$DBUSER\2/
1,\$s/\('PASSWORD'[	 ]*:[	 ]*'\).*\('[	 ]*,\)/\1$DBPASSWD\2/
1,\$s/\('HOST'[	 ]*:[	 ]*'\).*\('[	 ]*,\)/#\1$DBHOST\2/
1,\$s/\('PORT'[	 ]*:[	 ]*'\).*\('[	 ]*,\)/#\1$DBPORT\2/
1,\$s:\(STATIC_URL[	 ]*=[	 ]*'\).*\('.*\):\1$INSTSTAT_URL/\2:
wq
END

# 5.3 django syncdb (without interactive prompts) 

sudo -u eoxserver python $MNGCMD syncdb --noinput 

#TODO: django admin user account creation 
#sudo -u eoxserver python $MNGCMD createsuperuser

#-------------------------------------------------------------------------------
# 6 HTTPD setup part 2

## 6.1 set path to settings in WSGI module 
## not necessary for 0.3 relase 
#sudo -u eoxserver ex "$WSGI" <<END
#/^import os/a  
#import sys 


#path = "${INSTROOT}/${INSTANCE}"
#if path not in sys.path:
#    sys.path.append(path)

#.
#wq
#END

# ... not needed anymore 


# 6.2 collect statics 
sudo -u eoxserver python $MNGCMD collectstatic -l --noinput

# 6.3 allow access to log-file 
chmod g+w "$INSTLOG"

# 6.x apache configuration 

# locate proper configuration file 

CONFS="/etc/httpd/conf/httpd.conf /etc/httpd/conf.d/*.conf"
CONF_DEFAULT="/etc/httpd/conf.d/00_default_site.conf"
CONF=

for F in $CONFS 
do
    if [ 0 -lt `grep -c '^[ 	]*<VirtualHost[ 	]*\*:80>' $F` ] 
    then 
        CONF=$F
        break 
    fi
done

#if the virtual host is not present - create one 

if [ -z "$CONF" ]
then
    CONF="$CONF_DEFAULT"
    echo "Default virtual host not located creting own one in: $CONF" 
    cat >"$CONF" <<END
# default site generated by the automatic EOxServer instance configuration 
<VirtualHost *:80>
</VirtualHost>
END
else
    echo "Default virtual host located in: $CONF" 
fi

# insert the configuration to the virtual host 

ex "$CONF" <<END
/^[ 	]*<VirtualHost[ 	]*\*:80>/a

    # EOxServer instance configured by the automatic installation script

    WSGIDaemonProcess ows processes=10 threads=1

    Alias /$INSTANCE "${INSTROOT}/${INSTANCE}/${INSTANCE}/wsgi.py"
    <Directory "${INSTROOT}/${INSTANCE}/${INSTANCE}">
            Options +ExecCGI -MultiViews +FollowSymLinks
            AddHandler wsgi-script .py
            WSGIProcessGroup ows
            AllowOverride None
            Order Allow,Deny
            Allow from all
    </Directory>

    # static content 
    Alias $INSTSTAT_URL "$INSTSTAT_DIR"
    <Directory "$INSTSTAT_DIR">
            Options -MultiViews +FollowSymLinks
            AllowOverride None
            Order Allow,Deny
            Allow from all
    </Directory>
.
wq
END

# set the daemon socket to a readable location 

CONF=
for F in $CONFS 
do
    if [ 0 -lt `grep -c '^[ 	]*WSGISocketPrefix' $F` ] 
    then 
        CONF=$F
        break 
    fi
done

if [ -z "$CONF" ] 
then # set socket prefix if not already set
    echo "WSGISocketPrefix $SOCKET_PREFIX" >> /etc/httpd/conf.d/wsgi.conf 
fi

# set the service url 
sudo -u eoxserver ex "$EOXSCONF" <<END
/^[	 ]*http_service_url[	 ]*=/s;\(^[	 ]*http_service_url[	 ]*=\).*;\1http://${HOSTNAME}/${INSTANCE}/ows;
wq
END

# restart apache  

service httpd restart

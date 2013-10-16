#!/bin/sh 
#-----------------------------------------------------------------------
#
# Description: 
#
#   Automatic installation and configuration on CentOS 
#   (applicable also to RHEL and its clones). 
#
#   The script creates and configures EOxServer instance. 
#   set the instance name as the first argument. 
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
INSTANCE=${1:-"instance00"}

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
    echo "Set the HOSTNAME variable!" 1>&2
    exit 1 
fi 

#-------------------------------------------------------------------------------
# 4 create instance 

if [ -d "$INSTROOT/$INSTANCE" ]
then
    echo "Instance directory: $INSTROOT/$INSTANCE" 1>&2
    echo "Instance directory exists! The instance seems to exists already." 1>&2
    exit 1 
fi

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

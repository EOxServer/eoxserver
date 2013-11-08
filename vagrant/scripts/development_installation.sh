#!/bin/sh -e

# EOxServer
cd /var/eoxserver/
python setup.py develop

# Configure EOxServer autotest instance
cd /var/eoxserver/autotest/

# Prepare DBs
python manage.py syncdb --noinput --traceback
python manage.py loaddata auth_data.json initial_rangetypes.json --traceback

# Create admin user
TMPFILE=`mktemp`
cat << EOF > "$TMPFILE"
#!/usr/bin/env python
from os import environ
import sys

path = "/var/eoxserver/autotest"
if path not in sys.path:
    sys.path.insert(0,path)
environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotest.settings')

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

user = authenticate(username='admin', password='admin')
if user is None:
    user = User.objects.create_user('admin', 'office@eox.at', 'admin')
EOF
if [ -f $TMPFILE ] ; then
    chmod +rx $TMPFILE
    "$TMPFILE"
    rm "$TMPFILE"
else
    echo "Script to add admin user not found."
fi

# Collect static files
python manage.py collectstatic --noinput

# Create runtime files
touch /var/eoxserver/autotest/autotest/logs/eoxserver.log

# Load the demonstration if not already present
if python manage.py eoxs_check_id -a MER_FRS_1P_RGB_reduced --traceback ; then
    python manage.py eoxs_add_dataset_series -i MER_FRS_1P_RGB_reduced --traceback
    python manage.py eoxs_register_dataset -d /var/eoxserver/autotest/autotest/data/meris/mosaic_MER_FRS_1P_RGB_reduced/*.tif -r RGB --dataset-series MER_FRS_1P_RGB_reduced --traceback
fi

# Add CRS 900913 if not present
if ! grep -Fxq "<900913> +proj=tmerc +lat_0=0 +lon_0=21 +k=1 +x_0=21500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs  <>" /usr/share/proj/epsg ; then
    echo "# WGS 84 / Pseudo-Mercator" >> /usr/share/proj/epsg
    echo "<900913> +proj=tmerc +lat_0=0 +lon_0=21 +k=1 +x_0=21500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs  <>" >> /usr/share/proj/epsg
fi

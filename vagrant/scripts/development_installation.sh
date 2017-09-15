#!/bin/sh -e

# allow a custom EOxServer location to override the default one if needed
export EOX_ROOT=${1:-"/var/eoxserver"}

# Locate sudo (when available) for commands requiring the superuser.
# Allows setup of a custom autoconf instance located in the non-root user-space.
SUDO=`which sudo`

# Add CRS 900913 if not present
if ! grep -Fxq "<900913> +proj=tmerc +lat_0=0 +lon_0=21 +k=1 +x_0=21500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs  <>" /usr/share/proj/epsg ; then
    $SUDO sh -c 'echo "# WGS 84 / Pseudo-Mercator" >> /usr/share/proj/epsg'
    $SUDO sh -c 'echo "<900913> +proj=tmerc +lat_0=0 +lon_0=21 +k=1 +x_0=21500000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs  <>" >> /usr/share/proj/epsg'
fi

# Install EOxServer in development mode ignoring dependencies which are
# already installed
cd "$EOX_ROOT/"
$SUDO pip install -e .

# Initialize SpatiaLite database if not already present
if [ ! -e "$EOX_ROOT/autotest/autotest/data/config.sqlite" ] ; then
    $EOX_ROOT/vagrant/scripts/spatialite.py
fi

# Configure EOxServer autotest instance
cd "$EOX_ROOT/autotest/"

# Prepare DBs
python manage.py migrate --noinput --traceback

# Create admin user
python manage.py shell 1>/dev/null 2>&1 -c "
from django.contrib.auth import models
models.User.objects.create_superuser('admin', 'office@eox.at', 'admin')
"

# Collect static files
python manage.py collectstatic --noinput

# Create runtime files
touch "$EOX_ROOT/autotest/autotest/logs/eoxserver.log"

# Load the demonstration if not already present
COLLECTION="MER_FRS_1P_reduced_RGB"
if python manage.py id check "$COLLECTION" --type Collection --traceback  ; then
    python manage.py coveragetype import "$EOX_ROOT/autotest/autotest/data/meris/meris_range_type_definition.json"
    python manage.py collection create "$COLLECTION" --traceback
    for TIF in "$EOX_ROOT/autotest/autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/"*.tif
    do
        PROD_ID="$(basename ${TIF}).product"
        python manage.py product register -i "$PROD_ID" --metadata "${TIF//.tif/.xml}" --traceback
        python manage.py browse register "$PROD_ID" "$TIF"
        python manage.py coverage register -d "$TIF" -m "${TIF//.tif/.xml}" --product "$PROD_ID" -t MERIS_uint16 --traceback
        python manage.py collection insert "$COLLECTION" "$PROD_ID" --traceback
    done
fi

#!/bin/sh -xe

OS=`facter operatingsystem`

# Create the virtual environment if it does not exist
cd "$WORKSPACE"
if [ -d ".venv" ]; then
    echo "**> virtualenv exists!"
else
    echo "**> creating virtualenv..."
    virtualenv --system-site-packages .venv
fi

# activate the virtual environment
source .venv/bin/activate

# Install the required Django version
case $DJANGO in
    "django1.4")
        echo "Using latest django 1.4"
        pip install "django<1.5,>=1.4"
        ;;
    "django1.5")
        echo "Using latest django 1.5"
        pip install "django<1.6,>=1.5"
        ;;
    *)
        echo "Unknown django version, Exiting..."
        exit 1
        ;;
esac

# Install EOxServer
echo "**> installing eoxserver..."
if [ $OS == "Ubuntu" ]; then
    python setup.py develop --disable-extended-reftools
else
    python setup.py develop
fi

# Create the EOxServer instance
echo "**> creating autotest instance..."
mv autotest tmp1
eoxserver-admin.py create_instance autotest --init_spatialite
cp -R tmp1/autotest/data/ autotest/autotest/
cp -R tmp1/autotest/expected/ autotest/autotest/
cp tmp1/autotest/conf/template.map autotest/autotest/conf/template.map
mkdir -p autotest/autotest/responses/
rm -r tmp1

sed -e 's/pdp_type=none/pdp_type=dummypdp/' -i autotest/autotest/conf/eoxserver.conf
sed -e 's/allowed_actions=/allowed_actions=Add,Delete/' -i autotest/autotest/conf/eoxserver.conf
sed -e 's/# cache_dir=\/tmp/cache_dir=\/tmp/' -i autotest/autotest/conf/eoxserver.conf

if [ $OS != "Ubuntu" ]; then
  sed -e 's/#binary_raster_comparison_enabled=false/binary_raster_comparison_enabled=false/' -i autotest/autotest/conf/eoxserver.conf
fi

# Configure the specified database system
case $DB in
    "spatialite")
        echo "Using spatialite database!"
        # Noting to do, as by default eoxserver autotest will use a spatialite db
        ;;
    "postgis")
        echo "Using postgis database!"
        sed -e "s/'ENGINE':.*/'ENGINE': 'django.contrib.gis.db.backends.postgis',/" -i autotest/autotest/settings.py
        sed -e "s/'NAME':.*/'NAME': 'eoxserver_testing',/" -i autotest/autotest/settings.py
        sed -e "s/'USER':.*/'USER': 'jenkins',/" -i autotest/autotest/settings.py
        sed -e "s/'PASSWORD':.*/'PASSWORD': 'eeJ0Kain',/" -i autotest/autotest/settings.py
        sed -e "/'HOST':.*/d" -i autotest/autotest/settings.py
        sed -e "/'PORT':.*/d" -i autotest/autotest/settings.py
        ;;
    *)
        echo "Unknown database system, Exiting..."
        exit 1
        ;;
esac

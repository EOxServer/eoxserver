#!/bin/sh -xe

OS=`facter operatingsystem`

# Create the virtual environment if it does not exist
cd $WORKSPACE
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
    "django1.3")
        echo "Using latest django 1.3"
        pip install "django<1.4,>=1.3"
        ;;
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
python setup.py develop

# Create the EOxServer instance
echo "**> creating autotest instance..."
mv autotest tmp1
eoxserver-admin.py create_instance autotest --init_spatialite
if [ $DJANGO -eq "django1.3" ]; do
    cp -R tmp1/* autotest/
    rm r tmp1
else
    mv autotest/manage.py tmp1/
    mv autotest/autotest/ tmp2
    rmdir autotest/
    mv tmp1 autotest
    mv tmp2/settings.py autotest/
    mv tmp2/conf/eoxserver.conf autotest/conf/
    mv tmp2/wsgi.py autotest/
    mv tmp2/data/config.sqlite autotest/data/
    mv tmp2/data/init_spatialite-2.3.sql autotest/data/
    rm -r tmp2
fi
sed -e 's/\/autotest\/autotest/\/autotest/' -i autotest/settings.py
sed -e "s/#'TEST_NAME':/'TEST_NAME':/" -i autotest/settings.py
sed -e 's/\/autotest\/autotest/\/autotest/' -i autotest/conf/eoxserver.conf
sed -e 's/allowed_actions=/allowed_actions=Add,Delete/' -i autotest/conf/eoxserver.conf

if [ $OS != 'Ubuntu' ]; then
  sed -e 's/#binary_raster_comparison_enabled=false/binary_raster_comparison_enabled=false/' -i autotest/conf/eoxserver.conf
fi

# Configure the specified database system
case $DB in
    "spatialite")
        echo "Using spatialite database!"
        # Noting to do, as by default eoxserver autotest will use a spatialite db
        ;;
    "postgis")
        echo "Using postgis database!"
        sed -e "s/'ENGINE':.*/'ENGINE': 'django.contrib.gis.db.backends.postgis',/" -i autotest/settings.py
        sed -e "s/'NAME':.*/'NAME': 'eoxserver_testing',/" -i autotest/settings.py
        sed -e "s/'USER':.*/'USER': 'jenkins',/" -i autotest/settings.py
        sed -e "s/'PASSWORD':.*/'PASSWORD': 'eeJ0Kain',/" -i autotest/settings.py
        sed -e "/'HOST':.*/d" -i autotest/settings.py
        sed -e "/'PORT':.*/d" -i autotest/settings.py
        ;;
    *)
        echo "Unknown database system, Exiting..."
        exit 1
        ;;
esac

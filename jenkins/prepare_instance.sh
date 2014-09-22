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

django-admin.py --version

if [ $OS == "Ubuntu" ] && [ $DJANGO == "django1.4" ]; then
    find . -name libgeos.py  -exec patch {} jenkins/geos-dev.patch \;
fi

# Install EOxServer
echo "**> installing eoxserver..."
if [ $OS == "Ubuntu" ]; then
    python setup.py develop --disable-extended-reftools
else
    python setup.py develop
fi

if [ $OS == "Ubuntu" ]; then
  sed -e 's/#binary_raster_comparison_enabled=false/binary_raster_comparison_enabled=false/' -i autotest/autotest/conf/eoxserver.conf
  echo "disabled_tests=WCS20GetCoverageReferenceableDatasetGeogCRSSubsetTestCase,WCS20GetCoverageReferenceableDatasetGeogCRSSubsetExceedsExtentTestCase,WCS20GetCoverageOutputCRSotherUoMDatasetTestCase,WCS20GetCoverageJPEG2000TestCase,WCS20DescribeEOCoverageSetIncorrectSpatialSubsetFaultTestCase,WCS10DescribeCoverageMosaicTestCase,WCS10DescribeCoverageDatasetTestCase" >> autotest/autotest/conf/eoxserver.conf
fi

# Configure the specified database system
case $DB in
    "spatialite")
        echo "Using spatialite database!"
        # Noting to do, as by default eoxserver autotest will use a spatialite db
        ;;
    "postgis")
        echo "Using postgis database!"
        sed -e "s/'USER':.*/'USER': 'jenkins',/" -i autotest/autotest/settings.py
        sed -e "s/'PASSWORD':.*/'PASSWORD': 'eeJ0Kain',/" -i autotest/autotest/settings.py
        ;;
    *)
        echo "Unknown database system, Exiting..."
        exit 1
        ;;
esac

# Create a new EOxServer instance for command line, server, etc. testing
echo "**> creating autotest_jenkins instance..."
rm -rf autotest_jenkins/
eoxserver-admin.py create_instance autotest_jenkins --init_spatialite
cp -R autotest/autotest/data/fixtures/ autotest_jenkins/autotest_jenkins/data/
cp -R autotest/autotest/data/meris/ autotest_jenkins/autotest_jenkins/data/
cp -R autotest/autotest/data/asar/ autotest_jenkins/autotest_jenkins/data/
cp -R autotest/autotest/expected/ autotest_jenkins/autotest_jenkins/
cp autotest/autotest/conf/eoxserver.conf autotest_jenkins/autotest_jenkins/conf/eoxserver.conf
mkdir -p autotest_jenkins/autotest_jenkins/responses/

# Configure the specified database system
case $DB in
    "spatialite")
        echo "Using spatialite database!"
        # Noting to do, as by default eoxserver autotest will use a spatialite db
        ;;
    "postgis")
        echo "Using postgis database!"
        sed -e "s/'ENGINE':.*/'ENGINE': 'django.contrib.gis.db.backends.postgis',/" -i autotest_jenkins/autotest_jenkins/settings.py
        sed -e "s/'NAME':.*/'NAME': 'eoxserver_testing',/" -i autotest_jenkins/autotest_jenkins/settings.py
        sed -e "s/'USER':.*/'USER': 'jenkins',/" -i autotest_jenkins/autotest_jenkins/settings.py
        sed -e "s/'PASSWORD':.*/'PASSWORD': 'eeJ0Kain',/" -i autotest_jenkins/autotest_jenkins/settings.py
        sed -e "/'HOST':.*/d" -i autotest_jenkins/autotest_jenkins/settings.py
        sed -e "/'PORT':.*/d" -i autotest_jenkins/autotest_jenkins/settings.py
        ;;
    *)
        echo "Unknown database system, Exiting..."
        exit 1
        ;;
esac

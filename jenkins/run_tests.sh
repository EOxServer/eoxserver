#!/bin/sh -xe

OS=`facter operatingsystem`

# Activate the virtual environment
cd $WORKSPACE
source .venv/bin/activate

cd autotest
export XML_CATALOG_FILES="$WORKSPACE/schemas/catalog.xml"
echo "**> running tests ..."
if [ $OS == "Ubuntu" ]; then
    python manage.py test services -v2
else
    python manage.py test "services|WMS13GetCapabilitiesEmptyTestCase,WMS13GetCapabilitiesValidTestCase,SecWMS13GetCapabilitiesValidTestCase,WCS11GetCapabilitiesEmptyTestCase,WCS11GetCapabilitiesValidTestCase,WCS11PostGetCapabilitiesValidTestCase,WCS11TransactionAsyncRectifiedDatasetTestCase,WCS11TransactionRectifiedDatasetTestCase,WCS20GetCoverageOutputCRSotherUoMDatasetTestCase,WCS20GetCoverageReprojectedEPSG3857DatasetTestCase,WCS20GetCoverageJPEG2000TestCase" -v2
    # TODO: Make WCS20GetCoverageJPEG2000TestCase work.
fi
#TODO: Enable testing of all apps
#python manage.py test core services coverages backends processes -v2

# Run command line tests
echo "**> running command line tests ..."

# Restet PostGIS database if used
if [ $DB == "postgis" ]; then
    dropdb eoxserver_testing
    createdb -T template_postgis -O jenkins eoxserver_testing
fi

python manage.py syncdb --noinput
python manage.py loaddata auth_data.json initial_rangetypes.json testing_base.json testing_asar_base.json
python manage.py eoxs_add_dataset_series -i MER_FRS_1P_reduced --traceback
python manage.py eoxs_register_dataset -d data/meris/MER_FRS_1P_reduced/*.tif -r MERIS_uint16 --dataset-series MER_FRS_1P_reduced --traceback
python manage.py eoxs_register_dataset -d data/meris/mosaic_MER_FRS_1P_RGB_reduced/*.tif -r RGB --traceback
python manage.py eoxs_register_dataset -d data/asar/*.tiff -m data/asar/*.tiff -r ASAR --traceback

# Send some requests and compare results with expected results
python manage.py runserver 1>/dev/null 2>&1 &
sleep 3
PID=$!

curl -sS -o tmp "http://localhost:8000/ows?service=wcs&request=getcapabilities"
xmllint --format tmp > tmp1
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.0&request=GetCapabilities"
xmllint --format tmp > tmp2
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
xmllint --format tmp > tmp3
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
xmllint --format tmp > tmp4

# Restart development server otherwise the GetCoverage requests hangs forever
kill `ps --ppid $PID -o pid=`
python manage.py runserver 1>/dev/null 2>&1 &
sleep 3
PID=$!

curl -sS -o tmp "http://localhost:8000/ows?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff"

# Perform binary comparison only on reference platform
if [ $DB == "spatialite" ]; then
    diff tmp1 expected/command_line_test_getcapabilities.xml
    diff tmp2 expected/command_line_test_getcapabilities.xml
    diff tmp3 expected/command_line_test_describecoverage.xml
    diff tmp4 expected/command_line_test_describeeocoverageset.xml
fi
if [ $OS == "Ubuntu" ]; then
    diff tmp expected/WCS20GetCoverageDatasetTestCase.tif
fi

rm tmp tmp1 tmp2 tmp3 tmp4
kill `ps --ppid $PID -o pid=`

python manage.py eoxs_synchronize --all --traceback

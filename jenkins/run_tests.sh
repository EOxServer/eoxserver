#!/bin/sh -xe

OS=`facter operatingsystem`

# Activate the virtual environment
cd "$WORKSPACE"
source .venv/bin/activate

# Run pylint
echo "**> running pylint tests ..."
#TODO pylint -E

# Run unit tests
echo "**> running unit tests tests ..."
cd autotest

# Make sure the PostGIS test database is not present
if [ $DB == "postgis" ] && [ `psql template_postgis jenkins -tAc "SELECT 1 FROM pg_database WHERE datname='test_eoxserver_testing'"` ] ; then
    echo "Dropping PostGIS test database."
    dropdb test_eoxserver_testing
fi

export XML_CATALOG_FILES="$WORKSPACE/schemas/catalog.xml"
python manage.py test autotest_services -v2
python manage.py test services coverages -v2
#TODO: Enable testing of all apps
#python manage.py test autotest_services core services coverages backends processes -v2
cd ..

# Run command line tests
echo "**> running command line tests ..."
cd autotest_jenkins

# Restet PostGIS database if used
if [ $DB == "postgis" ]; then
    if [ `psql template_postgis jenkins -tAc "SELECT 1 FROM pg_database WHERE datname='eoxserver_testing'"` ] ; then
        echo "Dropping PostGIS database."
        dropdb eoxserver_testing
    fi
    createdb -T template_postgis -O jenkins eoxserver_testing
fi

python manage.py syncdb --noinput --traceback
python manage.py loaddata auth_data.json range_types.json --traceback
python manage.py eoxs_rangetype_load -i autotest_jenkins/data/meris/meris_range_type_definition.json --traceback
python manage.py eoxs_rangetype_load -i autotest_jenkins/data/asar/asar_range_type_definition.json --traceback
python manage.py eoxs_rangetype_list --traceback
python manage.py eoxs_rangetype_list --json --traceback # dump all range-types as JSON
python manage.py eoxs_collection_create -i MER_FRS_1P_reduced --traceback
python manage.py eoxs_dataset_register -d autotest_jenkins/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif -m autotest_jenkins/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml -r MERIS_uint16 --visible --traceback
python manage.py eoxs_dataset_register -d autotest_jenkins/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif -m autotest_jenkins/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.xml -r MERIS_uint16 --visible --traceback
python manage.py eoxs_dataset_register -d autotest_jenkins/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.tif -m autotest_jenkins/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.xml -r MERIS_uint16 --visible --traceback

python manage.py eoxs_collection_link --collection MER_FRS_1P_reduced --add MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed

python manage.py eoxs_dataset_register --collection MER_FRS_1P_reduced -d autotest_jenkins/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif -m autotest_jenkins/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.xml -r RGB --visible --traceback
python manage.py eoxs_dataset_register --collection MER_FRS_1P_reduced -d autotest_jenkins/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.tif -m autotest_jenkins/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.xml -r RGB --visible --traceback
python manage.py eoxs_dataset_register --collection MER_FRS_1P_reduced -d autotest_jenkins/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced.tif -m autotest_jenkins/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced.xml -r RGB --visible --traceback
#python manage.py eoxs_collection_link --series MER_FRS_1P_reduced --add mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced --traceback

python manage.py eoxs_dataset_register -d autotest_jenkins/data/asar/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tiff -r ASAR --coverage-type=ReferenceableDataset --projection 4326 --extent 16.727605,-36.259107,22.301754,-31.984922 --visible --traceback
python manage.py eoxs_id_list --traceback

# Send some requests and compare results with expected results
python manage.py runserver 1>/dev/null 2>&1 &
sleep 3
PID=$!

curl -sS -o tmp "http://localhost:8000/ows?service=wcs&request=getcapabilities"
xmllint --format tmp > tmp1
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.1&request=GetCapabilities"
xmllint --format tmp > tmp2
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.1&request=DescribeCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
xmllint --format tmp > tmp3
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.1&request=DescribeEOCoverageSet&eoId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
xmllint --format tmp > tmp4

# Restart development server otherwise the GetCoverage request hangs forever
kill `ps --ppid $PID -o pid=`
python manage.py runserver 1>/dev/null 2>&1 &
sleep 3
PID=$!

curl -sS -o tmp "http://localhost:8000/ows?service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff"

# Perform binary comparison only on reference platform
if [ $DB == "spatialite" ]; then
    diff tmp1 autotest_jenkins/expected/command_line_test_getcapabilities.xml
    diff tmp2 autotest_jenkins/expected/command_line_test_getcapabilities.xml
    diff tmp3 autotest_jenkins/expected/command_line_test_describecoverage.xml
    diff tmp4 autotest_jenkins/expected/command_line_test_describeeocoverageset.xml
fi
if [ $OS != "Ubuntu" ]; then
    diff tmp autotest_jenkins/expected/WCS20GetCoverageDatasetTestCase.tif
fi

rm tmp tmp1 tmp2 tmp3 tmp4
kill `ps --ppid $PID -o pid=`

python manage.py eoxs_collection_unlink --collection MER_FRS_1P_reduced --remove mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced --traceback
python manage.py eoxs_dataset_deregister mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced --traceback
python manage.py eoxs_id_list --traceback
python manage.py eoxs_id_check --traceback -t DatasetSeries MER_FRS_1P_reduced && echo "Test of 'eoxs_id_check' passed."
python manage.py eoxs_id_check --traceback ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed && echo "Test of 'eoxs_id_check' passed."
python manage.py eoxs_id_check --traceback nonexistent_XYZ || echo "Test of 'eoxs_id_check' passed."
#python manage.py eoxs_id_check notused --traceback
#python manage.py eoxs_id_check ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed --traceback
#python manage.py eoxs_id_check MER_FRS_1P_reduced --traceback
# TODO: re-activate once implemented
#python manage.py eoxs_collection_create -i test_sync -d autotest_jenkins/data/meris/MER_FRS_1P_reduced/ autotest_jenkins/data/meris/mosaic_MER_FRS_1P_reduced_RGB/ -p "*.tif" --traceback
#python manage.py eoxs_synchronize -a --traceback
python manage.py eoxs_id_list --traceback

# Run Selenium
echo "**> running Selenium tests ..."
#TODO

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
export XML_CATALOG_FILES="$WORKSPACE/schemas/catalog.xml"
# ftp tests are disabled
if [ $OS == "Ubuntu" ]; then
    python manage.py test "services|WCS20GetCoverageJPEG2000TestCase,WCS10DescribeCoverageDatasetTestCase,WCS10DescribeCoverageMosaicTestCase,WCS11TransactionReferenceableDatasetTestCase,WCS20GetCoverageReferenceableDatasetGeogCRSSubsetExceedsExtentTestCase,WCS20GetCoverageReferenceableDatasetGeogCRSSubsetTestCase,WCS20GetCoverageReferenceableDatasetImageCRSSubsetTestCase,WCS20PostGetCoverageReferenceableMultipartDatasetTestCase" -v2
    python manage.py test "coverages|RegisterRemoteDatasetTestCase,RectifiedStitchedMosaicCreateWithRemotePathTestCase" -v2
else
    python manage.py test "services|WCS20GetCoverageOutputCRSotherUoMDatasetTestCase,WCS20GetCoverageReprojectedEPSG3857DatasetTestCase" -v2
    python manage.py test "coverages|RegisterRemoteDatasetTestCase,RectifiedStitchedMosaicCreateWithRemotePathTestCase" -v2
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

python manage.py syncdb --noinput --traceback
python manage.py loaddata auth_data.json initial_rangetypes.json --traceback
python manage.py eoxs_load_rangetypes --traceback << EOF
[{
    "bands": [
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS first band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_01_uint16",
            "name": "MERIS_radiance_01_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 second band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_02_uint16",
            "name": "MERIS_radiance_02_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 third band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_03_uint16",
            "name": "MERIS_radiance_03_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 fourth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_04_uint16",
            "name": "MERIS_radiance_04_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 fifth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_05_uint16",
            "name": "MERIS_radiance_05_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 sixth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_06_uint16",
            "name": "MERIS_radiance_06_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 seventh band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_07_uint16",
            "name": "MERIS_radiance_07_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 eighth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_08_uint16",
            "name": "MERIS_radiance_08_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 ninth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_09_uint16",
            "name": "MERIS_radiance_09_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 tenth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_10_uint16",
            "name": "MERIS_radiance_10_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 eleventh band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_11_uint16",
            "name": "MERIS_radiance_11_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 twelfth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_12_uint16",
            "name": "MERIS_radiance_12_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint 16 thirteenth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_13_uint16",
            "name": "MERIS_radiance_13_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 fourteenth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_14_uint16",
            "name": "MERIS_radiance_14_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        },
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
            "description": "MERIS uint16 fifteenth band",
            "gdal_interpretation": "Undefined",
            "identifier": "MERIS_radiance_15_uint16",
            "name": "MERIS_radiance_15_uint16",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "W.m-2.sr-1.nm-1"
        }
    ],
    "data_type": "UInt16",
    "name": "MERIS_uint16"
},
{
    "bands": [
        {
            "definition": "http://www.opengis.net/def/property/OGC/0/Amplitude",
            "description": "ASAR Amplitude Band",
            "gdal_interpretation": "Undefined",
            "identifier": "ASAR_Amplitude",
            "name": "ASAR_Amplitude",
            "nil_values": [
                {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                    "value": 0
                }
            ],
            "uom": "?"
        }
    ],
    "data_type": "UInt16",
    "name": "ASAR"
}]
EOF
python manage.py eoxs_list_rangetypes --traceback
python manage.py eoxs_add_dataset_series -i MER_FRS_1P_reduced --traceback
python manage.py eoxs_register_dataset -d autotest/data/meris/MER_FRS_1P_reduced/*.tif -r MERIS_uint16 --dataset-series MER_FRS_1P_reduced --traceback
python manage.py eoxs_register_dataset -d autotest/data/meris/mosaic_MER_FRS_1P_RGB_reduced/*.tif -r RGB --traceback
python manage.py eoxs_register_dataset -d autotest/data/asar/*.tiff -r ASAR --traceback
python manage.py eoxs_list_ids --traceback
python manage.py eoxs_insert_into_series -d mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced -s MER_FRS_1P_reduced --traceback

# Send some requests and compare results with expected results
python manage.py runserver 1>/dev/null 2>&1 &
sleep 3
PID=$!

curl -sS -o tmp "http://localhost:8000/ows?service=wcs&request=getcapabilities"
xmllint --format tmp > tmp1
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.1&request=GetCapabilities"
xmllint --format tmp > tmp2
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.1&request=DescribeCoverage&CoverageId=ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
xmllint --format tmp > tmp3
curl -sS -o tmp "http://localhost:8000/ows?service=WCS&version=2.0.1&request=DescribeEOCoverageSet&eoId=ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
xmllint --format tmp > tmp4

# Restart development server otherwise the GetCoverage requests hangs forever
kill `ps --ppid $PID -o pid=`
python manage.py runserver 1>/dev/null 2>&1 &
sleep 3
PID=$!

curl -sS -o tmp "http://localhost:8000/ows?service=wcs&version=2.0.1&request=GetCoverage&CoverageId=ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff"

# Perform binary comparison only on reference platform
if [ $DB == "spatialite" ]; then
    diff tmp1 autotest/expected/command_line_test_getcapabilities.xml
    diff tmp2 autotest/expected/command_line_test_getcapabilities.xml
    diff tmp3 autotest/expected/command_line_test_describecoverage.xml
    diff tmp4 autotest/expected/command_line_test_describeeocoverageset.xml
fi
if [ $OS == "Ubuntu" ]; then
    diff tmp autotest/expected/WCS20GetCoverageDatasetTestCase.tif
fi

rm tmp tmp1 tmp2 tmp3 tmp4
kill `ps --ppid $PID -o pid=`

python manage.py eoxs_remove_from_series -d mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced -s MER_FRS_1P_reduced --traceback
python manage.py eoxs_deregister_dataset mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced --traceback
python manage.py eoxs_list_ids --traceback
python manage.py eoxs_check_id -a notused --traceback
python manage.py eoxs_check_id -u ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed --traceback
python manage.py eoxs_check_id -u MER_FRS_1P_reduced --traceback
python manage.py eoxs_add_dataset_series -i test_sync -d autotest/data/meris/MER_FRS_1P_reduced/ autotest/data/meris/mosaic_MER_FRS_1P_RGB_reduced/ -p "*.tif" --traceback
python manage.py eoxs_synchronize -a --traceback
python manage.py eoxs_list_ids --traceback

# Run Selenium
echo "**> running Selenium tests ..."
#TODO

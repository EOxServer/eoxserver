#!/bin/bash -xe

function dumpdata_coveragetype() {
  python manage.py dumpdata --indent=4 coverages.CoverageType coverages.FieldType coverages.AllowedValueRange coverages.NilValue 
}

function dumpdata_coverages() {
  python manage.py dumpdata --indent=4 coverages.EOObject coverages.Coverage coverages.Collection coverages.ArrayDataItem coverages.MetaDataItem coverages.Grid
}

##

# TODO: make documentation

#


#
# ASAR
#

# Load ASAR coveragetypes
python manage.py coveragetype import autotest/data/asar/asar_range_type_definition.json

# save ASAR coveragetype fixtures
dumpdata_coveragetype > autotest/data/asar/asar_range_type.json

# register ASAR data
python manage.py coverage register \
    -i ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775 \
    --begin-time 2005-03-31T08:00:36.342970Z \
    --end-time 2005-03-31T07:59:36.409059Z \
    -d autotest/data/asar/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tiff

# save ASAR coverages fixtures
dumpdata_coverages > autotest/data/asar/asar_coverages.json

# deregister ASAR coverages/coverage types
python manage.py coverage deregister ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775
python manage.py coveragetype delete ASAR

#
# MERIS Uint16
#

##### 


# Load MERIS coveragetypes
python manage.py coveragetype import autotest/data/meris/meris_range_type_definition.json

# save MERIS coveragetype fixtures
dumpdata_coveragetype > autotest/data/meris/meris_range_type.json

# create a collection for the coverages
python manage.py collection create MER_FRS_1P_reduced

# register MERIS Uint16 data
python manage.py coverage register \
    -t MERIS_uint16 \
    -d autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif \
    -m autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml

python manage.py coverage register \
    -t MERIS_uint16 \
    -d autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif \
    -m autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.xml

python manage.py coverage register \
    -t MERIS_uint16 \
    -d autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.tif \
    -m autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.xml

python manage.py collection insert MER_FRS_1P_reduced MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed
python manage.py collection insert MER_FRS_1P_reduced MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed
python manage.py collection insert MER_FRS_1P_reduced MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed

dumpdata_coverages > autotest/data/meris/meris_coverages_uint16.json

# deregister coverages and collections
python manage.py coverage deregister MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed
python manage.py coverage deregister MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed
python manage.py coverage deregister MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed
python manage.py collection delete MER_FRS_1P_reduced

# deregister MERIS Uint16 coverages/coverage types
python manage.py coveragetype delete MERIS_uint16

#
# MERIS RGB
#

# Load RGB coveragetypes
python manage.py coveragetype import autotest/data/rgb_definition.json


# TODO: dump coveragetype for RGB as-well?



# create a collection for the coverages
python manage.py collection create MER_FRS_1P_reduced_RGB

# create a grid + mosaic for the coverages
python manage.py grid create mosaic_MER_FRS_1P_reduced_RGB_grid EPSG:4326 -n x -n y -t spatial -t spatial -o 0.031355000000000 -o -0.031355000000000
python manage.py mosaic create mosaic_MER_FRS_1P_reduced_RGB -t RGB --grid mosaic_MER_FRS_1P_reduced_RGB_grid

# register MERIS RGB data
python manage.py coverage register \
    -t RGB --grid mosaic_MER_FRS_1P_reduced_RGB_grid \
    -d autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif \
    -m autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.xml

python manage.py coverage register \
    -t RGB --grid mosaic_MER_FRS_1P_reduced_RGB_grid \
    -d autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.tif \
    -m autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.xml

python manage.py coverage register \
    -t RGB --grid mosaic_MER_FRS_1P_reduced_RGB_grid \
    -d autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced.tif \
    -m autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced.xml

# insert coverages into mosaic and collection
python manage.py mosaic insert mosaic_MER_FRS_1P_reduced_RGB mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced
python manage.py collection insert MER_FRS_1P_reduced_RGB mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced

dumpdata_coverages > autotest/data/meris/meris_coverages_rgb.json

python manage.py coverage deregister mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced
python manage.py coverage deregister mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced
python manage.py coverage deregister mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced

python manage.py mosaic delete mosaic_MER_FRS_1P_reduced_RGB
python manage.py grid delete mosaic_MER_FRS_1P_reduced_RGB_grid

python manage.py collection delete MER_FRS_1P_reduced_RGB

#
# CROSSES_DATELINE
#

# register CROSSES data
python manage.py coverage register \
    -i crosses_dateline \
    -t RGB \
    -d autotest/data/misc/crosses_dateline.tif

# save ASAR coverages fixtures
dumpdata_coverages > autotest/data/misc/crosses_dateline.json

# deregister CROSSES_DATELINE coverages/coverage types
python manage.py coverage deregister crosses_dateline
# We are using the same RGB coveragetypes as MERIS RGB, so we deregister RGB coverages/coverage types one time here
python manage.py coveragetype delete RGB
#!/bin/bash -xe

# save current database
mv autotest/data/config.sqlite autotest/data/bakfixtures.config.sqlite

# recreate database
python manage.py migrate

# save initial data as base.json
python manage.py dumpdata --indent 4 > out/base.json

#
# ASAR
#

# Load ASAR coveragetypes
python manage.py coveragetype import autotest/data/asar/asar_range_type_definition.json

# save ASAR coveragetype fixtures
# python manage.py dumpdata coverages --indent 4 > out/asar_coveragetypes.json

# register ASAR data
python manage.py coverage register \
    -i ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775 \
    --begin-time 2005-03-31T08:00:36.342970Z \
    --end-time 2005-03-31T07:59:36.409059Z \
    -d autotest/data/asar/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tiff

# save ASAR coverages fixtures
# python manage.py dumpdata coverages --indent 4 \
#     -e coverages.CoverageType \
#     -e coverages.NilValue \
#     -e coverages.FieldType > out/asar_coverages.json

# deregister ASAR coverages/coverage types
# python manage.py coverage deregister ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775
# python manage.py coveragetype delete ASAR

#
# MERIS Uint16
#


##### 


# Load MERIS coveragetypes
python manage.py coveragetype import autotest/data/meris/meris_range_type_definition.json

# save MERIS coveragetype fixtures
# python manage.py dumpdata coverages --indent 4 > out/meris_coveragetypes.json

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

#######

# save MERIS coverages fixtures
# python manage.py dumpdata coverages backends --indent 4 \
#     -e coverages.CoverageType \
#     -e coverages.NilValue \
#     -e coverages.FieldType > out/meris_coverages_uint16.json

# deregister coverages and collections
# python manage.py coverage deregister MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed
# python manage.py coverage deregister MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed
# python manage.py coverage deregister MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed
# python manage.py collection delete MER_FRS_1P_reduced

# deregister MERIS Uint16 coverages/coverage types
# python manage.py coveragetype delete MERIS_uint16

#
# MERIS RGB
#

# Load MERIS coveragetypes
# python manage.py coveragetype import autotest/data/meris/meris_range_type_definition.json

# save MERIS coveragetype fixtures
# python manage.py dumpdata coverages --indent 4 > out/meris_coveragetypes.json

# Load RGB coveragetypes
python manage.py coveragetype import autotest/data/rgb_definition.json

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

python manage.py dumpdata coverages backends --indent 4 > autotest/data/fixtures/fixtures.json


mv autotest/data/bakfixtures.config.sqlite autotest/data/config.sqlite
function dumpdata_coveragetype() {
  python manage.py dumpdata --indent=4 coverages.CoverageType coverages.FieldType coverages.AllowedValueRange coverages.NilValue  \
  | sed 's/        "inserted":.*/        "inserted": "2019-01-01T00:00:00.000Z",/g' \
  | sed 's/        "updated":.*/        "updated": "2019-01-01T00:00:00.000Z"/g'
}


# 
# # Full Products example
#

# Load MERIS coveragetypes

python manage.py coveragetype import autotest/data/meris/meris_range_type_definition.json


# create a product type with the allowed coverage type from above

python manage.py producttype create MERIS_range_type -c MERIS_uint16 

######### add browse type with nice visualizations (find examples for MERIS)

python manage.py browsetype create MERIS_range_type "NDVI" --traceback \
        --grey "(MERIS_radiance_13_uint16-MERIS_radiance_07_uint16)/(MERIS_radiance_13_uint16+MERIS_radiance_07_uint16)" --grey-range -0.597591 0.998323


# create a collection type with the allowed product type above


python manage.py collectiontype create MERIS_Products_range_type -p MERIS_range_type


# save MERIS coveragetype fixtures
dumpdata_coveragetype > autotest/data/meris/meris_range_type.json

# create a collection for the coverages usin the collection type above

python manage.py collection create MER_FRS_1P_reduced -t MERIS_Products_range_type

# create 3 products using the metadata from the .xmls and set metadata like cloud coverage and so on

product_A_ID=$(python manage.py product register -t MERIS_range_type -r --print-identifier --metadata-file /opt/instance/autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml)

product_B_ID=$(python manage.py product register -t MERIS_range_type -r --print-identifier --metadata-file /opt/instance/autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.xml)

product_C_ID=$(python manage.py product register -t MERIS_range_type -r --print-identifier --metadata-file /opt/instance/autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.xml)

# register the RGB TIFFs as browses

python manage.py browse register $product_A_ID /opt/instance/autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif
python manage.py browse register $product_B_ID /opt/instance/autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.tif
python manage.py browse register $product_C_ID /opt/instance/autotest/data/meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced.tif

# register MERIS Uint16 data

# for each coverage registered set the associated product from above

coverage_A_ID=$(python manage.py coverage register \
    -t MERIS_uint16 \
    -d autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif \
    -m autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml \
    --identifier-template 'coverage_{identifier}' -p $product_A_ID --print-identifier -r)

coverage_B_ID=$(python manage.py coverage register \
    -t MERIS_uint16 \
    -d autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif \
    -m autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.xml \
    --identifier-template 'coverage_{identifier}' -p $product_B_ID --print-identifier -r)

coverage_C_ID=$(python manage.py coverage register \
    -t MERIS_uint16 \
    -d autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.tif \
    -m autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.xml \
    --identifier-template 'coverage_{identifier}' -p $product_C_ID  --print-identifier -r)

# dont register the coverages but the products
python manage.py collection insert MER_FRS_1P_reduced $product_A_ID
python manage.py collection insert MER_FRS_1P_reduced $product_B_ID
python manage.py collection insert MER_FRS_1P_reduced $product_C_ID

python manage.py dumpdata backends coverages services > autotest/data/meris/client.json


# deregister coverages
python manage.py coverage deregister $coverage_A_ID
python manage.py coverage deregister $coverage_B_ID
python manage.py coverage deregister $coverage_C_ID

python manage.py coveragetype delete MERIS_uint16



python manage.py product deregister $product_A_ID
python manage.py product deregister $product_B_ID
python manage.py product deregister $product_C_ID

python manage.py producttype delete MERIS_range_type


python manage.py collection delete MER_FRS_1P_reduced

python manage.py collectiontype delete MERIS_Products_range_type





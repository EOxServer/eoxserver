product_path=$1
browses_path=$2


img_data=$(unzip -Z -2 $product_path | grep jp2$)
out_browse_image=${browses_path}/$(basename "$product_path").tif

# create browse image if it does not yet exist
[ -e $out_browse_image ] || {
    tci_path=$(echo "$img_data" | grep TCI.jp2)

    unzip -j $product_path $tci_path -d /tmp/ -u > /dev/null

    gdal_translate /tmp/$(basename "$tci_path") $out_browse_image \
        -co TILED=YES --config GDAL_CACHEMAX 1000 --config GDAL_NUM_THREADS 4 \
        -co COMPRESS=LZW

    gdaladdo --config COMPRESS_OVERVIEW LZW $out_browse_image 2 4 8 16 32 64 128 256

    rm /tmp/$(basename "$tci_path")
}



# actually register the product
product_id=$(
    python manage.py product register \
        --package $product_path --product-type S2MSI1C \
        --no-browses \
        --replace --print-identifier
)

# register the generated browse
python manage.py browse register $product_id ${browses_path}/$(basename "$product_path").tif

# insert the product in the collection
python manage.py collection insert S2MSI1C $product_id

# img_data=$(python manage.py product discover $product_id "*/GRANULE/*/IMG_DATA/*.jp2" 2> /dev/null)

for band in B01 B02 B03 B04 B05 B06 B07 B08 B8A B09 B10 B11 B12 ; do
    # echo "*/GRANULE/*/IMG_DATA/*$band.jp2" '*/GRANULE/*/IMG_DATA/*$band.jp2'
    # python manage.py product discover $PRODUCT_ID "*/GRANULE/*/IMG_DATA/*$band.jp2" 2> /dev/null
    coverage_path=$(echo "$img_data" | grep ${band}.jp2)
    python manage.py coverage register \
        -d $product_path $coverage_path --coverage-type S2MSI1C_${band} \
        --identifier ${product_id}_${band} --product ${product_id} --replace
done

python manage.py collection summary S2MSI1C

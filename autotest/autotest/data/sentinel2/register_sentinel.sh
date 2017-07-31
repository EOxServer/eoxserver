product_path=$1

product_id=$(python manage.py product register --package $product_path --print-identifier --product-type S2MSI1C)

for band in B01 B02 B03 B04 B05 B06 B07 B08 B8A B09 B10 B11 B12 ; do
    # echo "*/GRANULE/*/IMG_DATA/*$band.jp2" '*/GRANULE/*/IMG_DATA/*$band.jp2'
    # python manage.py product discover $PRODUCT_ID "*/GRANULE/*/IMG_DATA/*$band.jp2" 2> /dev/null
    coverage_path=$(python manage.py product discover $product_id "*/GRANULE/*/IMG_DATA/*$band.jp2" 2> /dev/null)
    python manage.py coverage register -d $product_path $coverage_path --coverage-type S2MSI1C_${band} --identifier ${product_id}_${band}

    python manage.py product insert
done

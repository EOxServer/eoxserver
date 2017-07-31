python manage.py coveragetype create S2MSI1C_B01 --field-type B01 B01 "Solar irradiance" "W/m2/um" 1913.57
python manage.py coveragetype create S2MSI1C_B02 --field-type B02 B02 "Solar irradiance" "W/m2/um" 1941.63
python manage.py coveragetype create S2MSI1C_B03 --field-type B03 B03 "Solar irradiance" "W/m2/um" 1822.61
python manage.py coveragetype create S2MSI1C_B04 --field-type B04 B04 "Solar irradiance" "W/m2/um" 1512.79
python manage.py coveragetype create S2MSI1C_B05 --field-type B05 B05 "Solar irradiance" "W/m2/um" 1425.56
python manage.py coveragetype create S2MSI1C_B06 --field-type B06 B06 "Solar irradiance" "W/m2/um" 1288.32
python manage.py coveragetype create S2MSI1C_B07 --field-type B07 B07 "Solar irradiance" "W/m2/um" 1163.19
python manage.py coveragetype create S2MSI1C_B08 --field-type B08 B08 "Solar irradiance" "W/m2/um" 1036.39
python manage.py coveragetype create S2MSI1C_B8A --field-type B8A B8A "Solar irradiance" "W/m2/um" 955.19
python manage.py coveragetype create S2MSI1C_B09 --field-type B09 B09 "Solar irradiance" "W/m2/um" 813.04
python manage.py coveragetype create S2MSI1C_B10 --field-type B10 B10 "Solar irradiance" "W/m2/um" 367.15
python manage.py coveragetype create S2MSI1C_B11 --field-type B11 B11 "Solar irradiance" "W/m2/um" 245.59
python manage.py coveragetype create S2MSI1C_B12 --field-type B12 B12 "Solar irradiance" "W/m2/um" 85.25

python manage.py producttype create S2MSI1C \
    -c S2MSI1C_B01 -c S2MSI1C_B02 -c S2MSI1C_B03 -c S2MSI1C_B04 -c S2MSI1C_B05 -c S2MSI1C_B06 -c S2MSI1C_B07 -c S2MSI1C_B08 -c S2MSI1C_B8A -c S2MSI1C_B09 -c S2MSI1C_B10 -c S2MSI1C_B11 -c S2MSI1C_B12 \
    -m clouds -m no_data


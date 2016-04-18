The SoilMoisture data in this directory was kindly provided by the Vienna
University of Technology (TU Wien) and the European Space Agency (ESA).

Please see the file named LICENSE or
http://www.esa-soilmoisture-cci.org/dataregistration/terms-and-conditions
for terms and conditions for usage of data in this directory.

# Register the data

```sh
# define a range type for real SM data
python manage.py eoxs_rangetype_load -i autotest/data/cci_soilmoisture/sm_rangetype.json

# create empty collections
python manage.py eoxs_collection_create -i SoilMoisture
python manage.py eoxs_collection_create -i SoilMoistureRGB

# add datasources to the collections: a template to look up files
python manage.py eoxs_collection_datasource -i SoilMoisture -s "`pwd`/autotest/data/cci_soilmoisture/*tif" -t "`pwd`/autotest/data/cci_soilmoisture/{basename}.xml" -t "`pwd`/autotest/data/cci_soilmoisture/sm_rangetype.conf"
python manage.py eoxs_collection_datasource -i SoilMoistureRGB -s "`pwd`/autotest/data/cci_soilmoisture/*png" -t "`pwd`/autotest/data/cci_soilmoisture/{basename}.xml" -t "`pwd`/autotest/data/cci_soilmoisture/rgb_rangetype.conf"

# synchronize the collections: register/unregister depending on the files in the datasources
python manage.py eoxs_collection_synchronize -i SoilMoisture
python manage.py eoxs_collection_synchronize -i SoilMoistureRGB
```

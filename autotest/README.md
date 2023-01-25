# autotest

Autotest is an instance of eoxserver used for running tests.

## How to configure autotest

Configure database

```sh
cd autotest/
vi settings.py

python manage.py syncdb --noinput
python manage.py loaddata auth_data.json initial_rangetypes.json
```

## How to generate a custom EOxServer instance

```sh
eoxserver-admin.py create_instance <your-instance-name> --init_spatialite
cd <your-instance-name>/
python manage.py syncdb
```

## How to run tests

Perform steps outlined in `How to configure autotest`

```sh
cd /var/eoxserver/autotest/
export XML_CATALOG_FILES="../schemas/catalog.xml"
python manage.py test <appname>
```

Autotest_services only

```sh
python manage.py test autotest_services -v2
```

Test all modules

```sh
python manage.py test autotest_services services coverages backends processes core
```

or simply

```sh
python manage.py test
```

Running single tests

```sh
python manage.py test autotest_services.WCS20GetCapabilities
```

## How to load test data

Perform steps mentioned in `How to configure autotest`

```sh
cd /var/eoxserver/autotest/
python manage.py loaddata data/fixtures/some_fixture.json ...

# To load all test fixtures:
python manage.py loaddata auth_data.json range_types.json \
                 testing_base.json testing_coverages.json \
                 testing_asar_base.json testing_asar.json \
                 testing_reprojected_coverages.json
```

List of fixtures:

* initial_data.json - Base data to enable components. Loaded with syncdb.
* auth_data.json - An administration account.
* range_types.json - Range types for RGB and gray-scale coverages.
* testing_base.json - Range type for the 15 band uint16 test data.
* testing_coverages.json - Metadata for the MERIS test data.
* testing_asar_base.json - Range type for the ASAR test data.
* testing_asar.json - Metadata for the ASAR test data.
* testing_rasdaman_coverages.json - Use this fixtures in addition when
                                    rasdaman is installed and configured.
* testing_backends.json - This fixtures are used for testing the backend
                           layer only and shouldn't be loaded in the test
                           instance.
* testing_reprojected_coverages.json - Metadata for the reprojected
                                        MERIS test data.

## How to run development server

Perform steps mentioned in `How to configure autotest`

Optionally perform steps mentioned in `How to load test data`

```sh
cd /var/eoxserver/autotest/
python manage.py runserver 0.0.0.0:8000
```

The server is running on [http://localhost:8000/]

## How to update fixtures

```sh
cd /var/eoxserver/autotest/
python manage.py dumpdata --format=json --indent=4 > tmp.json
# Inspect file e.g. with: meld tmp.json data/fixtures/initial_data.json
mv tmp.json data/fixtures/<json-file>
```

## How to add expected results

To format XML files in a pretty way use the following command

```sh
xmllint --format <filename> > <tmpfilename>
mv <tmpfilename> <filename>
```

## How to compare XML documents

To compare an expected XML document with the actual XML response use the following command

```sh
cd /var/eoxserver/autotest/
../tools/xcomp.py responses/<XML-document> expected/<XML-document>
```

The XML comparator parses the XML documents and compares the documents' trees, therefore the tool is able to cope with different formatting (including different order of elements attributes and various name-space prefixes).

## How to validate XML documents

```sh
export XML_CATALOG_FILES="<path_to_eoxserver_directory>/schemas/catalog.xml"
xmllint --noout --schema http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd <XML-document>
```

## How to run schematron tests

```sh
export XML_CATALOG_FILES="<path_to_eoxserver_directory>/schemas/catalog.xml"

cd <path_to_eoxserver_directory>/schemas/
xsltproc schematron_xslt1/iso_dsdl_include.xsl wcseo/1.0/wcsEOSchematron.sch | xsltproc schematron_xslt1/iso_abstract_expand.xsl - | xsltproc schematron_xslt1/iso_svrl_for_xslt1.xsl - | xsltproc - <XML-document>
```

## How to run all tests

1. Run tests (see above)
2. Run Selenium tests
3. Run test instance, load data via CLI commands, run some requests, and
   compare responses with unit tests results
4. If libxml is built with schematron support run schematron tests (see
   above)

## How to reset the autotest instance

Perform steps outlined in `How to configure autotest`

```sh
cd /var/eoxserver/autotest/
sudo service httpd stop
```

Reset DB with PostgreSQL:

```sh
sudo su postgres -c "dropdb eoxserver_testing"
sudo su postgres -c "createdb -O eoxserver -T template_postgis eoxserver_testing"

python manage.py syncdb --noinput --traceback
python manage.py loaddata auth_data.json initial_rangetypes.json --traceback
```

Reset EOxServer

```sh
rm -f autotest/logs/eoxserver.log
touch autotest/logs/eoxserver.log

sudo service httpd start
```

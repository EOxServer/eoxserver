# Run the tests
cd $WORKSPACE/autotest
export XML_CATALOG_FILES="$WORKSPACE/schemas/catalog.xml"
echo "**> running tests..."

# Run autotest tests
#python manage.py test
#python manage.py test services.WCS1
python manage.py test services.WCS20GetCap
#python manage.py test services.WCSVersion
#python manage.py test services.WCS20DescribeCoverage
#python manage.py test services.WCS20DescribeEOCoverageSet
#python manage.py test services.WCS20GetCoverage
#python manage.py test services.WCS20Post
#python manage.py test services.WMS
#python manage.py test services.Sec

# Run command line tests
python manage.py syncdb --noinput
python manage.py loaddata auth_data.json initial_rangetypes.json
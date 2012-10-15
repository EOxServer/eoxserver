#!/bin/sh
# Create the virtual environment if it does not exist
cd $WORKSPACE
if [ -d ".venv" ]; then
  echo "**> virtualenv exists! not installing any dependencies"
else
  echo "**> creating virtualenv..."
  virtualenv .venv
  
  # Install the dependencies
  source .venv/bin/activate
  echo "**> installing dependencies..."
  pip install pysqlite pyspatialite lxml
  pip install --no-install GDAL==1.8.1
  cd $WORKSPACE/.venv/build/GDAL
  python setup.py build_ext --include-dirs=/usr/include/gdal/
  pip install --no-download GDAL
fi


# Install EOxServer and recompile pyspatialite
echo "**> installing eoxserver..."
pip install --upgrade ./

echo "**> recompiling pysqlite"
mkdir -p $WORKSPACE/tmp
cd $WORKSPACE/tmp
wget https://pysqlite.googlecode.com/files/pysqlite-2.6.3.tar.gz
tar xzf pysqlite-2.6.3.tar.gz
cd pysqlite-2.6.3
sed -i -e 's/define=SQLITE_OMIT_LOAD_EXTENSION/#define=SQLITE_OMIT_LOAD_EXTENSION/' setup.cfg 
python setup.py install --force
cd $WORKSPACE
rm -rf $WORKSPACE/tmp

# Create the EOxServer instance
echo "**> creating autotest instance..."
mv autotest autotest_orig
eoxserver-admin.py create_instance autotest
cp -r autotest_orig/* autotest/autotest/
rm -rf autotest_orig

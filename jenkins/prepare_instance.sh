#!/bin/sh -xe

OS=`facter operatingsystem`

# Create the virtual environment if it does not exist
cd $WORKSPACE
if [ -d ".venv" ]; then
  echo "**> virtualenv exists!"
else
  echo "**> creating virtualenv..."
  virtualenv --system-site-packages .venv
fi

# activate the virtual environment
source .venv/bin/activate

# Install EOxServer
echo "**> installing eoxserver..."
python setup.py develop

# Create the EOxServer instance
echo "**> creating autotest instance..."
mv autotest tmp1
eoxserver-admin.py create_instance autotest --init_spatialite
cp -R tmp1/* autotest/autotest/
rm -r tmp1

sed -e 's/pdp_type=none/pdp_type=dummypdp/' -i autotest/autotest/conf/eoxserver.conf
sed -e 's/allowed_actions=/allowed_actions=Add,Delete/' -i autotest/autotest/conf/eoxserver.conf

if [ $OS != 'Ubuntu' ]; then
  sed -e 's/#binary_raster_comparison_enabled=false/binary_raster_comparison_enabled=false/' -i autotest/autotest/conf/eoxserver.conf
fi

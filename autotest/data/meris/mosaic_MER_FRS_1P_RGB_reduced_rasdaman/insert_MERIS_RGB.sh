#!/bin/bash
#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
#
# This file is based on "insertdemo.sh" which is part of rasdaman community.
#
# --- parameter evaluation -----------------------------------------------------
if [ $# != 5 ]
then
  echo "Usage: $0 host port imagedir user passwd"
  echo "   host        host name of rasdaman server"
  echo "   port        port where rasdaman server listens (usually: 7001)"
  echo "   imagedir    source image directory"
  echo "   user        rasdaman database login name (needs write access)"
  echo "   passwd      rasdaman password"
  echo "Example: $0 localhost 7001 /home/rasdaman/install/share/rasdaman/examples/images rasadmin rasadmin"
  exit 0
fi

    HOST=$1
    PORT=$2
IMAGEDIR=$3
    USER=$4
  PASSWD=$5

# --- global defines --------------------------------------------------

# script name
PROG=`basename $0`

# database to be used
DB=RASBASE

# shorthand: insertppm parameters
INSERTPPM_ARGS="--server $HOST --port $PORT --database $DB --user $USER --passwd $PASSWD"

# --- check prerequisites ---------------------------------------------

echo "$PROG: insert MERIS test data based on rasdaman demo data insert script v2.0"
echo "$PROG: using host $HOST, image directory $IMAGEDIR, and user/passwd $USER/$PASSWD"

# --- evaluate cmd line parameters ------------------------------------

# is insertppm compiled already?
if [ -f /home/rasdaman/install/bin/insertppm ]
then
  INSERTPPM="/home/rasdaman/install/bin/insertppm"
else
  echo "$PROG: insertppm not found. Trying to compile it...\c"
  make --directory=/home/rasdaman/install/share/rasdaman/examples/c++ insertppm
  if [ -f /home/rasdaman/install/share/rasdaman/examples/c++/insertppm ]
  then
    echo "ok"
    INSERTPPM="/home/rasdaman/install/share/rasdaman/examples/c++/insertppm"    
  else
    echo "$PROG: Error: Failed to compile insertppm."
    exit 1
  fi
fi

# does $IMAGEDIR point to a good directory?
if [ ! -d $IMAGEDIR ]
then
	echo "$PROG: Illegal package path $IMAGEDIR."
	exit 1
fi

# insert images
echo -n "MERIS..."
for i in $IMAGEDIR/mosaic_ENVISAT-MER_FRS_*.ppm;
do
  $INSERTPPM $INSERTPPM_ARGS --type color --collection MERIS $i || exit 1
done

echo "$PROG: done."

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
  echo "Example: $0 localhost 7001 . rasadmin rasadmin"
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

# is insertppm available?
if [ -f /usr/bin/insertppm ]
then
  INSERTPPM="/usr/bin/insertppm"
else
  echo "$PROG: insertppm not found."
  exit 1
fi

# does $IMAGEDIR point to a good directory?
if [ ! -d $IMAGEDIR ]
then
	echo "$PROG: Illegal package path $IMAGEDIR."
	exit 1
fi

# insert images
echo "MERIS..."
$INSERTPPM $INSERTPPM_ARGS --type color --collection MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced $IMAGEDIR/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.ppm || exit 1
$INSERTPPM $INSERTPPM_ARGS --type color --collection MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced $IMAGEDIR/mosaic_ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced.ppm || exit 1
$INSERTPPM $INSERTPPM_ARGS --type color --collection MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced $IMAGEDIR/mosaic_ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced.ppm || exit 1

echo "$PROG: done."

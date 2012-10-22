#-------------------------------------------------------------------------------
# $Id: mosaic.py 1296 2012-02-15 14:18:44Z krauses $
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
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

CC= gcc
LD= gcc
LD_SHARED = $(LD) -shared 

INCLUDES=`gdal-config --cflags`
#CCFLAGS= -c -g -DDEBUG=1 -Wall -fPIC $(INCLUDES)
CCFLAGS= -c -O2 -Wall -fPIC $(INCLUDES)

LIBS=`gdal-config --libs`

OBJS= reftools.o

EXE_LIST= reftools

# --------------------------------------------

all: $(EXE_LIST) clean

%.o: %.c
	$(CC) $< $(CCFLAGS) -o $@

reftools: $(OBJS)
	$(LD_SHARED) -Wl,-soname,_reftools.so -o _reftools.so $(OBJS) $(LIBS) 

clean:
	rm *.o


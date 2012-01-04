#-------------------------------------------------------------------------------
# $Id: getcov.py 1051 2012-01-03 15:52:45Z krauses $
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

import os
import os.path
from subprocess import call
from cStringIO import StringIO

import logging

from eoxserver.core.system import System
from eoxserver.core.readers import ConfigReaderInterface
from eoxserver.core.exceptions import EngineError

def convert_format(src_path, dst_path, format=None):
    gpt_path = NESTConfigReader().getGPTPath()
    graph_path = os.path.join(
        os.path.dirname(os.path.abspath(__FILE__)),
        "Convert.xml"
    )
    
    args = [
        gpt_path,
        graph_path,
        "-Ssource=%s" % src_path,
        "-t %s" % dst_path
    ]
    
    if format is not None:
        args.append("-f %s" % format)
    
    err_str = StringIO()
    
    returncode = call(args, stderr=err_str)
    
    if returncode:
        logging.error(err_str.getvalue())
        
        err_str.close()
        
        raise EngineError(
            "NEST Error: could not convert format."
        )
    else:
        err_str.close()

def create_geo_subset(src_path, dst_path, srid, extent, format=None):
    pass

def create_pixel_subset(src_path, dst_path, extent, format=None):
    pass

class NESTConfigReader(object):
    def validate(self, config):
        pass
    
    def getGPTPath(self):
        return System.getConfig().getConfigValue("processing.nest.gpt", "gpt_path")

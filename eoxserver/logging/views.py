#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

import os.path
import logging
import re

from django.shortcuts import render_to_response
from django.template import RequestContext

from eoxserver.core.system import System
from eoxserver import get_version

LEVELS = [None, "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]

def logview(request):
    System.init()
    logfile_path = System.getConfig().getConfigValue("core.system", "logging_filename")
    logfile_path = os.path.abspath(logfile_path)
    
    count_logs = int(request.GET.get("count", 50))
    level = request.GET.get("level")
    if level not in LEVELS:
        level = LEVELS[1]
    
    with open(logfile_path) as f:
        if level is not None:
            rex = re.compile(r".*\[(%s)\].*" % "|".join(LEVELS[LEVELS.index(level):]),
                             re.IGNORECASE)
            lines = [line for line in f if rex.match(line)]
        else:
            lines = f.readlines()
        
    return render_to_response(
        'logging/logview.html',
        {
            "lines": lines[-count_logs:],
            "version": get_version(),
        },
        context_instance=RequestContext(request)
    )

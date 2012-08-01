#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

"""
This module contains utility functions for file operations.
"""

import sys
import os
import os.path
import tempfile 
from fnmatch import fnmatch

from eoxserver.core.exceptions import InternalError

def findFiles(dir, pattern):
    """
    This function mimicks the behaviour of the ``find`` shell command.
    It expects a directory path ``dir`` and a file name pattern
    ``pattern`` which may contain wildcards as accepted by the
    :func:`fnmatch.fnmatch` function. It returns a list of paths to
    matching files in ``dir`` and its subdirectories.
    
    If ``dir`` does not exist or does not point to a directory or if no
    matching files are found an empty list is returned.
    
    Directories and files whose name starts with "." are omitted.
    """
    filenames = []
    
    if os.path.exists(dir) and os.path.isdir(dir):
        for path in os.listdir(dir):
            if not path.startswith("."):
                if os.path.isdir(os.path.join(dir, path)):
                    filenames.extend(findFiles(os.path.join(dir, path), pattern))
                elif fnmatch(path, pattern):
                    filenames.append(os.path.join(dir, path))
    
    return filenames

def pathToModuleName(path):
    """
    This function takes a module path ``path`` as argument and returns
    the corresponding dotted name of the module.
    """
    
    module_name = [os.path.splitext(os.path.basename(path))[0]]
    tmp_path = os.path.abspath(os.path.dirname(path))
    
    search_paths = [dir for dir in sys.path]
    if '' in search_paths:
        search_paths.remove('')
        search_paths.append(os.getcwd())
    
    while tmp_path != "/" and tmp_path not in search_paths:
        tmp_path, name = os.path.split(tmp_path)
        module_name.append(name)
        
    if tmp_path == "/":
        raise InternalError("'%s' not on Python path." % path)
    else:
        return ".".join(reversed(module_name))


class TmpFile : 
    """ temporary file object - ``with - as`` statement friendly """  
    
    def __init__( self , suffix , prefix = "" ) : 
        _ , self.__fname = tempfile.mkstemp(suffix,prefix)

    def __str__( self ) :
        """Converts class to name of the temporary file.""" 
        return self.__fname

    def __enter__( self ) :
        """Begin of ``with - as`` block - returns name of the temporary file.""" 
        return self.__fname 

    def __exit__( self , type, value, traceback) :
        """End of ``with - as`` block - discards the temporary file.""" 
        os.remove(self.__fname)

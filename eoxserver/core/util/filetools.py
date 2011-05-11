#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import sys
import os
import os.path
from fnmatch import fnmatch

from eoxserver.core.exceptions import InternalError

def findFiles(dir, pattern):
    filenames = []
    
    for path in os.listdir(dir):
        if os.path.isdir(os.path.join(dir, path)):
            filenames.extend(findFiles(os.path.join(dir, path), pattern))
        elif fnmatch(path, pattern):
            filenames.append(os.path.join(dir, path))
    
    return filenames

def pathToModuleName(path):
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

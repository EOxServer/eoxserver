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

from copy import deepcopy

class CoverageSet(object):
    def __init__(self, seq=[]):
        """
        Initialize the :class:`CoverageSet`, optionally with 
        a sequence of coverages.
        """
        self._coverages = {}
        self.union(seq)
            
    def add(self, item):
        """
        Add a coverage to the set. The coverage is only added 
        if the EO ID is not yet present in the set. 
        """
        id = item.getCoverageId()
        if id in self._coverages:
            return
        self._coverages[id] = item
        
    def remove(self, item):
        """
        Remove a coverage with the EO ID from the set.
        """
        del self._coverages[item.getCoverageId()]
    
    def union(self, seq):
        for coverage in seq:
            self.add(coverage)
    
    def __iter__(self):
        """
        Return an iterator for the coverages.
        """
        return self._coverages.itervalues()
    
    def to_sorted_list(self):
        """
        Return a list of all contained coverages
        sorted by the coverage IDs.
        """
        keys = self._coverages.keys()
        keys.sort()
        return map(self._coverages.get, keys)

    def __contains__(self, item):
        """
        For `in` operator.
        """
        return item.getCoverageId() in self._coverages

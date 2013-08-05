#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
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

from django.db import models


class Storage(models.Model):
    url = models.CharField(max_length=1024)
    storage_type = models.CharField(max_length=32)
    
    def __unicode__(self):
        return "%s: %s" % (self.storage_type, self.url)


class BaseLocation(models.Model):
    # base type for everything that describes a locateable object
    location = models.CharField(max_length=64)
    format = models.CharField(max_length=32, null=True, blank=True)
    
    storage = models.ForeignKey(Storage, null=True, blank=True)


    class Meta:
        abstract = True

    def __unicode__(self):
        if self.format:
            return "%s (%s)" % (self.location, self.format)
        return self.location


class Package(BaseLocation):
    # for "packaged" data, like ZIP, TAR, SAFE packages or files like netCDF/HDF
    package = models.ForeignKey("self", related_name="pakages", null=True, blank=True)


class Dataset(BaseLocation):
    package = models.ForeignKey(Package, related_name="datasets", null=True, blank=True)


class DataItem(BaseLocation):
    # for extra locations
    # e.g: if a coverage consists of multiple files (each band in a single file)

    dataset = models.ForeignKey(Dataset, related_name="data_items")
    package = models.ForeignKey(Package, related_name="data_items", null=True, blank=True)
    semantic = models.CharField(max_length=64)

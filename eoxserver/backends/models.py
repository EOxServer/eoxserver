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

from django.db import models
from eoxserver.backends.validators import validate_path

class Storage(models.Model):
    """
    This class describes the storage facility a collection of data is
    stored on. Fields:
    
    * ``storage_type``: a string denoting the storage type
    * ``name``: a string denoting the name of the storage
    """
    storage_type = models.CharField(max_length=32, editable=False)
    name = models.CharField(max_length=256)
    
    def save(self, *args, **kwargs):
        self.storage_type = self.STORAGE_TYPE
        super(Storage, self).save(*args, **kwargs)

class FTPStorage(Storage):
    """
    This class describes an FTP repository. It inherits from
    :class:`Storage`. Additional fields:
    
    * ``host``: the host name
    * ``port`` (optional): the port number
    * ``user`` (optional): the user name to use
    * ``passwd`` (optional): the password to use
    """
    
    STORAGE_TYPE = "ftp"
    
    host = models.CharField(max_length=1024)
    port = models.IntegerField(null=True, blank=True)
    user = models.CharField(max_length=1024, null=True, blank=True)
    passwd = models.CharField(max_length=128, null=True, blank=True)
    
class RasdamanStorage(Storage):
    """
    This class describes a rasdaman database access. It inherits from
    :class:`Storage`. Additional fields:
    
    * ``host``: the host name
    * ``port`` (optional): the port number
    * ``user`` (optional): the user name to use
    * ``passwd`` (optional): the password to use
    """
    
    STORAGE_TYPE = "rasdaman"
    
    host = models.CharField(max_length=1024)
    port = models.IntegerField(null=True, blank=True)
    user = models.CharField(max_length=1024, null=True, blank=True)
    passwd = models.CharField(max_length=128, null=True, blank=True)
    db_name = models.CharField(max_length=128, null=True, blank=True)

class Location(models.Model):
    """
    :class:`Location` is the base class for describing the physical or
    logical location of a (general) resource relative to some storage.
    Fields:
    
    * ``location_type``: a string denoting the type of location
    """
    location_type = models.CharField(max_length=32, editable=False)
    
    def __unicode__(self):
        if self.location_type == "local":
            return self.localpath.path
        elif self.location_type == "rasdaman":
            return "rasdaman:%s:%s" % (self.rasdamanlocation.collection, self.rasdamanlocation.oid)
        elif self.location_type == "ftp":
            return "ftp://%s/%s" % (self.remotepath.storage.host, self.remotepath.path)
        else:
            return "Unknown location type"
        
    def save(self, *args, **kwargs):
        self.location_type = self.LOCATION_TYPE
        super(Location, self).save(*args, **kwargs)
    
class LocalPath(Location):
    """
    :class:`LocalPath` describes a path on the local file system. It
    inherits from :class:`Location`. Fields:
    
    * ``path``: a path on the local file system
    """
    LOCATION_TYPE = "local"
    
    path = models.CharField(max_length=1024, validators=[validate_path])
    
class RemotePath(Location):
    """
    :class:`RemotePath` describes a path on an FTP repository. It
    inherits from :class:`Location`. Fields:
    
    * ``storage``: a foreign key of an :class:`FTPStorage` entry.
    * ``path``: path on the repository
    """
    
    LOCATION_TYPE = "ftp"
    
    storage = models.ForeignKey(FTPStorage, related_name="paths")
    path = models.CharField(max_length=1024)
    
class RasdamanLocation(Location):
    """
    :class:`RasdamanLocation` describes the parameters for accessing a
    rasdaman array. It inherits from :class:`Location`. Fields:
    
    * ``storage``: a foreign key of a :class:`RasdamanStorage` entry
    * ``collection``: name of the rasdaman collection that contains the
      array
    * ``oid``: rasdaman OID of the array (note that this is a float)
    """
    
    LOCATION_TYPE = "rasdaman"
    
    storage = models.ForeignKey(RasdamanStorage, related_name="rasdaman_locations")
    collection = models.CharField(max_length=1024)  # comparable to table
    oid = models.FloatField(null=True, blank=True) # float due to rasdaman architecture; comparable to array
    
class CacheFile(models.Model):
    """
    :class:`CacheFile` stores the whereabouts of a file held in the
    cache. Fields:
    
    * ``location``: a link to a :class:`LocalPath` denoting the path
      to the cached file
    * ``size``: the size of the file in bytes, null if it is not known
    * ``access_timestamp``: the time of the last access
    """

    location = models.ForeignKey(LocalPath, related_name="cache_files")
    size = models.IntegerField(null=True)
    access_timestamp = models.DateTimeField()

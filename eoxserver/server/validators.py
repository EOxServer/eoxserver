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

import os.path
from lxml import etree

from django.conf import settings
from django.core.exceptions import ValidationError

class EOxSEOOMSchema(object):
    SCHEMA_LOCATION = os.path.join(settings.PROJECT_DIR, "..", "schemas", "omeo", "eop.xsd")
    schema = None
    
    @classmethod
    def getSchema(cls):
        if cls.schema is None:
            f = open(cls.SCHEMA_LOCATION)
            cls.schema = etree.XMLSchema(etree.parse(f))
            f.close()
        
        return cls.schema
        
def validateEOOM(xml):
    schema = EOxSEOOMSchema.getSchema()
    
    try:
        schema.assertValid(etree.fromstring(xml))
    except etree.Error as e:
        raise ValidationError(str(e))

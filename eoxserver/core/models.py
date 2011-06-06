#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
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

from django.db import models
from django.contrib.contenttypes.models import ContentType
    
class Implementation(models.Model):
    intf_id = models.CharField(max_length=256)
    impl_id = models.CharField(max_length=256, unique=True)

class Component(Implementation):
    enabled = models.BooleanField(default=False)

class ResourceClass(Implementation):
    content_type = models.ForeignKey(ContentType)
    
class Resource(models.Model):
    pass

class Relation(models.Model):
    rel_class = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)

    subj = models.ForeignKey(Component, related_name="relations")

    obj = models.ForeignKey(Resource, related_name="relations")

class ClassRelation(models.Model):
    rel_class = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)
    
    subj = models.ForeignKey(Component, related_name="class_relations")
    
    obj = models.ForeignKey(ResourceClass, related_name="class_relations")

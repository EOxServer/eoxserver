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

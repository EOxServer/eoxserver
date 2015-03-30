#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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


from optparse import make_option

from django.core.management.base import CommandError, BaseCommand

from eoxserver.resources.coverages import models

INDENT="  "

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-t", "--type", 
            dest="type_name", action="store", default="EOObject",
            help=("Optional. Restrict the listed identifiers to given type.")
        ),
        make_option("-r", "--recursive",
            dest="recursive", action="store_true", default=False,
            help=("Optional. Recursive listing for collections.")
        ),
    )

    args = "[<id> [<id> ...]] [-t <type>] [-r]"

    help = """ 
        Print a list of all objects in the database. Alternatively the list 
        can be filtered by a give set of identifiers or a given object type.

        The listing can also be done recursively with the `-r` option
    """

    def handle(self, *identifiers, **kwargs):
        type_name = kwargs["type_name"]

        try:
            # TODO: allow types residing in different apps
            ObjectType = getattr(models, type_name)
            if not issubclass(ObjectType, models.EOObject):
                raise CommandError("Unsupported type '%s'." % type_name)
        except AttributeError:
            raise CommandError("Unsupported type '%s'." % type_name)

        eo_objects = ObjectType.objects.all()

        if identifiers:
            eo_objects = eo_objects.filter(identifier__in=identifiers)

        for eo_object in eo_objects:
            self.print_object(eo_object, kwargs["recursive"])


    def print_object(self, eo_object, recursive=False, level=0):
        indent = INDENT * level
        eo_object = eo_object.cast()
        print("%s%s %s" % (indent, eo_object.identifier,
                                eo_object.__class__.__name__))

        if recursive and models.iscollection(eo_object):
            for sub_eo_object in eo_object.eo_objects.all():
                self.print_object(sub_eo_object, recursive, level+1)

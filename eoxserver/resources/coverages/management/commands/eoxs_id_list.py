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

from inspect import isclass
from django.core.management.base import CommandError, BaseCommand
from eoxserver.resources.coverages import models

INDENT = "  "


class Command(BaseCommand):

    help = """
        Print a list of all objects in the database. Alternatively the list
        can be filtered by a give set of identifiers or a given object type.

        The listing can also be done recursively with the `-r` option
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("identifier", nargs="*")
        parser.add_argument(
            "-t", "--type", dest="type_name", default="EOObject",
            help="Optional. Restrict the listed identifiers to given type."
        )
        parser.add_argument(
            "-r", "--recursive", dest="recursive", action="store_true",
            default=False, help="Optional. Recursive listing for collections."
        )
        parser.add_argument(
            "-s", "--suppress-type", dest="suppress_type", action="store_true",
            default=False, help=(
                "Optional. Suppress the output of the type. By default, the "
                "type is also printed after the identifier."
            )
        )

    def handle(self, *args, **kwargs):
        identifiers = kwargs["identifier"]
        type_name = kwargs["type_name"]
        suppress_type = kwargs["suppress_type"]

        eo_models = collect_eoobj_types()
        try:
            eo_model = eo_models[type_name]
        except KeyError:
            raise CommandError("Unsupported type '%s'." % type_name)

        eo_objects = eo_model.objects
        if identifiers:
            eo_objects = eo_objects.filter(identifier__in=identifiers)
        else:
            eo_objects = eo_objects.all()

        for eo_object in eo_objects:
            self.print_object(eo_object, kwargs["recursive"], suppress_type)


    def print_object(self, eo_object, recursive=False, suppress_type=False,
                     level=0):
        indent = INDENT * level
        eo_object = eo_object.cast()
        if not suppress_type:
            print("%s%s %s" % (indent, eo_object.identifier,
                               eo_object.__class__.__name__))
        else:
            print("%s%s" % (indent, eo_object.identifier))

        if recursive and models.iscollection(eo_object):
            for sub_eo_object in eo_object.eo_objects.all():
                self.print_object(
                    sub_eo_object, recursive, suppress_type, level+1
                )


def collect_eoobj_types():
    """ Collect all available EOObject type into a name->class map. """

    def _collect_obobj_models():
        for model in models.EO_OBJECT_TYPE_REGISTRY.values():
            yield model

        for name in dir(models):
            if not name.startswith("__"):
                model = getattr(models, name)
                if isclass(model) and issubclass(model, models.EOObject):
                    yield model

    def _collect_eoobj_types():
        for model in _collect_obobj_models():
            yield (model.__name__, model)
            yield ("%s.%s" % (model.__module__, model.__name__), model)

    return {name: model for name, model in _collect_eoobj_types()}

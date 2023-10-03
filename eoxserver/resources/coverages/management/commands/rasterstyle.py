# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction
from lxml import etree

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage product types. This command uses sub-commands for the
        specific tasks: create, delete
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        import_parser = self.add_subparser(parser, 'import')
        delete_parser = self.add_subparser(parser, 'delete')
        list_parser = self.add_subparser(parser, 'list')
        link_parser = self.add_subparser(parser, 'link')

        for parser in [create_parser, delete_parser, link_parser]:
            parser.add_argument(
                'name', nargs=1, help='The raster style name. Mandatory.'
            )

        create_parser.add_argument(
            '--type', '-t', action="store", default="ramp",
            choices=["ramp", "values", "intervals"],
            help="Specify this raster style type"
        )
        create_parser.add_argument(
            '--title', action="store",
            help="Specify this raster style title"
        )
        create_parser.add_argument(
            '--abstract', action="store",
            help="Specify this raster style abstract"
        )
        create_parser.add_argument(
            '--color-entry', '-c',
            action='append', dest='color_entries', default=[], nargs=4,
            help=(
                "A color style entry. Must consist of <value>, <color>, "
                "<opacity>, <label>"
            )
        )

        import_parser.add_argument(
            'filename', nargs=1, help='The SLD file name. Mandatory.'
        )
        import_parser.add_argument(
            '--select', '-s',
            action='append', dest='selects', default=[], nargs=1,
            help="Select a style to import"
        )
        import_parser.add_argument(
            '--rename', '-r',
            action='append', dest='renames', default=[], nargs=2,
            help="Rename a style from a name to another name"
        )

        link_parser.add_argument(
            'product_type_name', nargs=1, help=''
        )
        link_parser.add_argument(
            'browse_type_name', nargs=1, help=''
        )
        link_parser.add_argument(
            'style_name', nargs=1, help=''
        )

        for parser in [create_parser, import_parser]:
            parser.add_argument(
                '--replace', action='store_true',
                default=False,
                help=('''Change raster style if already exists.''')
            )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: create, delete, list, link.
        """
        if subcommand == "create":
            self.handle_create(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "import":
            self.handle_import(kwargs.pop('filename')[0], *args, **kwargs)
        elif subcommand == "delete":
            self.handle_delete(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "list":
            self.handle_list(*args, **kwargs)
        elif subcommand == "link":
            style_name = kwargs.pop('style_name')
            self.handle_link(
                kwargs.pop('name')[0],
                kwargs.pop('product_type_name')[0],
                kwargs.pop('browse_type_name')[0],
                style_name[0] if style_name else None,
                *args, **kwargs
            )

    def handle_create(self, name, type, title, abstract, color_entries, replace, *args, **kwargs):
        """ Handle the creation of a new raster style.
        """
        if replace:
            raster_style = models.RasterStyle.objects.update_or_create(
                name=name,
                defaults={
                    'type': type,
                    'title': title,
                    'abstract': abstract,
                },
            )[0]
        else:
            raster_style = models.RasterStyle.objects.create(
                name=name,
                type=type,
                title=title,
                abstract=abstract,
            )

        if not color_entries:
            raise CommandError("No color entries specified")
        first_iteration = True
        for value, color, opacity, label in color_entries:
            if replace and first_iteration:
                raster_style_color_entries_existing = models.RasterStyleColorEntry.objects.filter(
                    raster_style=raster_style,
                )
                raster_style_color_entries_existing.delete()
                first_iteration = False
            entry = models.RasterStyleColorEntry(
                raster_style=raster_style,
                value=float(value),
                color=color,
                opacity=float(opacity),
                label=label,
            )
            entry.full_clean()
            entry.save()

        print('Successfully created raster style %r' % name)

    def handle_import(self, filename, selects, renames, replace, *args, **kwargs):
        tree = etree.parse(filename)
        nsmap = {
            "sld": "http://www.opengis.net/sld",
            "se": "http://www.opengis.net/se",
        }
        user_styles = tree.xpath(
            "(sld:NamedLayer|sld:UserLayer)/sld:UserStyle", namespaces=nsmap
        )
        selects = [s[0] for s in selects]
        renames = dict(renames)
        count = 0
        for user_style in user_styles:
            name = user_style.xpath("(se:Name|sld:Name)/text()", namespaces=nsmap)[0]
            if selects and name not in selects:
                continue

            name = renames.get(name, name)
            color_map = user_style.xpath(
                "(se:FeatureTypeStyle/se:Rule/se:RasterSymbolizer/se:ColorMap|"
                "sld:FeatureTypeStyle/sld:Rule/sld:RasterSymbolizer/sld:ColorMap)",
                namespaces=nsmap,
            )[0]
            if replace:
                raster_style = models.RasterStyle.objects.update_or_create(
                    name=name,
                    defaults={
                        'type': color_map.get("type", "ramp"),
                    },
                )
            else:
                raster_style = models.RasterStyle.objects.create(
                    name=name, type=color_map.get("type", "ramp")
                )

            color_map_entries = color_map.xpath(
                "sld:ColorMapEntry", namespaces=nsmap
            )
            first_iteration = True
            for color_map_entry in color_map_entries:
                if replace and first_iteration:
                    raster_style_color_entries_existing = models.RasterStyleColorEntry.objects.filter(
                        raster_style=raster_style,
                    )
                    raster_style_color_entries_existing.delete()
                    first_iteration = False
                entry = models.RasterStyleColorEntry(
                    raster_style=raster_style,
                    value=float(color_map_entry.get("quantity")),
                    color=color_map_entry.get("color"),
                    label=color_map_entry.get("label"),
                )
                entry.full_clean()
                entry.save()

            count += 1
            print('Successfully created raster style %r' % name)

        if not count:
            raise CommandError("No raster styles were imported")
        print("Successfully imported %d raster styles" % count)

    def handle_delete(self, name, **kwargs):
        """ Handle the deletion of a raster style
        """

        try:
            raster_style = models.RasterStyle.objects.get(name=name)
        except models.RasterStyle.DoesNotExist:
            raise CommandError('No such raster style %r' % name)

        raster_style.delete()
        print('Successfully deleted raster style %r' % name)

    def handle_list(self, *args, **kwargs):
        """ Handle the listing of raster styles
        """
        for raster_style in models.RasterStyle.objects.all():
            print(raster_style.name)
            for entry in raster_style.color_entries.all():
                print("\t%f: %s (%f) %s" % (
                    entry.value, entry.color, entry.opacity, entry.label
                ))

    def handle_link(self, name, product_type_name, browse_type_name, stylename,
                    *args, **kwargs):
        """ Handle the linking of raster styles to browse types
        """
        raster_style = models.RasterStyle.objects.get(name=name)
        browse_type = models.BrowseType.objects.get(
            product_type__name=product_type_name,
            name=browse_type_name
        )
        models.RasterStyleToBrowseTypeThrough.objects.get_or_create(
            raster_style=raster_style,
            browse_type=browse_type,
            style_name=stylename,
        )
        print('Successfully linked raster style %r to browse type %r/%r' % (
            name, product_type_name, browse_type_name
        ))

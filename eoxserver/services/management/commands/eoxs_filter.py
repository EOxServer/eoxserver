from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.services.ecql import parse, to_filter, get_repr
from eoxserver.services.filters import get_field_mapping_for_model


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--collection', '-c', dest='collection_id',
            help='Optional. Only list datasets in this collection.'
        ),
        make_option('--type', '-t', dest='type', default='EOObject',
            help='Optional. Limit datasets to objects of that type.'
        ),
        make_option('--exclude', '-e', dest='exclude',
            action='store_true', default=False,
            help=(
                'Optional. Reverse the lookup: instead of including the matched '
                'datasets in the result, exclude them and include everything '
                'else.'
            )
        ),
        make_option('--show-attributes', '--show', '-s', dest='show_attributes',
            action='store_true', default=False,
            help=(
                'Optional. Display the available attributes for the given '
                'record type.'
            )
        )
    )

    args = '<cql-filter>'

    help = """
        Perform a query of datasets matching the given filters expressed in CQL.
        The dataset IDs will be written to stdout.
    """

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))

        # get the model class and the field mapping (with choices)
        ModelClass = getattr(models, options.get('type'))
        mapping, mapping_choices = get_field_mapping_for_model(ModelClass)

        # print the available attributes, if requested
        if options.get('show_attributes'):
            print("\n".join(mapping.keys()))
            return

        # filter by collection, if requested
        collection_id = options.get('collection_id')
        if collection_id:
            try:
                collection = models.Collection.objects.get(
                    identifier=collection_id
                )
                qs = ModelClass.objects.filter(collections__in=[collection.pk])
            except models.Collection.DoesNotExist:
                raise CommandError('No such collection %r' % collection_id)
        else:
            qs = ModelClass.objects.all()

        if len(args) < 1:
            raise CommandError('No CQL filter passed.')

        for arg in args:
            ast = parse(arg)

            if self.verbosity >= 2:
                self.print_msg(get_repr(ast), 2)

            filters = to_filter(ast, mapping, mapping_choices)
            if not filters:
                raise CommandError('Invalid filter specified')

            if options['exclude']:
                qs = ModelClass.objects.exclude(filters)
            else:
                qs = ModelClass.objects.filter(filters)

            if self.verbosity >= 2:
                self.print_msg(filters, 2)

        qs = qs.values_list('identifier', flat=True)
        print "\n".join(qs)

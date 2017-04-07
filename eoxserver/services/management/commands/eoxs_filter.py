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
        make_option('--debug', '-d', dest="debug",
            action="store_true", default=False,
            help=(
                "Optional. Print a representation of the parsed AST of the "
                "ECQL filter."
            )
        )
    )

    args = '<cql-filter>'

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))

        if len(args) < 1:
            raise CommandError('No CQL filter passed.')

        collection_id = options.get('collection_id')

        ModelClass = getattr(models, options.get('type'))

        mapping, mapping_choices = get_field_mapping_for_model(ModelClass)

        ast = parse(args[0], mapping, mapping_choices)

        if options.get('debug'):
            print(get_repr(ast))

        filters = to_filter(ast, mapping, mapping_choices)
        if not filters:
            raise CommandError('Invalid filter specified')

        qs = ModelClass.objects.filter(filters)
        print filters

        if collection_id:
            try:
                collection = models.Collection.objects.get(
                    identifier=collection_id
                )
                # qs.
            except models.Collection.DoesNotExist:
                raise CommandError('No such collection %r' % collection_id)

        qs = qs.values_list('identifier', flat=True)
        for identifier in qs:
            print identifier


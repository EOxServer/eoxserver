import os.path
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from eoxserver.core.system import System
from eoxserver.resources.coverages.geo import GeospatialMetadata
from eoxserver.resources.coverages.metadata import EOMetadata

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--data-file',
            dest='datafile',
            help='Mandatory path to a local file containing the image data.'
        ),
        make_option('-m', '--metadata-file',
            dest='metadatafile',
            help='Optional path to a local file containing the image meta data. '
                 'Defaults to the same path as the data file with the ".xml" extension.'
        ),
        make_option('-r', '--rangetype',
            dest='rangetype',
            help='Mandatory identifier of the rangetype used in the dataset.'
        ),
        make_option('--dataset-series',
            dest='datasetseries',
            help='Optional identifier of a dataset series in which the dataset shall be added.'
        )
    )
    
    help = 'Creates a new dataset record from a data and meta-data file.'

    def handle(self, *args, **options):
        datafile = options['datafile']
        if datafile is None:
            raise CommandError("Mandatory parameter --data-file is not present.")
        
        rangetype = options['rangetype']
        if rangetype is None:
            raise CommandError("Mandatory parameter --rangetype is not present.")
        
        metadatafile = options['metadatafile']
        if metadatafile is None:
            metadatafile = os.path.splitext(datafile)[0] + '.xml'
        
        System.init()
        mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_dataset"
            }
        )
        
        args = {
            "local_path": datafile,
            "md_local_path": metadatafile,
            "range_type_name": rangetype
        }
        
        # TODO insert into dataset series
        
        mgr.create(**args)
    
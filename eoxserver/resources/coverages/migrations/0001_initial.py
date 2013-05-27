# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'NilValueRecord'
        db.create_table(u'coverages_nilvaluerecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reason', self.gf('django.db.models.fields.CharField')(default='http://www.opengis.net/def/nil/OGC/0/unknown', max_length=128)),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'coverages', ['NilValueRecord'])

        # Adding model 'BandRecord'
        db.create_table(u'coverages_bandrecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('definition', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('uom', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('gdal_interpretation', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'coverages', ['BandRecord'])

        # Adding M2M table for field nil_values on 'BandRecord'
        m2m_table_name = db.shorten_name(u'coverages_bandrecord_nil_values')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bandrecord', models.ForeignKey(orm[u'coverages.bandrecord'], null=False)),
            ('nilvaluerecord', models.ForeignKey(orm[u'coverages.nilvaluerecord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bandrecord_id', 'nilvaluerecord_id'])

        # Adding model 'RangeTypeRecord'
        db.create_table(u'coverages_rangetyperecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('data_type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'coverages', ['RangeTypeRecord'])

        # Adding model 'RangeType2Band'
        db.create_table(u'coverages_rangetype2band', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('band', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.BandRecord'])),
            ('range_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.RangeTypeRecord'])),
            ('no', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'coverages', ['RangeType2Band'])

        # Adding model 'ExtentRecord'
        db.create_table(u'coverages_extentrecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('srid', self.gf('django.db.models.fields.IntegerField')()),
            ('size_x', self.gf('django.db.models.fields.IntegerField')()),
            ('size_y', self.gf('django.db.models.fields.IntegerField')()),
            ('minx', self.gf('django.db.models.fields.FloatField')()),
            ('miny', self.gf('django.db.models.fields.FloatField')()),
            ('maxx', self.gf('django.db.models.fields.FloatField')()),
            ('maxy', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'coverages', ['ExtentRecord'])

        # Adding model 'LayerMetadataRecord'
        db.create_table(u'coverages_layermetadatarecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'coverages', ['LayerMetadataRecord'])

        # Adding model 'LineageRecord'
        db.create_table(u'coverages_lineagerecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'coverages', ['LineageRecord'])

        # Adding model 'EOMetadataRecord'
        db.create_table(u'coverages_eometadatarecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp_begin', self.gf('django.db.models.fields.DateTimeField')()),
            ('timestamp_end', self.gf('django.db.models.fields.DateTimeField')()),
            ('footprint', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')()),
            ('eo_gml', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'coverages', ['EOMetadataRecord'])

        # Adding model 'DataSource'
        db.create_table(u'coverages_datasource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_sources', to=orm['backends.Location'])),
            ('search_pattern', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
        ))
        db.send_create_signal(u'coverages', ['DataSource'])

        # Adding unique constraint on 'DataSource', fields ['location', 'search_pattern']
        db.create_unique(u'coverages_datasource', ['location_id', 'search_pattern'])

        # Adding model 'DataPackage'
        db.create_table(u'coverages_datapackage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('data_package_type', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('metadata_format_name', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal(u'coverages', ['DataPackage'])

        # Adding model 'LocalDataPackage'
        db.create_table(u'coverages_localdatapackage', (
            (u'datapackage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.DataPackage'], unique=True, primary_key=True)),
            ('data_location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_file_packages', to=orm['backends.LocalPath'])),
            ('metadata_location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='metadata_file_packages', null=True, to=orm['backends.LocalPath'])),
            ('source_format', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'coverages', ['LocalDataPackage'])

        # Adding model 'RemoteDataPackage'
        db.create_table(u'coverages_remotedatapackage', (
            (u'datapackage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.DataPackage'], unique=True, primary_key=True)),
            ('data_location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_file_packages', to=orm['backends.RemotePath'])),
            ('metadata_location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='metadata_file_packages', null=True, to=orm['backends.RemotePath'])),
            ('source_format', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('cache_file', self.gf('django.db.models.fields.related.ForeignKey')(related_name='remote_data_packages', null=True, to=orm['backends.CacheFile'])),
        ))
        db.send_create_signal(u'coverages', ['RemoteDataPackage'])

        # Adding model 'RasdamanDataPackage'
        db.create_table(u'coverages_rasdamandatapackage', (
            (u'datapackage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.DataPackage'], unique=True, primary_key=True)),
            ('data_location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_packages', to=orm['backends.RasdamanLocation'])),
            ('metadata_location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rasdaman_metadata_file_packages', null=True, to=orm['backends.LocalPath'])),
        ))
        db.send_create_signal(u'coverages', ['RasdamanDataPackage'])

        # Adding model 'TileIndex'
        db.create_table(u'coverages_tileindex', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('storage_dir', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal(u'coverages', ['TileIndex'])

        # Adding model 'ReservedCoverageIdRecord'
        db.create_table(u'coverages_reservedcoverageidrecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('until', self.gf('django.db.models.fields.DateTimeField')()),
            ('request_id', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('coverage_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
        ))
        db.send_create_signal(u'coverages', ['ReservedCoverageIdRecord'])

        # Adding model 'CoverageRecord'
        db.create_table(u'coverages_coveragerecord', (
            (u'resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Resource'], unique=True, primary_key=True)),
            ('coverage_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('range_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.RangeTypeRecord'], on_delete=models.PROTECT)),
            ('automatic', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('data_source', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='coveragerecord_set', null=True, on_delete=models.SET_NULL, to=orm['coverages.DataSource'])),
        ))
        db.send_create_signal(u'coverages', ['CoverageRecord'])

        # Adding M2M table for field layer_metadata on 'CoverageRecord'
        m2m_table_name = db.shorten_name(u'coverages_coveragerecord_layer_metadata')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('coveragerecord', models.ForeignKey(orm[u'coverages.coveragerecord'], null=False)),
            ('layermetadatarecord', models.ForeignKey(orm[u'coverages.layermetadatarecord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['coveragerecord_id', 'layermetadatarecord_id'])

        # Adding model 'PlainCoverageRecord'
        db.create_table(u'coverages_plaincoveragerecord', (
            (u'coveragerecord_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.CoverageRecord'], unique=True, primary_key=True)),
            ('extent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='single_file_coverages', to=orm['coverages.ExtentRecord'])),
            ('data_package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plain_coverages', to=orm['coverages.DataPackage'])),
        ))
        db.send_create_signal(u'coverages', ['PlainCoverageRecord'])

        # Adding model 'RectifiedDatasetRecord'
        db.create_table(u'coverages_rectifieddatasetrecord', (
            (u'coveragerecord_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.CoverageRecord'], unique=True, primary_key=True)),
            ('eo_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('eo_metadata', self.gf('django.db.models.fields.related.OneToOneField')(related_name='rectifieddatasetrecord_set', unique=True, to=orm['coverages.EOMetadataRecord'])),
            ('lineage', self.gf('django.db.models.fields.related.OneToOneField')(related_name='rectifieddatasetrecord_set', unique=True, to=orm['coverages.LineageRecord'])),
            ('data_package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rectifieddatasetrecord_set', to=orm['coverages.DataPackage'])),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('extent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rect_datasets', to=orm['coverages.ExtentRecord'])),
        ))
        db.send_create_signal(u'coverages', ['RectifiedDatasetRecord'])

        # Adding model 'ReferenceableDatasetRecord'
        db.create_table(u'coverages_referenceabledatasetrecord', (
            (u'coveragerecord_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.CoverageRecord'], unique=True, primary_key=True)),
            ('eo_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('eo_metadata', self.gf('django.db.models.fields.related.OneToOneField')(related_name='referenceabledatasetrecord_set', unique=True, to=orm['coverages.EOMetadataRecord'])),
            ('lineage', self.gf('django.db.models.fields.related.OneToOneField')(related_name='referenceabledatasetrecord_set', unique=True, to=orm['coverages.LineageRecord'])),
            ('data_package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='referenceabledatasetrecord_set', to=orm['coverages.DataPackage'])),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('extent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='refa_datasets', to=orm['coverages.ExtentRecord'])),
        ))
        db.send_create_signal(u'coverages', ['ReferenceableDatasetRecord'])

        # Adding model 'RectifiedStitchedMosaicRecord'
        db.create_table(u'coverages_rectifiedstitchedmosaicrecord', (
            (u'coveragerecord_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.CoverageRecord'], unique=True, primary_key=True)),
            ('eo_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('eo_metadata', self.gf('django.db.models.fields.related.OneToOneField')(related_name='rectifiedstitchedmosaicrecord_set', unique=True, to=orm['coverages.EOMetadataRecord'])),
            ('lineage', self.gf('django.db.models.fields.related.OneToOneField')(related_name='rectifiedstitchedmosaicrecord_set', unique=True, to=orm['coverages.LineageRecord'])),
            ('extent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rect_stitched_mosaics', to=orm['coverages.ExtentRecord'])),
            ('tile_index', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rect_stitched_mosaics', to=orm['coverages.TileIndex'])),
        ))
        db.send_create_signal(u'coverages', ['RectifiedStitchedMosaicRecord'])

        # Adding M2M table for field data_sources on 'RectifiedStitchedMosaicRecord'
        m2m_table_name = db.shorten_name(u'coverages_rectifiedstitchedmosaicrecord_data_sources')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rectifiedstitchedmosaicrecord', models.ForeignKey(orm[u'coverages.rectifiedstitchedmosaicrecord'], null=False)),
            ('datasource', models.ForeignKey(orm[u'coverages.datasource'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rectifiedstitchedmosaicrecord_id', 'datasource_id'])

        # Adding M2M table for field rect_datasets on 'RectifiedStitchedMosaicRecord'
        m2m_table_name = db.shorten_name(u'coverages_rectifiedstitchedmosaicrecord_rect_datasets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rectifiedstitchedmosaicrecord', models.ForeignKey(orm[u'coverages.rectifiedstitchedmosaicrecord'], null=False)),
            ('rectifieddatasetrecord', models.ForeignKey(orm[u'coverages.rectifieddatasetrecord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rectifiedstitchedmosaicrecord_id', 'rectifieddatasetrecord_id'])

        # Adding model 'DatasetSeriesRecord'
        db.create_table(u'coverages_datasetseriesrecord', (
            (u'resource_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Resource'], unique=True, primary_key=True)),
            ('eo_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('eo_metadata', self.gf('django.db.models.fields.related.OneToOneField')(related_name='dataset_series_set', unique=True, to=orm['coverages.EOMetadataRecord'])),
        ))
        db.send_create_signal(u'coverages', ['DatasetSeriesRecord'])

        # Adding M2M table for field data_sources on 'DatasetSeriesRecord'
        m2m_table_name = db.shorten_name(u'coverages_datasetseriesrecord_data_sources')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('datasetseriesrecord', models.ForeignKey(orm[u'coverages.datasetseriesrecord'], null=False)),
            ('datasource', models.ForeignKey(orm[u'coverages.datasource'], null=False))
        ))
        db.create_unique(m2m_table_name, ['datasetseriesrecord_id', 'datasource_id'])

        # Adding M2M table for field rect_stitched_mosaics on 'DatasetSeriesRecord'
        m2m_table_name = db.shorten_name(u'coverages_datasetseriesrecord_rect_stitched_mosaics')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('datasetseriesrecord', models.ForeignKey(orm[u'coverages.datasetseriesrecord'], null=False)),
            ('rectifiedstitchedmosaicrecord', models.ForeignKey(orm[u'coverages.rectifiedstitchedmosaicrecord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['datasetseriesrecord_id', 'rectifiedstitchedmosaicrecord_id'])

        # Adding M2M table for field rect_datasets on 'DatasetSeriesRecord'
        m2m_table_name = db.shorten_name(u'coverages_datasetseriesrecord_rect_datasets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('datasetseriesrecord', models.ForeignKey(orm[u'coverages.datasetseriesrecord'], null=False)),
            ('rectifieddatasetrecord', models.ForeignKey(orm[u'coverages.rectifieddatasetrecord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['datasetseriesrecord_id', 'rectifieddatasetrecord_id'])

        # Adding M2M table for field ref_datasets on 'DatasetSeriesRecord'
        m2m_table_name = db.shorten_name(u'coverages_datasetseriesrecord_ref_datasets')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('datasetseriesrecord', models.ForeignKey(orm[u'coverages.datasetseriesrecord'], null=False)),
            ('referenceabledatasetrecord', models.ForeignKey(orm[u'coverages.referenceabledatasetrecord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['datasetseriesrecord_id', 'referenceabledatasetrecord_id'])

        # Adding M2M table for field layer_metadata on 'DatasetSeriesRecord'
        m2m_table_name = db.shorten_name(u'coverages_datasetseriesrecord_layer_metadata')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('datasetseriesrecord', models.ForeignKey(orm[u'coverages.datasetseriesrecord'], null=False)),
            ('layermetadatarecord', models.ForeignKey(orm[u'coverages.layermetadatarecord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['datasetseriesrecord_id', 'layermetadatarecord_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'DataSource', fields ['location', 'search_pattern']
        db.delete_unique(u'coverages_datasource', ['location_id', 'search_pattern'])

        # Deleting model 'NilValueRecord'
        db.delete_table(u'coverages_nilvaluerecord')

        # Deleting model 'BandRecord'
        db.delete_table(u'coverages_bandrecord')

        # Removing M2M table for field nil_values on 'BandRecord'
        db.delete_table(db.shorten_name(u'coverages_bandrecord_nil_values'))

        # Deleting model 'RangeTypeRecord'
        db.delete_table(u'coverages_rangetyperecord')

        # Deleting model 'RangeType2Band'
        db.delete_table(u'coverages_rangetype2band')

        # Deleting model 'ExtentRecord'
        db.delete_table(u'coverages_extentrecord')

        # Deleting model 'LayerMetadataRecord'
        db.delete_table(u'coverages_layermetadatarecord')

        # Deleting model 'LineageRecord'
        db.delete_table(u'coverages_lineagerecord')

        # Deleting model 'EOMetadataRecord'
        db.delete_table(u'coverages_eometadatarecord')

        # Deleting model 'DataSource'
        db.delete_table(u'coverages_datasource')

        # Deleting model 'DataPackage'
        db.delete_table(u'coverages_datapackage')

        # Deleting model 'LocalDataPackage'
        db.delete_table(u'coverages_localdatapackage')

        # Deleting model 'RemoteDataPackage'
        db.delete_table(u'coverages_remotedatapackage')

        # Deleting model 'RasdamanDataPackage'
        db.delete_table(u'coverages_rasdamandatapackage')

        # Deleting model 'TileIndex'
        db.delete_table(u'coverages_tileindex')

        # Deleting model 'ReservedCoverageIdRecord'
        db.delete_table(u'coverages_reservedcoverageidrecord')

        # Deleting model 'CoverageRecord'
        db.delete_table(u'coverages_coveragerecord')

        # Removing M2M table for field layer_metadata on 'CoverageRecord'
        db.delete_table(db.shorten_name(u'coverages_coveragerecord_layer_metadata'))

        # Deleting model 'PlainCoverageRecord'
        db.delete_table(u'coverages_plaincoveragerecord')

        # Deleting model 'RectifiedDatasetRecord'
        db.delete_table(u'coverages_rectifieddatasetrecord')

        # Deleting model 'ReferenceableDatasetRecord'
        db.delete_table(u'coverages_referenceabledatasetrecord')

        # Deleting model 'RectifiedStitchedMosaicRecord'
        db.delete_table(u'coverages_rectifiedstitchedmosaicrecord')

        # Removing M2M table for field data_sources on 'RectifiedStitchedMosaicRecord'
        db.delete_table(db.shorten_name(u'coverages_rectifiedstitchedmosaicrecord_data_sources'))

        # Removing M2M table for field rect_datasets on 'RectifiedStitchedMosaicRecord'
        db.delete_table(db.shorten_name(u'coverages_rectifiedstitchedmosaicrecord_rect_datasets'))

        # Deleting model 'DatasetSeriesRecord'
        db.delete_table(u'coverages_datasetseriesrecord')

        # Removing M2M table for field data_sources on 'DatasetSeriesRecord'
        db.delete_table(db.shorten_name(u'coverages_datasetseriesrecord_data_sources'))

        # Removing M2M table for field rect_stitched_mosaics on 'DatasetSeriesRecord'
        db.delete_table(db.shorten_name(u'coverages_datasetseriesrecord_rect_stitched_mosaics'))

        # Removing M2M table for field rect_datasets on 'DatasetSeriesRecord'
        db.delete_table(db.shorten_name(u'coverages_datasetseriesrecord_rect_datasets'))

        # Removing M2M table for field ref_datasets on 'DatasetSeriesRecord'
        db.delete_table(db.shorten_name(u'coverages_datasetseriesrecord_ref_datasets'))

        # Removing M2M table for field layer_metadata on 'DatasetSeriesRecord'
        db.delete_table(db.shorten_name(u'coverages_datasetseriesrecord_layer_metadata'))


    models = {
        u'backends.cachefile': {
            'Meta': {'object_name': 'CacheFile'},
            'access_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cache_files'", 'to': u"orm['backends.LocalPath']"}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        u'backends.ftpstorage': {
            'Meta': {'object_name': 'FTPStorage', '_ormbases': [u'backends.Storage']},
            'host': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'passwd': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'storage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['backends.Storage']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'})
        },
        u'backends.localpath': {
            'Meta': {'object_name': 'LocalPath', '_ormbases': [u'backends.Location']},
            u'location_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['backends.Location']", 'unique': 'True', 'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'backends.location': {
            'Meta': {'object_name': 'Location'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_type': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'backends.rasdamanlocation': {
            'Meta': {'object_name': 'RasdamanLocation', '_ormbases': [u'backends.Location']},
            'collection': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'location_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['backends.Location']", 'unique': 'True', 'primary_key': 'True'}),
            'oid': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'storage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rasdaman_locations'", 'to': u"orm['backends.RasdamanStorage']"})
        },
        u'backends.rasdamanstorage': {
            'Meta': {'object_name': 'RasdamanStorage', '_ormbases': [u'backends.Storage']},
            'db_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'passwd': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'storage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['backends.Storage']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'})
        },
        u'backends.remotepath': {
            'Meta': {'object_name': 'RemotePath', '_ormbases': [u'backends.Location']},
            u'location_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['backends.Location']", 'unique': 'True', 'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'storage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'paths'", 'to': u"orm['backends.FTPStorage']"})
        },
        u'backends.storage': {
            'Meta': {'object_name': 'Storage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'storage_type': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'core.resource': {
            'Meta': {'object_name': 'Resource'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'coverages.bandrecord': {
            'Meta': {'object_name': 'BandRecord'},
            'definition': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'gdal_interpretation': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'nil_values': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['coverages.NilValueRecord']", 'null': 'True', 'blank': 'True'}),
            'uom': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        },
        u'coverages.coveragerecord': {
            'Meta': {'object_name': 'CoverageRecord', '_ormbases': [u'core.Resource']},
            'automatic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'coverage_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'data_source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'coveragerecord_set'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['coverages.DataSource']"}),
            'layer_metadata': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['coverages.LayerMetadataRecord']", 'null': 'True', 'blank': 'True'}),
            'range_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.RangeTypeRecord']", 'on_delete': 'models.PROTECT'}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'coverages.datapackage': {
            'Meta': {'object_name': 'DataPackage'},
            'data_package_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata_format_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        u'coverages.datasetseriesrecord': {
            'Meta': {'object_name': 'DatasetSeriesRecord', '_ormbases': [u'core.Resource']},
            'data_sources': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'dataset_series_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['coverages.DataSource']"}),
            'eo_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'eo_metadata': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'dataset_series_set'", 'unique': 'True', 'to': u"orm['coverages.EOMetadataRecord']"}),
            'layer_metadata': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['coverages.LayerMetadataRecord']", 'null': 'True', 'blank': 'True'}),
            'rect_datasets': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'dataset_series_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['coverages.RectifiedDatasetRecord']"}),
            'rect_stitched_mosaics': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'dataset_series_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['coverages.RectifiedStitchedMosaicRecord']"}),
            'ref_datasets': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'dataset_series_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['coverages.ReferenceableDatasetRecord']"}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'coverages.datasource': {
            'Meta': {'unique_together': "(('location', 'search_pattern'),)", 'object_name': 'DataSource'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_sources'", 'to': u"orm['backends.Location']"}),
            'search_pattern': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        u'coverages.eometadatarecord': {
            'Meta': {'object_name': 'EOMetadataRecord'},
            'eo_gml': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'footprint': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp_begin': ('django.db.models.fields.DateTimeField', [], {}),
            'timestamp_end': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'coverages.extentrecord': {
            'Meta': {'object_name': 'ExtentRecord'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maxx': ('django.db.models.fields.FloatField', [], {}),
            'maxy': ('django.db.models.fields.FloatField', [], {}),
            'minx': ('django.db.models.fields.FloatField', [], {}),
            'miny': ('django.db.models.fields.FloatField', [], {}),
            'size_x': ('django.db.models.fields.IntegerField', [], {}),
            'size_y': ('django.db.models.fields.IntegerField', [], {}),
            'srid': ('django.db.models.fields.IntegerField', [], {})
        },
        u'coverages.layermetadatarecord': {
            'Meta': {'object_name': 'LayerMetadataRecord'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'coverages.lineagerecord': {
            'Meta': {'object_name': 'LineageRecord'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'coverages.localdatapackage': {
            'Meta': {'object_name': 'LocalDataPackage', '_ormbases': [u'coverages.DataPackage']},
            'data_location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_file_packages'", 'to': u"orm['backends.LocalPath']"}),
            u'datapackage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.DataPackage']", 'unique': 'True', 'primary_key': 'True'}),
            'metadata_location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadata_file_packages'", 'null': 'True', 'to': u"orm['backends.LocalPath']"}),
            'source_format': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'coverages.nilvaluerecord': {
            'Meta': {'object_name': 'NilValueRecord'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'default': "'http://www.opengis.net/def/nil/OGC/0/unknown'", 'max_length': '128'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'coverages.plaincoveragerecord': {
            'Meta': {'object_name': 'PlainCoverageRecord', '_ormbases': [u'coverages.CoverageRecord']},
            u'coveragerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.CoverageRecord']", 'unique': 'True', 'primary_key': 'True'}),
            'data_package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plain_coverages'", 'to': u"orm['coverages.DataPackage']"}),
            'extent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'single_file_coverages'", 'to': u"orm['coverages.ExtentRecord']"})
        },
        u'coverages.rangetype2band': {
            'Meta': {'object_name': 'RangeType2Band'},
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.BandRecord']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'no': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'range_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.RangeTypeRecord']"})
        },
        u'coverages.rangetyperecord': {
            'Meta': {'object_name': 'RangeTypeRecord'},
            'bands': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['coverages.BandRecord']", 'through': u"orm['coverages.RangeType2Band']", 'symmetrical': 'False'}),
            'data_type': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'coverages.rasdamandatapackage': {
            'Meta': {'object_name': 'RasdamanDataPackage', '_ormbases': [u'coverages.DataPackage']},
            'data_location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_packages'", 'to': u"orm['backends.RasdamanLocation']"}),
            u'datapackage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.DataPackage']", 'unique': 'True', 'primary_key': 'True'}),
            'metadata_location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rasdaman_metadata_file_packages'", 'null': 'True', 'to': u"orm['backends.LocalPath']"})
        },
        u'coverages.rectifieddatasetrecord': {
            'Meta': {'object_name': 'RectifiedDatasetRecord', '_ormbases': [u'coverages.CoverageRecord']},
            u'coveragerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.CoverageRecord']", 'unique': 'True', 'primary_key': 'True'}),
            'data_package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rectifieddatasetrecord_set'", 'to': u"orm['coverages.DataPackage']"}),
            'eo_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'eo_metadata': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'rectifieddatasetrecord_set'", 'unique': 'True', 'to': u"orm['coverages.EOMetadataRecord']"}),
            'extent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rect_datasets'", 'to': u"orm['coverages.ExtentRecord']"}),
            'lineage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'rectifieddatasetrecord_set'", 'unique': 'True', 'to': u"orm['coverages.LineageRecord']"}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'coverages.rectifiedstitchedmosaicrecord': {
            'Meta': {'object_name': 'RectifiedStitchedMosaicRecord', '_ormbases': [u'coverages.CoverageRecord']},
            u'coveragerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.CoverageRecord']", 'unique': 'True', 'primary_key': 'True'}),
            'data_sources': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'rect_stitched_mosaics'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['coverages.DataSource']"}),
            'eo_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'eo_metadata': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'rectifiedstitchedmosaicrecord_set'", 'unique': 'True', 'to': u"orm['coverages.EOMetadataRecord']"}),
            'extent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rect_stitched_mosaics'", 'to': u"orm['coverages.ExtentRecord']"}),
            'lineage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'rectifiedstitchedmosaicrecord_set'", 'unique': 'True', 'to': u"orm['coverages.LineageRecord']"}),
            'rect_datasets': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'rect_stitched_mosaics'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['coverages.RectifiedDatasetRecord']"}),
            'tile_index': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rect_stitched_mosaics'", 'to': u"orm['coverages.TileIndex']"})
        },
        u'coverages.referenceabledatasetrecord': {
            'Meta': {'object_name': 'ReferenceableDatasetRecord', '_ormbases': [u'coverages.CoverageRecord']},
            u'coveragerecord_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.CoverageRecord']", 'unique': 'True', 'primary_key': 'True'}),
            'data_package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'referenceabledatasetrecord_set'", 'to': u"orm['coverages.DataPackage']"}),
            'eo_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'eo_metadata': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'referenceabledatasetrecord_set'", 'unique': 'True', 'to': u"orm['coverages.EOMetadataRecord']"}),
            'extent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'refa_datasets'", 'to': u"orm['coverages.ExtentRecord']"}),
            'lineage': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'referenceabledatasetrecord_set'", 'unique': 'True', 'to': u"orm['coverages.LineageRecord']"}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'coverages.remotedatapackage': {
            'Meta': {'object_name': 'RemoteDataPackage', '_ormbases': [u'coverages.DataPackage']},
            'cache_file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'remote_data_packages'", 'null': 'True', 'to': u"orm['backends.CacheFile']"}),
            'data_location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_file_packages'", 'to': u"orm['backends.RemotePath']"}),
            u'datapackage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.DataPackage']", 'unique': 'True', 'primary_key': 'True'}),
            'metadata_location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadata_file_packages'", 'null': 'True', 'to': u"orm['backends.RemotePath']"}),
            'source_format': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'coverages.reservedcoverageidrecord': {
            'Meta': {'object_name': 'ReservedCoverageIdRecord'},
            'coverage_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'until': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'coverages.tileindex': {
            'Meta': {'object_name': 'TileIndex'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'storage_dir': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        }
    }

    complete_apps = ['coverages']
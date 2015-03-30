# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Projection'
        db.create_table(u'coverages_projection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('format', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('definition', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'coverages', ['Projection'])

        # Adding model 'DataSource'
        db.create_table(u'coverages_datasource', (
            (u'dataset_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['backends.Dataset'], unique=True, primary_key=True)),
            ('pattern', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('collection', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.Collection'])),
        ))
        db.send_create_signal(u'coverages', ['DataSource'])

        # Adding model 'EOObject'
        db.create_table(u'coverages_eoobject', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('begin_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('footprint', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(null=True, blank=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('real_content_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal(u'coverages', ['EOObject'])

        # Adding model 'ReservedID'
        db.create_table(u'coverages_reservedid', (
            (u'eoobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.EOObject'], unique=True, primary_key=True)),
            ('until', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('request_id', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
        ))
        db.send_create_signal(u'coverages', ['ReservedID'])

        # Adding model 'NilValueSet'
        db.create_table(u'coverages_nilvalueset', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('data_type', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'coverages', ['NilValueSet'])

        # Adding model 'NilValue'
        db.create_table(u'coverages_nilvalue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('raw_value', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('nil_value_set', self.gf('django.db.models.fields.related.ForeignKey')(related_name='nil_values', to=orm['coverages.NilValueSet'])),
        ))
        db.send_create_signal(u'coverages', ['NilValue'])

        # Adding model 'RangeType'
        db.create_table(u'coverages_rangetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
        ))
        db.send_create_signal(u'coverages', ['RangeType'])

        # Adding model 'Band'
        db.create_table(u'coverages_band', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('index', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('definition', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('uom', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('data_type', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('color_interpretation', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('raw_value_min', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('raw_value_max', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('range_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bands', to=orm['coverages.RangeType'])),
            ('nil_value_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.NilValueSet'], null=True, blank=True)),
        ))
        db.send_create_signal(u'coverages', ['Band'])

        # Adding unique constraint on 'Band', fields ['index', 'range_type']
        db.create_unique(u'coverages_band', ['index', 'range_type_id'])

        # Adding unique constraint on 'Band', fields ['identifier', 'range_type']
        db.create_unique(u'coverages_band', ['identifier', 'range_type_id'])

        # Adding model 'Coverage'
        db.create_table(u'coverages_coverage', (
            (u'dataset_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['backends.Dataset'], unique=True)),
            (u'eoobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.EOObject'], unique=True, primary_key=True)),
            ('min_x', self.gf('django.db.models.fields.FloatField')()),
            ('min_y', self.gf('django.db.models.fields.FloatField')()),
            ('max_x', self.gf('django.db.models.fields.FloatField')()),
            ('max_y', self.gf('django.db.models.fields.FloatField')()),
            ('srid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('projection', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.Projection'], null=True, blank=True)),
            ('size_x', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('size_y', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('range_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.RangeType'])),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'coverages', ['Coverage'])

        # Adding model 'Collection'
        db.create_table(u'coverages_collection', (
            (u'eoobject_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.EOObject'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'coverages', ['Collection'])

        # Adding model 'EOObjectToCollectionThrough'
        db.create_table(u'coverages_eoobjecttocollectionthrough', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('eo_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coverages.EOObject'])),
            ('collection', self.gf('django.db.models.fields.related.ForeignKey')(related_name='coverages_set', to=orm['coverages.Collection'])),
        ))
        db.send_create_signal(u'coverages', ['EOObjectToCollectionThrough'])

        # Adding unique constraint on 'EOObjectToCollectionThrough', fields ['eo_object', 'collection']
        db.create_unique(u'coverages_eoobjecttocollectionthrough', ['eo_object_id', 'collection_id'])

        # Adding model 'RectifiedDataset'
        db.create_table(u'coverages_rectifieddataset', (
            (u'coverage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.Coverage'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'coverages', ['RectifiedDataset'])

        # Adding model 'ReferenceableDataset'
        db.create_table(u'coverages_referenceabledataset', (
            (u'coverage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.Coverage'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'coverages', ['ReferenceableDataset'])

        # Adding model 'RectifiedStitchedMosaic'
        db.create_table(u'coverages_rectifiedstitchedmosaic', (
            (u'collection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.Collection'], unique=True)),
            (u'coverage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.Coverage'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'coverages', ['RectifiedStitchedMosaic'])

        # Adding model 'DatasetSeries'
        db.create_table(u'coverages_datasetseries', (
            (u'collection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['coverages.Collection'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'coverages', ['DatasetSeries'])


    def backwards(self, orm):
        # Removing unique constraint on 'EOObjectToCollectionThrough', fields ['eo_object', 'collection']
        db.delete_unique(u'coverages_eoobjecttocollectionthrough', ['eo_object_id', 'collection_id'])

        # Removing unique constraint on 'Band', fields ['identifier', 'range_type']
        db.delete_unique(u'coverages_band', ['identifier', 'range_type_id'])

        # Removing unique constraint on 'Band', fields ['index', 'range_type']
        db.delete_unique(u'coverages_band', ['index', 'range_type_id'])

        # Deleting model 'Projection'
        db.delete_table(u'coverages_projection')

        # Deleting model 'DataSource'
        db.delete_table(u'coverages_datasource')

        # Deleting model 'EOObject'
        db.delete_table(u'coverages_eoobject')

        # Deleting model 'ReservedID'
        db.delete_table(u'coverages_reservedid')

        # Deleting model 'NilValueSet'
        db.delete_table(u'coverages_nilvalueset')

        # Deleting model 'NilValue'
        db.delete_table(u'coverages_nilvalue')

        # Deleting model 'RangeType'
        db.delete_table(u'coverages_rangetype')

        # Deleting model 'Band'
        db.delete_table(u'coverages_band')

        # Deleting model 'Coverage'
        db.delete_table(u'coverages_coverage')

        # Deleting model 'Collection'
        db.delete_table(u'coverages_collection')

        # Deleting model 'EOObjectToCollectionThrough'
        db.delete_table(u'coverages_eoobjecttocollectionthrough')

        # Deleting model 'RectifiedDataset'
        db.delete_table(u'coverages_rectifieddataset')

        # Deleting model 'ReferenceableDataset'
        db.delete_table(u'coverages_referenceabledataset')

        # Deleting model 'RectifiedStitchedMosaic'
        db.delete_table(u'coverages_rectifiedstitchedmosaic')

        # Deleting model 'DatasetSeries'
        db.delete_table(u'coverages_datasetseries')


    models = {
        u'backends.dataset': {
            'Meta': {'object_name': 'Dataset'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'coverages.band': {
            'Meta': {'ordering': "('index',)", 'unique_together': "(('index', 'range_type'), ('identifier', 'range_type'))", 'object_name': 'Band'},
            'color_interpretation': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'data_type': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'definition': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'index': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'nil_value_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.NilValueSet']", 'null': 'True', 'blank': 'True'}),
            'range_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bands'", 'to': u"orm['coverages.RangeType']"}),
            'raw_value_max': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'raw_value_min': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'uom': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'coverages.collection': {
            'Meta': {'object_name': 'Collection', '_ormbases': [u'coverages.EOObject']},
            'eo_objects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'collections'", 'symmetrical': 'False', 'through': u"orm['coverages.EOObjectToCollectionThrough']", 'to': u"orm['coverages.EOObject']"}),
            u'eoobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.EOObject']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'coverages.coverage': {
            'Meta': {'object_name': 'Coverage', '_ormbases': [u'coverages.EOObject', u'backends.Dataset']},
            u'dataset_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['backends.Dataset']", 'unique': 'True'}),
            u'eoobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.EOObject']", 'unique': 'True', 'primary_key': 'True'}),
            'max_x': ('django.db.models.fields.FloatField', [], {}),
            'max_y': ('django.db.models.fields.FloatField', [], {}),
            'min_x': ('django.db.models.fields.FloatField', [], {}),
            'min_y': ('django.db.models.fields.FloatField', [], {}),
            'projection': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.Projection']", 'null': 'True', 'blank': 'True'}),
            'range_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.RangeType']"}),
            'size_x': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'size_y': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'srid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'coverages.datasetseries': {
            'Meta': {'object_name': 'DatasetSeries', '_ormbases': [u'coverages.Collection']},
            u'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.Collection']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'coverages.datasource': {
            'Meta': {'object_name': 'DataSource', '_ormbases': [u'backends.Dataset']},
            'collection': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.Collection']"}),
            u'dataset_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['backends.Dataset']", 'unique': 'True', 'primary_key': 'True'}),
            'pattern': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'coverages.eoobject': {
            'Meta': {'object_name': 'EOObject'},
            'begin_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'footprint': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'real_content_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'coverages.eoobjecttocollectionthrough': {
            'Meta': {'unique_together': "(('eo_object', 'collection'),)", 'object_name': 'EOObjectToCollectionThrough'},
            'collection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coverages_set'", 'to': u"orm['coverages.Collection']"}),
            'eo_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coverages.EOObject']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'coverages.nilvalue': {
            'Meta': {'object_name': 'NilValue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nil_value_set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nil_values'", 'to': u"orm['coverages.NilValueSet']"}),
            'raw_value': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        u'coverages.nilvalueset': {
            'Meta': {'object_name': 'NilValueSet'},
            'data_type': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        u'coverages.projection': {
            'Meta': {'object_name': 'Projection'},
            'definition': ('django.db.models.fields.TextField', [], {}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'coverages.rangetype': {
            'Meta': {'object_name': 'RangeType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'})
        },
        u'coverages.rectifieddataset': {
            'Meta': {'object_name': 'RectifiedDataset', '_ormbases': [u'coverages.Coverage']},
            u'coverage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.Coverage']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'coverages.rectifiedstitchedmosaic': {
            'Meta': {'object_name': 'RectifiedStitchedMosaic', '_ormbases': [u'coverages.Coverage', u'coverages.Collection']},
            u'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.Collection']", 'unique': 'True'}),
            u'coverage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.Coverage']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'coverages.referenceabledataset': {
            'Meta': {'object_name': 'ReferenceableDataset', '_ormbases': [u'coverages.Coverage']},
            u'coverage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.Coverage']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'coverages.reservedid': {
            'Meta': {'object_name': 'ReservedID', '_ormbases': [u'coverages.EOObject']},
            u'eoobject_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coverages.EOObject']", 'unique': 'True', 'primary_key': 'True'}),
            'request_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['coverages']
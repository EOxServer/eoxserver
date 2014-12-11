# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Storage'
        db.create_table(u'backends_storage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('storage_type', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'backends', ['Storage'])

        # Adding model 'Package'
        db.create_table(u'backends_package', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('format', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('storage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['backends.Storage'], null=True, blank=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='packages', null=True, to=orm['backends.Package'])),
        ))
        db.send_create_signal(u'backends', ['Package'])

        # Adding model 'Dataset'
        db.create_table(u'backends_dataset', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'backends', ['Dataset'])

        # Adding model 'DataItem'
        db.create_table(u'backends_dataitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('format', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('storage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['backends.Storage'], null=True, blank=True)),
            ('dataset', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='data_items', null=True, to=orm['backends.Dataset'])),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='data_items', null=True, to=orm['backends.Package'])),
            ('semantic', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'backends', ['DataItem'])


    def backwards(self, orm):
        # Deleting model 'Storage'
        db.delete_table(u'backends_storage')

        # Deleting model 'Package'
        db.delete_table(u'backends_package')

        # Deleting model 'Dataset'
        db.delete_table(u'backends_dataset')

        # Deleting model 'DataItem'
        db.delete_table(u'backends_dataitem')


    models = {
        u'backends.dataitem': {
            'Meta': {'object_name': 'DataItem'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'data_items'", 'null': 'True', 'to': u"orm['backends.Dataset']"}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'data_items'", 'null': 'True', 'to': u"orm['backends.Package']"}),
            'semantic': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'storage': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backends.Storage']", 'null': 'True', 'blank': 'True'})
        },
        u'backends.dataset': {
            'Meta': {'object_name': 'Dataset'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'backends.package': {
            'Meta': {'object_name': 'Package'},
            'format': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'packages'", 'null': 'True', 'to': u"orm['backends.Package']"}),
            'storage': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backends.Storage']", 'null': 'True', 'blank': 'True'})
        },
        u'backends.storage': {
            'Meta': {'object_name': 'Storage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'storage_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        }
    }

    complete_apps = ['backends']
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Storage'
        db.create_table(u'backends_storage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('storage_type', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal(u'backends', ['Storage'])

        # Adding model 'FTPStorage'
        db.create_table(u'backends_ftpstorage', (
            (u'storage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['backends.Storage'], unique=True, primary_key=True)),
            ('host', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('port', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('passwd', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal(u'backends', ['FTPStorage'])

        # Adding model 'RasdamanStorage'
        db.create_table(u'backends_rasdamanstorage', (
            (u'storage_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['backends.Storage'], unique=True, primary_key=True)),
            ('host', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('port', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('passwd', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('db_name', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal(u'backends', ['RasdamanStorage'])

        # Adding model 'Location'
        db.create_table(u'backends_location', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location_type', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'backends', ['Location'])

        # Adding model 'LocalPath'
        db.create_table(u'backends_localpath', (
            (u'location_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['backends.Location'], unique=True, primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal(u'backends', ['LocalPath'])

        # Adding model 'RemotePath'
        db.create_table(u'backends_remotepath', (
            (u'location_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['backends.Location'], unique=True, primary_key=True)),
            ('storage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='paths', to=orm['backends.FTPStorage'])),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal(u'backends', ['RemotePath'])

        # Adding model 'RasdamanLocation'
        db.create_table(u'backends_rasdamanlocation', (
            (u'location_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['backends.Location'], unique=True, primary_key=True)),
            ('storage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rasdaman_locations', to=orm['backends.RasdamanStorage'])),
            ('collection', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('oid', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'backends', ['RasdamanLocation'])

        # Adding model 'CacheFile'
        db.create_table(u'backends_cachefile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cache_files', to=orm['backends.LocalPath'])),
            ('size', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('access_timestamp', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'backends', ['CacheFile'])


    def backwards(self, orm):
        # Deleting model 'Storage'
        db.delete_table(u'backends_storage')

        # Deleting model 'FTPStorage'
        db.delete_table(u'backends_ftpstorage')

        # Deleting model 'RasdamanStorage'
        db.delete_table(u'backends_rasdamanstorage')

        # Deleting model 'Location'
        db.delete_table(u'backends_location')

        # Deleting model 'LocalPath'
        db.delete_table(u'backends_localpath')

        # Deleting model 'RemotePath'
        db.delete_table(u'backends_remotepath')

        # Deleting model 'RasdamanLocation'
        db.delete_table(u'backends_rasdamanlocation')

        # Deleting model 'CacheFile'
        db.delete_table(u'backends_cachefile')


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
        }
    }

    complete_apps = ['backends']
# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Type'
        db.create_table(u'processes_type', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('handler', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('maxstart', self.gf('django.db.models.fields.IntegerField')(default=3)),
            ('timeout', self.gf('django.db.models.fields.FloatField')(default=3600.0)),
            ('timeret', self.gf('django.db.models.fields.FloatField')(default=-1.0)),
        ))
        db.send_create_signal(u'processes', ['Type'])

        # Adding model 'Instance'
        db.create_table(u'processes_instance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['processes.Type'], on_delete=models.PROTECT)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('timeInsert', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('timeUpdate', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'processes', ['Instance'])

        # Adding unique constraint on 'Instance', fields ['identifier', 'type']
        db.create_unique(u'processes_instance', ['identifier', 'type_id'])

        # Adding model 'Task'
        db.create_table(u'processes_task', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['processes.Instance'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('lock', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
        ))
        db.send_create_signal(u'processes', ['Task'])

        # Adding model 'LogRecord'
        db.create_table(u'processes_logrecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['processes.Instance'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'processes', ['LogRecord'])

        # Adding model 'Response'
        db.create_table(u'processes_response', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['processes.Instance'], unique=True)),
            ('response', self.gf('django.db.models.fields.TextField')()),
            ('mimeType', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'processes', ['Response'])

        # Adding model 'Input'
        db.create_table(u'processes_input', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['processes.Instance'], unique=True)),
            ('input', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'processes', ['Input'])


    def backwards(self, orm):
        # Removing unique constraint on 'Instance', fields ['identifier', 'type']
        db.delete_unique(u'processes_instance', ['identifier', 'type_id'])

        # Deleting model 'Type'
        db.delete_table(u'processes_type')

        # Deleting model 'Instance'
        db.delete_table(u'processes_instance')

        # Deleting model 'Task'
        db.delete_table(u'processes_task')

        # Deleting model 'LogRecord'
        db.delete_table(u'processes_logrecord')

        # Deleting model 'Response'
        db.delete_table(u'processes_response')

        # Deleting model 'Input'
        db.delete_table(u'processes_input')


    models = {
        u'processes.input': {
            'Meta': {'object_name': 'Input'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input': ('django.db.models.fields.TextField', [], {}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['processes.Instance']", 'unique': 'True'})
        },
        u'processes.instance': {
            'Meta': {'unique_together': "(('identifier', 'type'),)", 'object_name': 'Instance'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'timeInsert': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'timeUpdate': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['processes.Type']", 'on_delete': 'models.PROTECT'})
        },
        u'processes.logrecord': {
            'Meta': {'object_name': 'LogRecord'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['processes.Instance']"}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'processes.response': {
            'Meta': {'object_name': 'Response'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['processes.Instance']", 'unique': 'True'}),
            'mimeType': ('django.db.models.fields.TextField', [], {}),
            'response': ('django.db.models.fields.TextField', [], {})
        },
        u'processes.task': {
            'Meta': {'object_name': 'Task'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['processes.Instance']"}),
            'lock': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'processes.type': {
            'Meta': {'object_name': 'Type'},
            'handler': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'maxstart': ('django.db.models.fields.IntegerField', [], {'default': '3'}),
            'timeout': ('django.db.models.fields.FloatField', [], {'default': '3600.0'}),
            'timeret': ('django.db.models.fields.FloatField', [], {'default': '-1.0'})
        }
    }

    complete_apps = ['processes']
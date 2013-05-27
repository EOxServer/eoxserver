# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Implementation'
        db.create_table(u'core_implementation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('intf_id', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('impl_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
        ))
        db.send_create_signal(u'core', ['Implementation'])

        # Adding model 'Component'
        db.create_table(u'core_component', (
            (u'implementation_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Implementation'], unique=True, primary_key=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'core', ['Component'])

        # Adding model 'ResourceClass'
        db.create_table(u'core_resourceclass', (
            (u'implementation_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Implementation'], unique=True, primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal(u'core', ['ResourceClass'])

        # Adding model 'Resource'
        db.create_table(u'core_resource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'core', ['Resource'])

        # Adding model 'Relation'
        db.create_table(u'core_relation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rel_class', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('subj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='relations', to=orm['core.Component'])),
            ('obj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='relations', to=orm['core.Resource'])),
        ))
        db.send_create_signal(u'core', ['Relation'])

        # Adding model 'ClassRelation'
        db.create_table(u'core_classrelation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rel_class', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('subj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='class_relations', to=orm['core.Component'])),
            ('obj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='class_relations', to=orm['core.ResourceClass'])),
        ))
        db.send_create_signal(u'core', ['ClassRelation'])


    def backwards(self, orm):
        # Deleting model 'Implementation'
        db.delete_table(u'core_implementation')

        # Deleting model 'Component'
        db.delete_table(u'core_component')

        # Deleting model 'ResourceClass'
        db.delete_table(u'core_resourceclass')

        # Deleting model 'Resource'
        db.delete_table(u'core_resource')

        # Deleting model 'Relation'
        db.delete_table(u'core_relation')

        # Deleting model 'ClassRelation'
        db.delete_table(u'core_classrelation')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.classrelation': {
            'Meta': {'object_name': 'ClassRelation'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'class_relations'", 'to': u"orm['core.ResourceClass']"}),
            'rel_class': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'subj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'class_relations'", 'to': u"orm['core.Component']"})
        },
        u'core.component': {
            'Meta': {'object_name': 'Component', '_ormbases': [u'core.Implementation']},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'implementation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Implementation']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'core.implementation': {
            'Meta': {'object_name': 'Implementation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impl_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'intf_id': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'core.relation': {
            'Meta': {'object_name': 'Relation'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relations'", 'to': u"orm['core.Resource']"}),
            'rel_class': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'subj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relations'", 'to': u"orm['core.Component']"})
        },
        u'core.resource': {
            'Meta': {'object_name': 'Resource'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'core.resourceclass': {
            'Meta': {'object_name': 'ResourceClass', '_ormbases': [u'core.Implementation']},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'implementation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Implementation']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['core']
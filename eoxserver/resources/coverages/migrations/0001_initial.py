# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('backends', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Band',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.PositiveSmallIntegerField()),
                ('name', models.CharField(max_length=512)),
                ('identifier', models.CharField(max_length=512)),
                ('description', models.TextField(null=True, blank=True)),
                ('definition', models.CharField(max_length=512, null=True, blank=True)),
                ('uom', models.CharField(max_length=64)),
                ('data_type', models.PositiveIntegerField()),
                ('color_interpretation', models.PositiveIntegerField(null=True, blank=True)),
                ('raw_value_min', models.CharField(help_text=b'The string representation of the minimum value.', max_length=512, null=True, blank=True)),
                ('raw_value_max', models.CharField(help_text=b'The string representation of the maximum value.', max_length=512, null=True, blank=True)),
            ],
            options={
                'ordering': ('index',),
            },
        ),
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('dataset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='backends.Dataset')),
                ('pattern', models.CharField(max_length=512)),
            ],
            bases=('backends.dataset',),
        ),
        migrations.CreateModel(
            name='EOObject',
            fields=[
                ('dataset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='backends.Dataset')),
                ('begin_time', models.DateTimeField(null=True, blank=True)),
                ('end_time', models.DateTimeField(null=True, blank=True)),
                ('footprint', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('identifier', models.CharField(unique=True, max_length=256)),
                ('real_content_type', models.PositiveSmallIntegerField()),
            ],
            options={
                'verbose_name': 'EO Object',
                'verbose_name_plural': 'EO Objects',
            },
            bases=('backends.dataset', models.Model),
        ),
        migrations.CreateModel(
            name='EOObjectToCollectionThrough',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'verbose_name': 'EO Object to Collection Relation',
                'verbose_name_plural': 'EO Object to Collection Relations',
            },
        ),
        migrations.CreateModel(
            name='NilValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('raw_value', models.CharField(help_text=b'The string representation of the nil value.', max_length=512)),
                ('reason', models.CharField(help_text=b'A string identifier (commonly a URI or URL) for the reason of this nil value.', max_length=512, choices=[(b'http://www.opengis.net/def/nil/OGC/0/inapplicable', b'Inapplicable (There is no value)'), (b'http://www.opengis.net/def/nil/OGC/0/missing', b'Missing'), (b'http://www.opengis.net/def/nil/OGC/0/template', b'Template (The value will be available later)'), (b'http://www.opengis.net/def/nil/OGC/0/unknown', b'Unknown'), (b'http://www.opengis.net/def/nil/OGC/0/withheld', b'Withheld (The value is not divulged)'), (b'http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange', b'Above detection range'), (b'http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange', b'Below detection range')])),
            ],
            options={
                'verbose_name': 'Nil Value',
            },
        ),
        migrations.CreateModel(
            name='NilValueSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=512)),
                ('data_type', models.PositiveIntegerField()),
            ],
            options={
                'verbose_name': 'Nil Value Set',
            },
        ),
        migrations.CreateModel(
            name='Projection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('format', models.CharField(max_length=16)),
                ('definition', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='RangeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=512)),
            ],
            options={
                'verbose_name': 'Range Type',
            },
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('collection_to_eo_object_ptr', models.OneToOneField(parent_link=True, primary_key=True, serialize=False, to='coverages.EOObject')),
            ],
            options={
                'abstract': False,
            },
            bases=('coverages.eoobject',),
        ),
        migrations.CreateModel(
            name='Coverage',
            fields=[
                ('min_x', models.FloatField()),
                ('min_y', models.FloatField()),
                ('max_x', models.FloatField()),
                ('max_y', models.FloatField()),
                ('srid', models.PositiveIntegerField(null=True, blank=True)),
                ('coverage_to_eo_object_ptr', models.OneToOneField(parent_link=True, primary_key=True, serialize=False, to='coverages.EOObject')),
                ('size_x', models.PositiveIntegerField()),
                ('size_y', models.PositiveIntegerField()),
                ('visible', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('coverages.eoobject', models.Model),
        ),
        migrations.CreateModel(
            name='ReservedID',
            fields=[
                ('eoobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='coverages.EOObject')),
                ('until', models.DateTimeField(null=True)),
                ('request_id', models.CharField(max_length=256, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('coverages.eoobject',),
        ),
        migrations.AddField(
            model_name='nilvalue',
            name='nil_value_set',
            field=models.ForeignKey(related_name='nil_values', to='coverages.NilValueSet'),
        ),
        migrations.AddField(
            model_name='eoobjecttocollectionthrough',
            name='eo_object',
            field=models.ForeignKey(to='coverages.EOObject'),
        ),
        migrations.AddField(
            model_name='band',
            name='nil_value_set',
            field=models.ForeignKey(blank=True, to='coverages.NilValueSet', null=True),
        ),
        migrations.AddField(
            model_name='band',
            name='range_type',
            field=models.ForeignKey(related_name='bands', to='coverages.RangeType'),
        ),
        migrations.CreateModel(
            name='DatasetSeries',
            fields=[
                ('collection_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='coverages.Collection')),
            ],
            options={
                'verbose_name': 'Dataset Series',
                'verbose_name_plural': 'Dataset Series',
            },
            bases=('coverages.collection',),
        ),
        migrations.CreateModel(
            name='RectifiedDataset',
            fields=[
                ('coverage_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='coverages.Coverage')),
            ],
            options={
                'verbose_name': 'Rectified Dataset',
                'verbose_name_plural': 'Rectified Datasets',
            },
            bases=('coverages.coverage',),
        ),
        migrations.CreateModel(
            name='RectifiedStitchedMosaic',
            fields=[
                ('collection_ptr', models.OneToOneField(parent_link=True, auto_created=True, to='coverages.Collection')),
                ('coverage_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='coverages.Coverage')),
            ],
            options={
                'verbose_name': 'Rectified Stitched Mosaic',
                'verbose_name_plural': 'Rectified Stitched Mosaics',
            },
            bases=('coverages.coverage', 'coverages.collection'),
        ),
        migrations.CreateModel(
            name='ReferenceableDataset',
            fields=[
                ('coverage_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='coverages.Coverage')),
            ],
            options={
                'verbose_name': 'Referenceable Dataset',
                'verbose_name_plural': 'Referenceable Datasets',
            },
            bases=('coverages.coverage',),
        ),
        migrations.AddField(
            model_name='eoobjecttocollectionthrough',
            name='collection',
            field=models.ForeignKey(related_name='coverages_set', to='coverages.Collection'),
        ),
        migrations.AddField(
            model_name='datasource',
            name='collection',
            field=models.ForeignKey(related_name='data_sources', to='coverages.Collection'),
        ),
        migrations.AddField(
            model_name='coverage',
            name='projection',
            field=models.ForeignKey(blank=True, to='coverages.Projection', null=True),
        ),
        migrations.AddField(
            model_name='coverage',
            name='range_type',
            field=models.ForeignKey(to='coverages.RangeType'),
        ),
        migrations.AddField(
            model_name='collection',
            name='eo_objects',
            field=models.ManyToManyField(related_name='collections', through='coverages.EOObjectToCollectionThrough', to='coverages.EOObject'),
        ),
        migrations.AlterUniqueTogether(
            name='band',
            unique_together=set([('identifier', 'range_type'), ('index', 'range_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='eoobjecttocollectionthrough',
            unique_together=set([('eo_object', 'collection')]),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location', models.CharField(max_length=1024)),
                ('format', models.CharField(max_length=64, null=True, blank=True)),
                ('semantic', models.CharField(max_length=64)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location', models.CharField(max_length=1024)),
                ('format', models.CharField(max_length=64, null=True, blank=True)),
                ('package', models.ForeignKey(related_name='packages', blank=True, to='backends.Package', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=1024)),
                ('storage_type', models.CharField(max_length=32)),
            ],
        ),
        migrations.AddField(
            model_name='package',
            name='storage',
            field=models.ForeignKey(blank=True, to='backends.Storage', null=True),
        ),
        migrations.AddField(
            model_name='dataitem',
            name='dataset',
            field=models.ForeignKey(related_name='data_items', blank=True, to='backends.Dataset', null=True),
        ),
        migrations.AddField(
            model_name='dataitem',
            name='package',
            field=models.ForeignKey(related_name='data_items', blank=True, to='backends.Package', null=True),
        ),
        migrations.AddField(
            model_name='dataitem',
            name='storage',
            field=models.ForeignKey(blank=True, to='backends.Storage', null=True),
        ),
    ]

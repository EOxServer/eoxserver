# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Input',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('input', models.TextField(editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=64, editable=False)),
                ('timeInsert', models.DateTimeField(auto_now_add=True)),
                ('timeUpdate', models.DateTimeField(auto_now=True)),
                ('status', models.IntegerField(editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='LogRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now=True)),
                ('status', models.IntegerField(editable=False, choices=[(0, b'UNDEFINED'), (1, b'ACCEPTED'), (2, b'SCHEDULED'), (3, b'RUNNING'), (4, b'PAUSED'), (5, b'FINISHED'), (6, b'FAILED')])),
                ('message', models.TextField(editable=False)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='processes.Instance')),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response', models.TextField(editable=False)),
                ('mimeType', models.TextField()),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='processes.Instance', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now=True)),
                ('lock', models.BigIntegerField(default=0)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='processes.Instance')),
            ],
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(unique=True, max_length=64, editable=False)),
                ('handler', models.CharField(max_length=1024, editable=False)),
                ('maxstart', models.IntegerField(default=3, editable=False)),
                ('timeout', models.FloatField(default=3600.0, editable=False)),
                ('timeret', models.FloatField(default=-1.0, editable=False)),
            ],
        ),
        migrations.AddField(
            model_name='instance',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='processes.Type'),
        ),
        migrations.AddField(
            model_name='input',
            name='instance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to='processes.Instance', unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='instance',
            unique_together=set([('identifier', 'type')]),
        ),
    ]

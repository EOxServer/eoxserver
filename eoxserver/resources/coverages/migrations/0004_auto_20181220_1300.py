# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2018-12-20 13:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backends', '0001_initial'),
        ('coverages', '0003_metadata_items_semantic'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductDataItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=1024)),
                ('format', models.CharField(blank=True, max_length=64, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_data_items', to='coverages.Product')),
                ('storage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backends.Storage')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='eoobject',
            name='identifier',
            field=models.CharField(max_length=256, unique=True),
        ),
    ]
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coverages', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Extra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_name', models.CharField(max_length=64, null=True, blank=True)),
                ('info', models.TextField(null=True, blank=True)),
                ('color', models.CharField(max_length=64, null=True, blank=True)),
                ('default_visible', models.BooleanField(default=False)),
                ('eo_object', models.OneToOneField(related_name='webclient_extra', to='coverages.EOObject')),
            ],
        ),
    ]

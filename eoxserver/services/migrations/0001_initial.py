# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coverages', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='WMSRenderOptions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('default_red', models.PositiveIntegerField(default=None, null=True, blank=True)),
                ('default_green', models.PositiveIntegerField(default=None, null=True, blank=True)),
                ('default_blue', models.PositiveIntegerField(default=None, null=True, blank=True)),
                ('default_alpha', models.PositiveIntegerField(default=None, null=True, blank=True)),
                ('resampling', models.CharField(max_length=16, null=True, blank=True)),
                ('scale_auto', models.BooleanField(default=False)),
                ('scale_min', models.PositiveIntegerField(null=True, blank=True)),
                ('scale_max', models.PositiveIntegerField(null=True, blank=True)),
                ('bands_scale_min', models.CharField(max_length=256, null=True, blank=True)),
                ('bands_scale_max', models.CharField(max_length=256, null=True, blank=True)),
                ('coverage', models.OneToOneField(to='coverages.Coverage')),
            ],
        ),
    ]

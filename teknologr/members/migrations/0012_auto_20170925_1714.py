# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-09-25 14:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0011_auto_20170906_2105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='student_id',
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
    ]

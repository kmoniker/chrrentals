# Generated by Django 2.0.6 on 2018-09-21 18:04

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0004_auto_20180921_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deposit',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]

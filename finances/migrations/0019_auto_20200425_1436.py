# Generated by Django 2.1.3 on 2020-04-25 20:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0018_auto_20200425_1241'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='asset',
            new_name='property',
        ),
    ]

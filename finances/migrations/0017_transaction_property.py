# Generated by Django 2.1.3 on 2020-04-25 18:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0016_auto_20190602_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='property',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finances.Asset'),
        ),
    ]

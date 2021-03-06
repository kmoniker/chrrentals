# Generated by Django 2.0.6 on 2018-09-21 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0003_tenant_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=2, help_text='A positive number.', max_digits=8),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='bank_posted_date',
            field=models.DateField(blank=True, help_text='The date the transaction hit the bank.', null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='out_flow',
            field=models.BooleanField(help_text="Check this box if it's an expense."),
        ),
    ]

# Generated by Django 3.0.7 on 2020-06-19 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('batch_transfer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='batchtransferjob',
            name='trial_protocol_id',
            field=models.TextField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='batchtransferjob',
            name='trial_protocol_name',
            field=models.TextField(default='', max_length=64),
            preserve_default=False,
        ),
    ]

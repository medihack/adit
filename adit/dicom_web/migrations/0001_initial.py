# Generated by Django 4.2.2 on 2023-06-29 10:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DicomWebSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("locked", models.BooleanField(default=False)),
                ("suspended", models.BooleanField(default=False)),
                (
                    "slot_begin_time",
                    models.TimeField(
                        default=datetime.time(22, 0), help_text="Must be set in UTC time zone."
                    ),
                ),
                (
                    "slot_end_time",
                    models.TimeField(
                        default=datetime.time(8, 0), help_text="Must be set in UTC time zone."
                    ),
                ),
                ("transfer_timeout", models.IntegerField(default=3)),
            ],
            options={
                "verbose_name_plural": "Dicom Web settings",
            },
        ),
    ]

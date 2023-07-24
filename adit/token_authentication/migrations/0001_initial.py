# Generated by Django 4.2.2 on 2023-06-15 12:59

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TokenSettings",
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
                "verbose_name_plural": "Token settings",
            },
        ),
        migrations.CreateModel(
            name="Token",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("token_string", models.TextField(max_length=30)),
                ("created_time", models.DateTimeField(auto_now_add=True)),
                ("client", models.TextField(max_length=100)),
                ("expiry_time", models.DateTimeField()),
                ("expires", models.BooleanField(default=True)),
                ("last_used", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "permissions": [("manage_auth_tokens", "Can manage REST authentication tokens")],
            },
        ),
    ]

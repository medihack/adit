# Generated by Django 4.2.7 on 2023-12-10 12:53

from django.db import migrations


def copy_fields_to_profile(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    UserProfile = apps.get_model("accounts", "UserProfile")
    for user in User.objects.all():
        profile = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = user.phone_number
        profile.department = user.department
        profile.preferences = user.preferences
        profile.save()


def copy_fields_from_profile(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    for profile in UserProfile.objects.all():
        user = profile.user
        user.phone_number = profile.phone_number
        user.department = profile.department
        user.preferences = profile.preferences
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_userprofile"),
    ]

    operations = [migrations.RunPython(copy_fields_to_profile, copy_fields_from_profile)]

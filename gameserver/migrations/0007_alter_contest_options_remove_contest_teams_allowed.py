# Generated by Django 4.0.1 on 2022-01-29 22:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gameserver", "0006_rename_is_private_contest_is_public_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contest",
            options={
                "permissions": (
                    ("change_contest_visibility", "Change visibility of contests"),
                    ("edit_all_contests", "Edit all contests"),
                )
            },
        ),
        migrations.RemoveField(
            model_name="contest",
            name="teams_allowed",
        ),
    ]

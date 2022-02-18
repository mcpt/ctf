# Generated by Django 4.0.1 on 2022-02-18 18:13

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gameserver", "0020_alter_contestproblem_options_contestproblem_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="contest",
            name="curators",
            field=models.ManyToManyField(
                blank=True, related_name="contests_curated", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]

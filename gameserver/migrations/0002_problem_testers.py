# Generated by Django 4.0.1 on 2022-01-26 22:02

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gameserver", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="problem",
            name="testers",
            field=models.ManyToManyField(
                blank=True, related_name="problems_testing", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]

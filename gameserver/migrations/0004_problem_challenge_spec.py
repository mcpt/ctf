# Generated by Django 4.0.1 on 2022-01-27 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gameserver', '0003_alter_user_school_contact_alter_user_school_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='challenge_spec',
            field=models.JSONField(blank=True, null=True),
        ),
    ]

# Generated by Django 4.0.1 on 2022-02-08 02:50

from django.db import migrations, models

import gameserver.models.problem


class Migration(migrations.Migration):

    dependencies = [
        ('gameserver', '0012_problem_opaque_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='opaque_id',
            field=models.CharField(default=gameserver.models.problem.gen_opaque_id, editable=False, max_length=172),
        ),
    ]

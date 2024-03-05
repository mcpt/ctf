# Generated by Django 4.0.1 on 2024-03-05 02:51

from django.db import migrations, models
import gameserver.models.profile


class Migration(migrations.Migration):

    dependencies = [
        ('gameserver', '0031_problem_log_submission_content_submission_content_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(fields=['user'], name='gameserver__user_id_87074d_idx'),
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(fields=['problem'], name='gameserver__problem_4c16db_idx'),
        ),
        migrations.AddIndex(
            model_name='submission',
            index=models.Index(fields=['is_correct'], name='gameserver__is_corr_678c6b_idx'),
        ),
    ]

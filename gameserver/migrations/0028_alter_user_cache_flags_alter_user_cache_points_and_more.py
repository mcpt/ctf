# Generated by Django 4.0.1 on 2023-02-28 19:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import gameserver.models.profile


class Migration(migrations.Migration):

    dependencies = [
        ('gameserver', '0027_user_cache_flags_user_cache_points'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='cache_flags',
            field=models.IntegerField(default=None, verbose_name='Total Flags Cache'),
        ),
        migrations.AlterField(
            model_name='user',
            name='cache_points',
            field=models.IntegerField(default=None, verbose_name='Total Points Cache'),
        ),
        migrations.CreateModel(
            name='UserCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(verbose_name='Points')),
                ('flags', models.IntegerField(verbose_name='Flags')),
                ('participation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='current_caches', to='gameserver.contestparticipation')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='caches', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

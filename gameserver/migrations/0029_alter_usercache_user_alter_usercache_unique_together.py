# Generated by Django 4.0.1 on 2023-02-28 19:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gameserver', '0028_alter_user_cache_flags_alter_user_cache_points_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercache',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='caches', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='usercache',
            unique_together={('user', 'participation')},
        ),
    ]

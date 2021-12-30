# Generated by Django 3.2.8 on 2021-12-27 20:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('gameserver', '0006_auto_20211227_2032'), ('gameserver', '0007_alter_writeup_url')]

    dependencies = [
        ('gameserver', '0005_editorial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Writeup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(blank=True, max_length=128)),
                ('text', models.TextField(blank=True)),
                ('summary', models.CharField(max_length=150)),
                ('slug', models.SlugField(unique=True)),
                ('url', models.URLField(blank=True, null=True)),
                ('pointee', models.CharField(choices=[('P', 'Post'), ('E', 'External URL')], default='E', max_length=1)),
                ('author', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='writeups', to='gameserver.problem')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='Editorial',
        ),
    ]
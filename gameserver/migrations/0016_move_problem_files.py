import os
from shutil import move

from django.conf import settings
from django.db import migrations

import gameserver.models.problem


def move_problem_files(apps, schema_editor):
    MEDIA_ROOT = settings.MEDIA_ROOT
    media_path = lambda path: os.path.join(MEDIA_ROOT, path)
    Problem = apps.get_model('gameserver', 'Problem')
    for problem in Problem.objects.all():
        for file in problem.files.all():
            orig_path = str(file.artifact)
            filename = os.path.basename(os.path.normpath(orig_path))
            new_filename = gameserver.models.problem.problem_file_path(file, filename)
            if media_path(orig_path) == media_path(new_filename):
                print("[{}] NOT MOVING {}".format(problem.slug, media_path(orig_path)))
            else:
                print("[{}] MOVING {} to {}".format(problem.slug, media_path(orig_path), media_path(new_filename)))
                # could be implemented by shutil.move-ing a the directory, but this is easier to write
                if not os.path.exists(new_filename):
                    os.makedirs(os.path.dirname(media_path(new_filename)), exist_ok=True)
                move(media_path(orig_path), media_path(new_filename))
            containing = os.path.dirname(media_path(orig_path))
            if os.path.exists(containing) and len(os.listdir(containing)) == 0:
                print("[{}] REMOVING EMPTY DIRECTORY {} for {}".format(problem.slug, containing, media_path(new_filename)))
                os.rmdir(containing)
            file.artifact = new_filename
            file.save()

class Migration(migrations.Migration):

    dependencies = [
        ('gameserver', '0015_alter_problem_opaque_id'),
    ]

    operations = [
        migrations.RunPython(move_problem_files, reverse_code=migrations.RunPython.noop),
    ]

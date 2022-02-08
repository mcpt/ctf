from django.db import migrations
import gameserver.models.problem

def regen_opaque_id(apps, schema_editor):
    Problem = apps.get_model('gameserver', 'Problem')
    for row in Problem.objects.all():
        row.opaque_id = gameserver.models.problem.gen_opaque_id()
        row.save(update_fields=['opaque_id'])

class Migration(migrations.Migration):

    dependencies = [
        ('gameserver', '0013_alter_problem_opaque_id'),
    ]

    operations = [
        migrations.RunPython(regen_opaque_id, reverse_code=migrations.RunPython.noop),
    ]

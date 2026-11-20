from django.db import migrations


def seed_categories(apps, schema_editor):
    category = apps.get_model('feedback_polls', 'FeedbackCategory')
    categories = ('فاطمیه', 'هیئت هفتگی', 'خوابگاه‌ها', 'برنامه‌ها و مراسم', 'سایر موضوعات')
    for position, name in enumerate(categories, start=1):
        category.objects.using(schema_editor.connection.alias).get_or_create(
            name=name, defaults={'position': position},
        )


class Migration(migrations.Migration):
    dependencies = [('feedback_polls', '0001_initial')]
    operations = [migrations.RunPython(seed_categories, migrations.RunPython.noop)]

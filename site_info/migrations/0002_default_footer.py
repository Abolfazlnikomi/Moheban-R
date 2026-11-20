from django.db import migrations


def create_footer(apps, schema_editor):
    footer = apps.get_model('site_info', 'FooterSettings')
    footer.objects.using(schema_editor.connection.alias).get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [('site_info', '0001_initial')]
    operations = [migrations.RunPython(create_footer, migrations.RunPython.noop)]

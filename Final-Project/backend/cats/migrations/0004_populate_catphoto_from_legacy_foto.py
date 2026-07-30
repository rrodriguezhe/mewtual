from django.db import migrations


def populate_catphoto_from_legacy_foto(apps, schema_editor):
    Cat = apps.get_model("cats", "Cat")
    CatPhoto = apps.get_model("cats", "CatPhoto")
    for cat in Cat.objects.exclude(foto="").exclude(foto__isnull=True):
        CatPhoto.objects.create(gato_id=cat.pk, imagen=cat.foto.name, orden=0)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("cats", "0003_catphoto"),
    ]

    operations = [
        migrations.RunPython(populate_catphoto_from_legacy_foto, noop_reverse),
    ]

# Generated by Django 2.2.16 on 2021-04-16 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0008_auto_20210402_1428"),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="_is_deleted",
            field=models.BooleanField(default=False),
        ),
    ]

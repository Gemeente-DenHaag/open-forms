# Generated by Django 2.2.24 on 2021-07-21 09:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cookie_consent", "0002_auto__add_logitem"),
        ("config", "0014_auto_20210716_1046"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="analytics_cookie_consent_group",
            field=models.ForeignKey(
                blank=True,
                help_text="The cookie group used for analytical cookies. The analytics scripts are loaded only if this cookie group is accepted by the end-user.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cookie_consent.CookieGroup",
            ),
        ),
    ]
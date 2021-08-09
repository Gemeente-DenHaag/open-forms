# Generated by Django 2.2.24 on 2021-08-09 13:26

from django.db import migrations, models


def set_initial_last_register_date(apps, schema_editor):
    Submission = apps.get_model("submissions", "Submission")
    for submission in Submission.objects.all():
        submission.last_register_date = submission.completed_on
        submission.save()


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0025_auto_20210726_0832"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="last_register_date",
            field=models.DateTimeField(
                blank=True,
                help_text="The last time the submission registration was attempted with the backend.  Note that this date will be updated even if the registration is not successful.",
                null=True,
                verbose_name="last register attempt date",
            ),
        ),
        migrations.AlterField(
            model_name="submission",
            name="registration_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending (not registered yet)"),
                    ("in_progress", "In Progress (not registered yet)"),
                    ("success", "Success"),
                    ("failed", "Failed"),
                ],
                default="pending",
                help_text="Indication whether the registration in the configured backend was successful.",
                max_length=50,
                verbose_name="registration backend status",
            ),
        ),
        migrations.RunPython(set_initial_last_register_date, migrations.RunPython.noop),
    ]

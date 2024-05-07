# Generated by Django 4.2.4 on 2023-08-23 00:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tomato", "0003_rotator_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="rotator",
            name="is_single_play",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Enable single play mode, which will cause the desktop app to allow playing a random asset from"
                    " this rotator. (Standard and advanced mode only.)"
                ),
                verbose_name="single play",
            ),
        ),
        migrations.AlterField(
            model_name="clientlogentry",
            name="type",
            field=models.CharField(
                choices=[
                    ("internal_error", "Internal client error"),
                    ("login", "Logged in or reconnected"),
                    ("logout", "Logged out"),
                    ("overdue", "Playing of stop set overdue"),
                    ("played_asset", "Played an audio asset"),
                    ("played_single", "Played single play rotator"),
                    ("played_stopset", "Played an entire stop set"),
                    ("skipped_asset", "Skipped (or played a partial) audio asset"),
                    ("skipped_stopset", "Skipped (or played a partial) stop set"),
                    ("waited", "Waited"),
                    ("unspecified", "Unspecified"),
                ],
                default="unspecified",
                max_length=15,
            ),
        ),
    ]
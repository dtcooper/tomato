# Generated by Django 4.2.3 on 2023-07-10 22:59

import datetime
import dirtyfields.dirtyfields
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import tomato.models.asset
import tomato.models.base
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Designates that this user is an administrator and is implicitly in all groups. NOTE: Only"
                            " administrators can create and edit user accounts. "
                        ),
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={"unique": "A user with that username already exists."},
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                        verbose_name="username",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Designates whether this account is enabled. Unselect this instead of deleting an account."
                        ),
                        verbose_name="active",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="created at")),
                (
                    "enable_client_logs",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Disable client logging for this account. In general you'll want to keep this enabled, but"
                            " for test accounts you may not want to pollute the client logs."
                        ),
                        verbose_name="client logs entries enabled",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The permission groups this user belongs to.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "db_table": "users",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Rotator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="created at")),
                (
                    "name",
                    models.CharField(
                        help_text="The name of this rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc.",
                        max_length=70,
                        unique=True,
                        verbose_name="name",
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        choices=[
                            ("red", "Red"),
                            ("pink", "Pink"),
                            ("purple", "Purple"),
                            ("deep-purple", "Deep Purple"),
                            ("indigo", "Indigo"),
                            ("blue", "Blue"),
                            ("light-blue", "Light Blue"),
                            ("cyan", "Cyan"),
                            ("teal", "Teal"),
                            ("green", "Green"),
                            ("light-green", "Light Green"),
                            ("lime", "Lime"),
                            ("yellow", "Yellow"),
                            ("amber", "Amber"),
                            ("orange", "Orange"),
                            ("deep-orange", "Deep Orange"),
                        ],
                        default="red",
                        help_text="Color that appears in the client for this rotator.",
                        max_length=20,
                        verbose_name="Color",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
            ],
            options={
                "verbose_name": "rotator",
                "db_table": "rotators",
                "ordering": ("name",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Stopset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text="If unselected, entity is completely disabled regardless of begin and end air date.",
                        verbose_name="enabled",
                    ),
                ),
                (
                    "begin",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text=(
                            "Date when eligibility for random selection <strong>begins</strong>. If specified, random"
                            " selection is only eligible after this date. If left blank, its always eligible for random"
                            " selection up to end air date."
                        ),
                        null=True,
                        verbose_name="begin air date",
                    ),
                ),
                (
                    "end",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text=(
                            "Date when eligibility for random selection <strong>ends</strong>. If specified, random"
                            " selection is only eligible before this date. If left blank, its always eligible for"
                            " random selection starting with begin air date."
                        ),
                        null=True,
                        verbose_name="end air date",
                    ),
                ),
                (
                    "weight",
                    models.DecimalField(
                        decimal_places=2,
                        default=1,
                        help_text=(
                            "The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as"
                            " likely as all others, '2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, and"
                            ' so on. See the <a href="http://dtcooper.github.io/tomato/concepts#weight"'
                            ' target="_blank">docs for more information</a>.'
                        ),
                        max_digits=6,
                        validators=[tomato.models.base.greater_than_zero],
                        verbose_name="weight",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="created at")),
                ("name", models.CharField(max_length=70, unique=True, verbose_name="name")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
            ],
            options={
                "verbose_name": "stop set",
                "db_table": "stopsets",
                "ordering": ("name",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="StopsetRotator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "rotator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="tomato.rotator", verbose_name="Rotator"
                    ),
                ),
                ("stopset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tomato.stopset")),
            ],
            options={
                "verbose_name": "rotator in stop set relationship",
                "db_table": "stopset_rotators",
                "ordering": ("id",),
            },
        ),
        migrations.AddField(
            model_name="rotator",
            name="stopsets",
            field=models.ManyToManyField(
                related_name="rotators", through="tomato.StopsetRotator", to="tomato.stopset", verbose_name="stop set"
            ),
        ),
        migrations.CreateModel(
            name="ClientLogEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("played_asset", "Played an audio asset"),
                            ("played_part_stopset", "Played a partial stop set"),
                            ("played_stopset", "Played an entire stop set"),
                            ("skipped_asset", "Skipped playing an audio asset"),
                            ("skipped_stopset", "Skipped playing an entire stop set"),
                            ("waited", "Waited"),
                        ],
                        max_length=19,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "verbose_name": "client log entry",
                "verbose_name_plural": "client log entries",
                "db_table": "logs",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Asset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "begin",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text=(
                            "Date when eligibility for random selection <strong>begins</strong>. If specified, random"
                            " selection is only eligible after this date. If left blank, its always eligible for random"
                            " selection up to end air date."
                        ),
                        null=True,
                        verbose_name="begin air date",
                    ),
                ),
                (
                    "end",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text=(
                            "Date when eligibility for random selection <strong>ends</strong>. If specified, random"
                            " selection is only eligible before this date. If left blank, its always eligible for"
                            " random selection starting with begin air date."
                        ),
                        null=True,
                        verbose_name="end air date",
                    ),
                ),
                (
                    "weight",
                    models.DecimalField(
                        decimal_places=2,
                        default=1,
                        help_text=(
                            "The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as"
                            " likely as all others, '2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, and"
                            ' so on. See the <a href="http://dtcooper.github.io/tomato/concepts#weight"'
                            ' target="_blank">docs for more information</a>.'
                        ),
                        max_digits=6,
                        validators=[tomato.models.base.greater_than_zero],
                        verbose_name="weight",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="created at")),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text=(
                            "Optional name, if left empty, we'll automatically base it off the audio file's metadata"
                            " and failing that its filename."
                        ),
                        max_length=70,
                        verbose_name="name",
                    ),
                ),
                ("file", models.FileField(upload_to=tomato.models.asset.asset_upload_to, verbose_name="audio file")),
                ("md5sum", models.BinaryField(default=None, max_length=16, null=True)),
                (
                    "status",
                    models.SmallIntegerField(
                        choices=[(0, "Pending processing"), (1, "Processing"), (2, "Ready")],
                        default=0,
                        help_text="All assets will be processed after uploading.",
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Designates whether this asset is enabled. Unselect this to completely disable playing of"
                            " this asset."
                        ),
                        verbose_name="enabled",
                    ),
                ),
                ("duration", models.DurationField(default=datetime.timedelta(0))),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "rotators",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Rotators that this asset will be included in.",
                        related_name="assets",
                        to="tomato.rotator",
                        verbose_name="rotators",
                    ),
                ),
            ],
            options={
                "verbose_name": "audio asset",
                "db_table": "assets",
                "ordering": ("-created_at",),
                "permissions": [("immediate_play_asset", "Can immediately play audio assets")],
                "abstract": False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]

import datetime

from django.db import migrations, models

BROKERS = ["degiro", "bitvavo"]


def load_broker_config(apps, schema_editor):
    broker_configuration = apps.get_model("stonks_overwatch", "BrokersConfiguration")
    for broker in BROKERS:
        enabled = True if broker == "degiro" else False
        credentials = {}
        start_date = datetime.date(2020, 1, 1)
        update_frequency = 5

        broker_configuration.objects.update_or_create(
            broker_name=broker,
            defaults={
                "enabled": enabled,
                "credentials": credentials,
                "start_date": start_date,
                "update_frequency": update_frequency,
            },
        )


def reverse_func(apps, schema_editor):
    broker_configuration = apps.get_model("stonks_overwatch", "BrokersConfiguration")
    for broker in BROKERS:
        broker_configuration.objects.filter(broker_name=broker).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("stonks_overwatch", "0004_bitvavo"),
    ]

    operations = [
        migrations.CreateModel(
            name="BrokersConfiguration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("broker_name", models.CharField(max_length=64, unique=True)),
                ("enabled", models.BooleanField(default=False)),
                ("start_date", models.DateField(blank=True, null=True)),
                (
                    "update_frequency",
                    models.IntegerField(default=5, help_text="Update frequency in minutes"),
                ),
                ("credentials", models.JSONField()),
            ],
            options={
                "db_table": '"brokers_configuration"',
            },
        ),
        migrations.RunPython(load_broker_config, reverse_func),
    ]

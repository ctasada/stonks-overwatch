import datetime

from django.db import migrations

BROKERS = ["ibkr"]


def load_broker_config(apps, schema_editor):
    broker_configuration = apps.get_model("stonks_overwatch", "BrokersConfiguration")
    for broker in BROKERS:
        enabled = False
        credentials = {}
        start_date = datetime.date(2020, 1, 1)
        update_frequency = 15

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
        ("stonks_overwatch", "0006_alter_degiro_crypto"),
    ]

    operations = [
        migrations.RunPython(load_broker_config, reverse_func),
    ]

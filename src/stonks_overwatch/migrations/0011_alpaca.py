# ruff: noqa: E501
import datetime

from django.db import migrations, models

from stonks_overwatch.constants import BrokerName


def load_alpaca_config(apps, schema_editor):
    broker_configuration = apps.get_model("stonks_overwatch", "BrokersConfiguration")
    broker_configuration.objects.update_or_create(
        broker_name=BrokerName.ALPACA,
        defaults={
            "enabled": False,
            "credentials": {},
            "start_date": datetime.date(2020, 1, 1),
            "update_frequency": 15,
        },
    )


def reverse_alpaca_config(apps, schema_editor):
    broker_configuration = apps.get_model("stonks_overwatch", "BrokersConfiguration")
    broker_configuration.objects.filter(broker_name=BrokerName.ALPACA).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("stonks_overwatch", "0010_brokersynclog"),
    ]

    operations = [
        migrations.CreateModel(
            name="AlpacaActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activity_id", models.CharField(max_length=100, unique=True)),
                ("activity_type", models.CharField(db_index=True, max_length=20)),
                ("symbol", models.CharField(blank=True, max_length=25, null=True)),
                ("qty", models.DecimalField(blank=True, decimal_places=10, default=None, max_digits=20, null=True)),
                ("price", models.DecimalField(blank=True, decimal_places=10, default=None, max_digits=20, null=True)),
                (
                    "net_amount",
                    models.DecimalField(blank=True, decimal_places=10, default=None, max_digits=20, null=True),
                ),
                (
                    "per_share_amount",
                    models.DecimalField(blank=True, decimal_places=10, default=None, max_digits=20, null=True),
                ),
                ("activity_date", models.DateField(blank=True, null=True)),
                ("description", models.CharField(blank=True, max_length=500, null=True)),
            ],
            options={
                "db_table": '"alpaca_activity"',
            },
        ),
        migrations.CreateModel(
            name="AlpacaOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.CharField(max_length=50, unique=True)),
                ("symbol", models.CharField(db_index=True, max_length=25)),
                ("qty", models.DecimalField(blank=True, decimal_places=10, default=None, max_digits=20, null=True)),
                (
                    "filled_qty",
                    models.DecimalField(blank=True, decimal_places=10, default=None, max_digits=20, null=True),
                ),
                (
                    "filled_avg_price",
                    models.DecimalField(blank=True, decimal_places=10, default=None, max_digits=20, null=True),
                ),
                ("side", models.CharField(max_length=10)),
                ("order_type", models.CharField(max_length=20)),
                ("status", models.CharField(max_length=20)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("filled_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": '"alpaca_order"',
            },
        ),
        migrations.CreateModel(
            name="AlpacaPosition",
            fields=[
                ("symbol", models.CharField(max_length=25, primary_key=True, serialize=False)),
                ("qty", models.DecimalField(decimal_places=10, default=0, max_digits=20)),
                (
                    "avg_entry_price",
                    models.DecimalField(blank=True, decimal_places=10, default=0, max_digits=20, null=True),
                ),
                (
                    "market_value",
                    models.DecimalField(blank=True, decimal_places=10, default=0, max_digits=20, null=True),
                ),
                (
                    "current_price",
                    models.DecimalField(blank=True, decimal_places=10, default=0, max_digits=20, null=True),
                ),
                (
                    "unrealized_pl",
                    models.DecimalField(blank=True, decimal_places=10, default=0, max_digits=20, null=True),
                ),
                ("cost_basis", models.DecimalField(blank=True, decimal_places=10, default=0, max_digits=20, null=True)),
                ("side", models.CharField(default="long", max_length=10)),
                ("currency", models.CharField(default="USD", max_length=10)),
                ("synced_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": '"alpaca_position"',
            },
        ),
        migrations.RunPython(load_alpaca_config, reverse_alpaca_config),
    ]

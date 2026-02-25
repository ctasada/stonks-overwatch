import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stonks_overwatch", "0009_globalconfiguration"),
    ]

    operations = [
        migrations.CreateModel(
            name="BrokerSyncLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("broker_name", models.CharField(db_index=True, max_length=50)),
                ("synced_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("success", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Broker Sync Log",
                "verbose_name_plural": "Broker Sync Logs",
                "db_table": "broker_sync_log",
                "get_latest_by": "synced_at",
            },
        ),
    ]

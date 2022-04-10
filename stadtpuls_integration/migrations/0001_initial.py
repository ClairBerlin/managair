# Generated by Django 4.0.2 on 2022-04-10 21:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0006_address_latitude_address_longitude'),
    ]

    operations = [
        migrations.CreateModel(
            name='StadpulsSensor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inserted_s', models.PositiveIntegerField()),
                ('installation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stadtpuls_sensor', to='core.roomnodeinstallation')),
            ],
        ),
    ]

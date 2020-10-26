# Generated by Django 3.1.2 on 2020-10-26 09:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20201025_2028'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='height_m',
            field=models.DecimalField(decimal_places=1, max_digits=3, null=True),
        ),
        migrations.CreateModel(
            name='RoomNodeInstallation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_timestamp', models.PositiveIntegerField()),
                ('to_timestamp', models.PositiveIntegerField(null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_installation', to='core.node')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='node_installations', to='core.room')),
            ],
            options={
                'ordering': ['-from_timestamp'],
                'get_latest_by': 'from_timestamp',
            },
        ),
        migrations.AddConstraint(
            model_name='roomnodeinstallation',
            constraint=models.UniqueConstraint(fields=('node', 'from_timestamp'), name='unique_node_installation'),
        ),
    ]
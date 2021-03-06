# Generated by Django 3.1.2 on 2020-10-27 10:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0005_auto_20201026_0918'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='roomnodeinstallation',
            options={'get_latest_by': 'from_timestamp_s', 'ordering': ['-from_timestamp_s']},
        ),
        migrations.RemoveConstraint(
            model_name='roomnodeinstallation',
            name='unique_node_installation',
        ),
        migrations.RenameField(
            model_name='roomnodeinstallation',
            old_name='from_timestamp',
            new_name='from_timestamp_s',
        ),
        migrations.RenameField(
            model_name='roomnodeinstallation',
            old_name='to_timestamp',
            new_name='to_timestamp_s',
        ),
        migrations.AlterField(
            model_name='membership',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.organization'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='organization',
            name='users',
            field=models.ManyToManyField(related_name='organizations', through='core.Membership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='room',
            name='nodes',
            field=models.ManyToManyField(related_name='rooms', through='core.RoomNodeInstallation', to='core.Node'),
        ),
        migrations.AddConstraint(
            model_name='roomnodeinstallation',
            constraint=models.UniqueConstraint(fields=('node', 'from_timestamp_s'), name='unique_node_installation'),
        ),
    ]

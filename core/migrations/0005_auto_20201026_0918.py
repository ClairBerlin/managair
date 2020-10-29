# Generated by Django 3.1.2 on 2020-10-26 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20201026_0900'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='site',
            name='nodes',
        ),
        migrations.AddField(
            model_name='room',
            name='nodes',
            field=models.ManyToManyField(through='core.RoomNodeInstallation', to='core.Node'),
        ),
        migrations.DeleteModel(
            name='NodeInstallation',
        ),
    ]

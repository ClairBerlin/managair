# Generated by Django 3.1.2 on 2020-10-29 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20201027_1405'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='alias',
            field=models.CharField(max_length=100),
        ),
    ]

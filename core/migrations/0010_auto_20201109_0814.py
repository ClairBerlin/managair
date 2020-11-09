# Generated by Django 3.1.3 on 2020-11-09 08:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0009_auto_20201104_2058'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='node',
            options={'get_latest_by': 'eui64', 'ordering': ['eui64']},
        ),
        migrations.RenameField(
            model_name='node',
            old_name='device_id',
            new_name='eui64',
        ),
        migrations.AlterField(
            model_name='membership',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='core.organization'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL),
        ),
    ]

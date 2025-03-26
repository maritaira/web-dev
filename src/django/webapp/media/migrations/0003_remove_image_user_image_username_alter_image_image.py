# Generated by Django 5.1.5 on 2025-01-29 18:01

import media.models
import webapp.storages
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0002_alter_image_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='user',
        ),
        migrations.AddField(
            model_name='image',
            name='username',
            field=models.CharField(default='default_user', max_length=255),
        ),
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(storage=webapp.storages.CarsBucketStorage, upload_to=media.models.image_upload_to),
        ),
    ]

# Generated by Django 3.2.16 on 2023-01-18 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowerapp', '0003_consultation'),
    ]

    operations = [
        migrations.AddField(
            model_name='bouquet',
            name='is_recommended',
            field=models.BooleanField(default=False, verbose_name='рекомендованный'),
        ),
    ]

# Generated by Django 4.2.19 on 2025-03-09 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentscan',
            name='content',
            field=models.TextField(default=''),
        ),
    ]

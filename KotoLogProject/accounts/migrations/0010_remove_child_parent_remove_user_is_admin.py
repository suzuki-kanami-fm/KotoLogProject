# Generated by Django 5.0.7 on 2024-10-12 17:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_user_is_admin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='child',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_admin',
        ),
    ]
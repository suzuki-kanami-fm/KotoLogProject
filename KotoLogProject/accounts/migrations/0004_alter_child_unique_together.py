# Generated by Django 4.1 on 2024-10-07 13:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_child_parent_alter_child_family_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='child',
            unique_together={('family', 'child_name', 'birthday')},
        ),
    ]

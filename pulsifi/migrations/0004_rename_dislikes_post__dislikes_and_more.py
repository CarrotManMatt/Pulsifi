# Generated by Django 4.1.3 on 2022-11-26 21:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pulsifi', '0003_alter_post_creator'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='dislikes',
            new_name='_dislikes',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='likes',
            new_name='_likes',
        ),
    ]

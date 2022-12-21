# Generated by Django 4.1.4 on 2022-12-21 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulsifi', '0002_alter_report_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pulse',
            name='_dislikes',
        ),
        migrations.RemoveField(
            model_name='pulse',
            name='_likes',
        ),
        migrations.RemoveField(
            model_name='reply',
            name='_dislikes',
        ),
        migrations.RemoveField(
            model_name='reply',
            name='_likes',
        ),
        migrations.AddField(
            model_name='pulse',
            name='disliked_by',
            field=models.ManyToManyField(blank=True, related_name='disliked_pulses', to='pulsifi.profile'),
        ),
        migrations.AddField(
            model_name='pulse',
            name='liked_by',
            field=models.ManyToManyField(blank=True, related_name='liked_pulses', to='pulsifi.profile'),
        ),
        migrations.AddField(
            model_name='reply',
            name='disliked_by',
            field=models.ManyToManyField(blank=True, related_name='disliked_replies', to='pulsifi.profile'),
        ),
        migrations.AddField(
            model_name='reply',
            name='liked_by',
            field=models.ManyToManyField(blank=True, related_name='liked_replies', to='pulsifi.profile'),
        ),
    ]

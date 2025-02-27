# Generated by Django 4.1.7 on 2023-03-29 00:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('pulsifi', '0002_alter_report_assigned_moderator'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pulse',
            old_name='visible',
            new_name='is_visible',
        ),
        migrations.RenameField(
            model_name='reply',
            old_name='visible',
            new_name='is_visible',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='verified',
            new_name='is_verified',
        ),
        migrations.AlterField(
            model_name='report',
            name='_content_type',
            field=models.ForeignKey(help_text='Link to the content type of the reported_object instance (either :model:`pulsifi.user`, :model:`pulsifi.pulse` or :model:`pulsifi.reply`).', limit_choices_to={'app_label': 'pulsifi', 'model__in': ('user', 'pulse', 'reply')}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Reported Object Type'),
        ),
        migrations.AlterField(
            model_name='report',
            name='assigned_moderator',
            field=models.ForeignKey(blank=True, help_text='Link to the :model:`pulsifi.user` object instance (from the set of moderators) that has been assigned to moderate this report.', limit_choices_to={'groups__name': 'Moderators', 'is_active': True}, on_delete=django.db.models.deletion.CASCADE, related_name='moderator_assigned_report_set', to=settings.AUTH_USER_MODEL, verbose_name='Assigned Moderator'),
        ),
    ]

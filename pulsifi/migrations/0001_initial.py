# Generated by Django 4.1.3 on 2022-11-29 00:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Visible_Model',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visible', models.BooleanField(default=True, verbose_name='Visibility')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('visible_model_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pulsifi.visible_model')),
                ('name', models.CharField(max_length=30, verbose_name='Name')),
                ('bio', models.TextField(blank=True, max_length=200, null=True, verbose_name='Bio')),
                ('profile_pic', models.ImageField(blank=True, null=True, upload_to='profile_pic', verbose_name='Profile Picture')),
                ('_base_user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('following', models.ManyToManyField(blank=True, related_name='followers', to='pulsifi.profile')),
            ],
            options={
                'verbose_name': 'User',
            },
            bases=('pulsifi.visible_model',),
        ),
        migrations.CreateModel(
            name='Pulse',
            fields=[
                ('visible_model_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pulsifi.visible_model')),
                ('message', models.TextField(verbose_name='Message')),
                ('unlisted', models.BooleanField(default=False, verbose_name='Unlisted')),
                ('_likes', models.PositiveIntegerField(default=0, verbose_name='Number of Likes')),
                ('_dislikes', models.PositiveIntegerField(default=0, verbose_name='Number of Dislikes')),
                ('_date_time_created', models.DateTimeField(auto_now=True, verbose_name='Creation Date & Time')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pulses_and_replies', to='pulsifi.profile', verbose_name='Creator')),
            ],
            options={
                'verbose_name': 'Pulse',
            },
            bases=('pulsifi.visible_model',),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_object_id', models.PositiveIntegerField()),
                ('reason', models.TextField(verbose_name='Reason')),
                ('category', models.CharField(choices=[('SPM', 'Spam'), ('SEX', 'Nudity or sexual activity'), ('HAT', 'Hate speech or symbols'), ('VIO', 'Violence or dangerous organisations'), ('IGL', 'Sale of illegal or regulated goods'), ('BUL', 'Bullying or harassment'), ('INP', 'Intellectual property violation'), ('INJ', 'Suicide or self-injury'), ('SCM', 'Scam or fraud'), ('FLS', 'False or misleading information')], max_length=3, verbose_name='Category')),
                ('status', models.CharField(choices=[('PR', 'In progress'), ('RE', 'Resolved')], max_length=2, verbose_name='Status')),
                ('_date_time_created', models.DateTimeField(auto_now=True, verbose_name='Creation Date & Time')),
                ('_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pulsifi.profile', verbose_name='Reporter')),
            ],
            options={
                'verbose_name': 'Reply',
            },
        ),
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('pulse_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='pulsifi.pulse')),
                ('_object_id', models.PositiveIntegerField()),
                ('_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('_original_pulse', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='pulsifi.pulse', verbose_name='Original Pulse')),
            ],
            options={
                'verbose_name': 'Reply',
            },
            bases=('pulsifi.pulse',),
        ),
    ]

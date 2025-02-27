# Generated by Django 4.1.7 on 2023-03-27 01:57

import django.contrib.auth.models
import django.core.validators
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import pulsifi.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, unique=True, validators=[django.core.validators.RegexValidator('^[\\w.-]+\\Z', 'Enter a valid username. This value may contain only letters, digits and ./_ characters.'), pulsifi.validators.ReservedUsernameValidator(), pulsifi.validators.ConfusableUsernameValidator()], verbose_name='Username')),
                ('email', models.EmailField(error_messages={'unique': 'That Email Address is already in use by another user.'}, max_length=254, unique=True, validators=[pulsifi.validators.HTML5EmailValidator(), pulsifi.validators.FreeEmailValidator(), pulsifi.validators.ConfusableEmailValidator(), pulsifi.validators.PreexistingEmailTLDValidator(), pulsifi.validators.ExampleEmailValidator()], verbose_name='Email Address')),
                ('bio', models.TextField(blank=True, help_text='Longer textfield containing an autobiographical description of this user.', max_length=200, verbose_name='Bio')),
                ('verified', models.BooleanField(default=False, help_text='Boolean flag to indicate whether this user is a noteable person/organisation.', verbose_name='Is verified?')),
                ('is_staff', models.BooleanField(default=False, help_text='Boolean flag to indicate whether this user is a staff member, and thus can log into the admin site.', verbose_name='Is a staff member?')),
                ('is_superuser', models.BooleanField(default=False, help_text='Boolean flag to provide a quick way to designate that this user has all permissions without explicitly assigning them.', verbose_name='Is a superuser?')),
                ('is_active', models.BooleanField(default=True, help_text='Boolean flag to determine whether this object should be accessible to the website. Use this flag instead of deleting objects.', verbose_name='Is visible?')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='Date Joined')),
                ('last_login', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Last Login')),
            ],
            options={
                'verbose_name': 'User',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_date_time_created', models.DateTimeField(auto_now=True, help_text='Datetime object representing the date & time that this object instance was created.', verbose_name='Creation Date & Time')),
                ('_object_id', models.PositiveIntegerField(help_text='ID number of the specific instance of the reported_object instance.', verbose_name='Reported Object ID')),
                ('reason', models.TextField(help_text="Longer textfield containing an detailed description of the reason for this report's existence.", verbose_name='Reason')),
                ('category', models.CharField(choices=[('SPM', 'Spam'), ('SEX', 'Nudity or sexual activity'), ('HAT', 'Hate speech or symbols'), ('VIO', 'Violence or dangerous organisations'), ('ILG', 'Sale of illegal or regulated goods'), ('BUL', 'Bullying or harassment'), ('INP', 'Intellectual property violation or impersonation'), ('INJ', 'Suicide or self-injury'), ('SCM', 'Scam or fraud'), ('FLS', 'False or misleading information')], help_text='The category code that gives an overview as to the reason for the report.', max_length=3, verbose_name='Category')),
                ('status', models.CharField(choices=[('PR', 'In Progress'), ('RE', 'Rejected'), ('CM', 'Completed')], default='PR', help_text='The status code that outlines the current position within the moderation cycle that this report is within.', max_length=2, verbose_name='Status')),
                ('_content_type', models.ForeignKey(help_text='Link to the content type of the reported_object instance (either :model:`pulsifi.user`, :model:`pulsifi.pulse` or :model:`pulsifi.reply`).', limit_choices_to={'app_label': 'pulsifi', 'model__in': ['user', 'pulse', 'reply']}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Reported Object Type')),
                ('assigned_moderator', models.ForeignKey(blank=True, help_text='Link to the :model:`pulsifi.user` object instance (from the set of moderators) that has been assigned to moderate this report.', limit_choices_to={'groups__name': 'Moderators', 'is_active': True}, on_delete=django.db.models.deletion.CASCADE, related_name='moderator_assigned_report_set', to=settings.AUTH_USER_MODEL, verbose_name='Assigned Moderator')),
                ('reporter', models.ForeignKey(help_text='Link to the :model:`pulsifi.user` object instance that created this report.', on_delete=django.db.models.deletion.CASCADE, related_name='submitted_report_set', to=settings.AUTH_USER_MODEL, verbose_name='Reporter')),
            ],
            options={
                'verbose_name': 'Report',
            },
        ),
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_date_time_created', models.DateTimeField(auto_now=True, help_text='Datetime object representing the date & time that this object instance was created.', verbose_name='Creation Date & Time')),
                ('message', models.TextField(verbose_name='Message')),
                ('visible', models.BooleanField(default=True, help_text='Boolean flag to determine whether this object should be accessible to the website. Use this flag instead of deleting objects.', verbose_name='Is visible?')),
                ('_object_id', models.PositiveIntegerField(help_text='ID number of the specific instance of the replied_content instance.', verbose_name='Replied Content ID')),
                ('_content_type', models.ForeignKey(help_text='Link to the content type of the replied_content instance (either :model:`pulsifi.pulse` or :model:`pulsifi.reply`).', limit_choices_to={'app_label': 'pulsifi', 'model__in': ('pulse', 'reply')}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Replied Content Type')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('disliked_by', models.ManyToManyField(blank=True, help_text='The set of :model:`pulsifi.user` instances that have disliked this content object instance.', related_name='disliked_%(class)s_set', to=settings.AUTH_USER_MODEL)),
                ('liked_by', models.ManyToManyField(blank=True, help_text='The set of :model:`pulsifi.user` instances that have liked this content object instance.', related_name='liked_%(class)s_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reply',
                'verbose_name_plural': 'Replies',
            },
        ),
        migrations.CreateModel(
            name='Pulse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_date_time_created', models.DateTimeField(auto_now=True, help_text='Datetime object representing the date & time that this object instance was created.', verbose_name='Creation Date & Time')),
                ('message', models.TextField(verbose_name='Message')),
                ('visible', models.BooleanField(default=True, help_text='Boolean flag to determine whether this object should be accessible to the website. Use this flag instead of deleting objects.', verbose_name='Is visible?')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Creator')),
                ('disliked_by', models.ManyToManyField(blank=True, help_text='The set of :model:`pulsifi.user` instances that have disliked this content object instance.', related_name='disliked_%(class)s_set', to=settings.AUTH_USER_MODEL)),
                ('liked_by', models.ManyToManyField(blank=True, help_text='The set of :model:`pulsifi.user` instances that have liked this content object instance.', related_name='liked_%(class)s_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pulse',
            },
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('followed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following_set', to=settings.AUTH_USER_MODEL)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Following Link',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='following',
            field=models.ManyToManyField(blank=True, help_text='Set of other :model:`pulsifi.user` objects that this user is following.', related_name='followers', through='pulsifi.Follow', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['_content_type', '_object_id'], name='pulsifi_rep__conten_e403cf_idx'),
        ),
        migrations.AddIndex(
            model_name='reply',
            index=models.Index(fields=['_content_type', '_object_id'], name='pulsifi_rep__conten_eaffc4_idx'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('follower', 'followed'), name='follow_once'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(('follower', models.F('followed')), _negated=True), name='not_follow_self'),
        ),
    ]

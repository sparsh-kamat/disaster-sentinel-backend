# Generated by Django 5.1.5 on 2025-04-16 13:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0006_alter_existingagencies_table'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VolunteerInterest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(blank=True, help_text='Optional message submitted by the volunteer.', null=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp indicating when the interest was submitted.')),
                ('agency', models.ForeignKey(help_text='The agency the user is interested in volunteering for.', limit_choices_to={'role': 'agency'}, on_delete=django.db.models.deletion.CASCADE, related_name='received_volunteer_interests', to=settings.AUTH_USER_MODEL)),
                ('volunteer', models.ForeignKey(help_text='The user expressing interest in volunteering.', limit_choices_to={'role': 'user'}, on_delete=django.db.models.deletion.CASCADE, related_name='volunteer_interests_submitted', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Volunteer Interest',
                'verbose_name_plural': 'Volunteer Interests',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='AgencyMemberPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view_missing', models.BooleanField(default=False, verbose_name='Can View Missing Person Reports')),
                ('can_edit_missing', models.BooleanField(default=False, verbose_name='Can Edit Missing Person Reports')),
                ('can_view_announcements', models.BooleanField(default=False, verbose_name='Can View Agency Announcements')),
                ('can_edit_announcements', models.BooleanField(default=False, verbose_name='Can Edit Agency Announcements')),
                ('can_make_announcements', models.BooleanField(default=False, verbose_name='Can Create New Agency Announcements')),
                ('can_manage_volunteers', models.BooleanField(default=False, verbose_name='Can Manage Agency Volunteers')),
                ('is_agency_admin', models.BooleanField(default=False, verbose_name='Is Agency Admin')),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agency', models.ForeignKey(help_text='The agency granting the permissions.', limit_choices_to={'role': 'agency'}, on_delete=django.db.models.deletion.CASCADE, related_name='granted_permissions', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(help_text='The user receiving the permissions.', on_delete=django.db.models.deletion.CASCADE, related_name='agency_permissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Agency Member Permission',
                'verbose_name_plural': 'Agency Member Permissions',
                'ordering': ['agency', 'member'],
                'unique_together': {('agency', 'member')},
            },
        ),
    ]

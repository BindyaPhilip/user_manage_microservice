# Generated by Django 5.2 on 2025-04-27 06:54

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_rustalert'),
    ]

    operations = [
        migrations.AddField(
            model_name='communitypost',
            name='crop_type',
            field=models.CharField(choices=[('MAIZE', 'MAIZE'), ('WHEAT', 'WHEAT'), ('RICE', 'RICE'), ('BEANS', 'BEANS'), ('POTATOES', 'POTATOES')], default='MAIZE', max_length=50),
        ),
        migrations.AddField(
            model_name='communitypost',
            name='disease_type',
            field=models.CharField(choices=[('common_rust', 'COMMON_RUST'), ('leaf_blast', 'LEAF_BLAST'), ('gray_leaf_spot', 'GRAY_LEAF_SPOT'), ('none', 'NONE')], default='none', max_length=50),
        ),
        migrations.AddField(
            model_name='communitypost',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='post_images'),
        ),
        migrations.AddField(
            model_name='communitypost',
            name='rust_detection',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='communitypost',
            name='urgency_level',
            field=models.CharField(choices=[('low', 'LOW'), ('medium', 'MEDIUM'), ('high', 'HIGH')], default='low', max_length=20),
        ),
        migrations.AddField(
            model_name='expertprofile',
            name='validated_responses_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='points',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='CommunityResponse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('expert_comment', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_responses', to=settings.AUTH_USER_MODEL)),
                ('farmer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_responses', to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='accounts.communitypost')),
            ],
        ),
        migrations.CreateModel(
            name='PointTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('points', models.IntegerField()),
                ('reason', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='point_transactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

# Generated by Django 5.1.2 on 2024-11-25 17:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_app', '0005_review_reply'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='review',
            name='order_id',
        ),
        migrations.AddField(
            model_name='review',
            name='order',
            field=models.ForeignKey(default=28, on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='business_app.order'),
            preserve_default=False,
        ),
    ]
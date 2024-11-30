# Generated by Django 5.1.2 on 2024-11-28 18:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_app', '0007_remove_review_order_review_order_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reply',
            name='review',
        ),
        migrations.AddField(
            model_name='review',
            name='reply',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review', to='business_app.reply'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('delivery', 'Delivery'), ('cancelled', 'Canceled'), ('completed', 'Completed')], default='confirmed', max_length=20),
        ),
    ]
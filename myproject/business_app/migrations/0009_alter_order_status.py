# Generated by Django 5.1.2 on 2024-12-08 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_app', '0008_remove_reply_review_review_reply_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('delivery', 'Delivery'), ('canceled', 'Canceled'), ('completed', 'Completed')], default='confirmed', max_length=20),
        ),
    ]

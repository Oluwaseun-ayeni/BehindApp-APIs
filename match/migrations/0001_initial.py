# Generated by Django 4.2.13 on 2024-06-14 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_score', models.IntegerField()),
                ('status', models.CharField(max_length=20)),
            ],
        ),
    ]
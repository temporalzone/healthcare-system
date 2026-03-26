from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_emailotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailotp',
            name='failed_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='emailotp',
            name='locked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

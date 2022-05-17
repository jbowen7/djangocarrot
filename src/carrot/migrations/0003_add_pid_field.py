from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carrot', '0002_auto_20200324_2313'),
    ]

    operations = [
		migrations.AddField('Task', 'pid', models.IntegerField(blank=True, null=True)),
    ]

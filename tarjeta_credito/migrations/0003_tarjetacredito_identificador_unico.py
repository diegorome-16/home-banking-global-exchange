# Generated migration for adding identificador_unico field

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tarjeta_credito', '0002_alter_tarjetacredito_marca'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarjetacredito',
            name='identificador_unico',
            field=models.UUIDField(default=uuid.uuid4, editable=False, help_text='Identificador único de la tarjeta para uso en APIs', unique=True),
        ),
    ]

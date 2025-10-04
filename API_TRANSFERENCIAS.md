# API de Transferencias

## Endpoint para Realizar Transferencias

### POST `/transferencia/api/realizar/`

Este endpoint permite realizar transferencias entre cuentas bancarias.

#### Parámetros de entrada (JSON):

```json
{
    "cuenta_origen": "1234567890123456",
    "cuenta_destino": "6543210987654321", 
    "monto": 1000.50,
    "motivo": "Pago de servicios"
}
```

- **cuenta_origen** (string, requerido): Número de cuenta de 16 dígitos desde donde se enviará el dinero
- **cuenta_destino** (string, requerido): Número de cuenta de 16 dígitos que recibirá el dinero
- **monto** (number, requerido): Cantidad a transferir (debe ser mayor a 0)
- **motivo** (string, opcional): Concepto o motivo de la transferencia

#### Respuestas:

##### Transferencia exitosa (201):
```json
{
    "success": true,
    "message": "Transferencia realizada exitosamente",
    "transferencia": {
        "referencia": "TRF20251002ABC12345",
        "monto": "1000.50",
        "concepto": "Pago de servicios",
        "estado": "COMPLETADA",
        "estado_display": "Completada",
        "fecha_creacion": "2025-10-02T14:30:00.123456Z",
        "fecha_procesamiento": "2025-10-02T14:30:00.234567Z",
        "cuenta_origen": {
            "numero_cuenta": "1234567890123456",
            "usuario": "usuario1",
            "saldo_actual": "4999.50"
        },
        "cuenta_destino": {
            "numero_cuenta": "6543210987654321", 
            "usuario": "usuario2",
            "saldo_actual": "2000.50"
        }
    }
}
```

##### Errores comunes:

**Parámetros faltantes (400):**
```json
{
    "success": false,
    "error": "Parámetros faltantes",
    "message": "Se requieren: cuenta_origen, cuenta_destino y monto"
}
```

**Saldo insuficiente (400):**
```json
{
    "success": false,
    "error": "Saldo insuficiente",
    "message": "Saldo disponible: 500.00, Monto solicitado: 1000.50"
}
```

**Cuenta no encontrada (404):**
```json
{
    "success": false,
    "error": "Cuenta origen no encontrada",
    "message": "No existe una cuenta activa con el número: 1234567890123456"
}
```

**Transferencia a misma cuenta (400):**
```json
{
    "success": false,
    "error": "Transferencia inválida",
    "message": "No se puede transferir a la misma cuenta"
}
```

## Endpoint para Consultar Transferencias

### GET `/transferencia/api/consultar/<referencia>/`

Consulta los datos de una transferencia existente por su número de referencia.

#### Ejemplo de uso:
```
GET /transferencia/api/consultar/TRF20251002ABC12345/
```

#### Respuesta exitosa (200):
```json
{
    "success": true,
    "tipo": "transferencia",
    "transferencia": {
        "referencia": "TRF20251002ABC12345",
        "monto": "1000.50",
        "concepto": "Pago de servicios",
        "estado": "COMPLETADA",
        "estado_display": "Completada",
        "fecha_creacion": "2025-10-02T14:30:00.123456Z",
        "fecha_procesamiento": "2025-10-02T14:30:00.234567Z",
        "cuenta_origen": {
            "numero_cuenta": "1234567890123456",
            "usuario": "usuario1",
            "tipo_cuenta": "Cuenta de Ahorro"
        },
        "cuenta_destino": {
            "numero_cuenta": "6543210987654321",
            "usuario": "usuario2", 
            "tipo_cuenta": "Cuenta Corriente"
        }
    }
}
```

## Ejemplo de uso con curl:

```bash
# Realizar una transferencia
curl -X POST http://localhost:8000/transferencia/api/realizar/ \
  -H "Content-Type: application/json" \
  -d '{
    "cuenta_origen": "1234567890123456",
    "cuenta_destino": "6543210987654321",
    "monto": 1000.50,
    "motivo": "Pago de servicios"
  }'

# Consultar una transferencia
curl -X GET http://localhost:8000/transferencia/api/consultar/TRF20251002ABC12345/
```

## Validaciones implementadas:

1. **Formato JSON válido**: El cuerpo de la petición debe ser JSON válido
2. **Parámetros requeridos**: cuenta_origen, cuenta_destino y monto son obligatorios
3. **Monto válido**: Debe ser un número mayor a 0
4. **Cuentas existentes**: Ambas cuentas deben existir y estar activas
5. **Cuentas diferentes**: No se puede transferir a la misma cuenta
6. **Saldo suficiente**: La cuenta origen debe tener saldo suficiente
7. **Transaccionalidad**: La operación es atómica (todo o nada)

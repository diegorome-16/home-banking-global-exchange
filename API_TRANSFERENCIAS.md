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

---

## Endpoints para Listar Transferencias por Usuario (NUEVO)

Estos endpoints devuelven las transferencias asociadas a un usuario. Aceptan el username de dos maneras:

- Recomendado: Query string en GET: `?username=<usuario>`
- También soportado: Body JSON en GET: `{ "username": "<usuario>" }`

Notas:
- Aunque no es común enviar body en GET, el backend soporta ambas formas por conveniencia.
- Las respuestas retornan un arreglo de objetos Transferencia con todos los campos del modelo.

### GET `/cuenta/api/transferencias/enviadas/`

Lista las transferencias realizadas por el usuario (donde su cuenta es cuenta_origen).

Parámetros:
- `username` (string, requerido) en query string o body JSON.

Ejemplos:

```bash
# Query string (recomendado)
curl "http://localhost:8000/cuenta/api/transferencias/enviadas/?username=karen"

# Body JSON en GET (alternativo)
curl -X GET "http://localhost:8000/cuenta/api/transferencias/enviadas/" \
  -H "Content-Type: application/json" \
  --data '{"username":"karen"}'
```

Respuesta (200):
```json
{
  "count": 2,
  "results": [
    {
      "id": 5,
      "cuenta_origen_id": 1,
      "cuenta_destino_id": 2,
      "monto": "1000.50",
      "concepto": "Pago",
      "estado": "COMPLETADA",
      "fecha_creacion": "2025-10-02T14:30:00.123456Z",
      "fecha_procesamiento": "2025-10-02T14:30:00.234567Z",
      "referencia": "TRF20251002ABC12345"
    }
  ]
}
```

Errores comunes:

- 400 Username requerido
```json
{ "detail": "username es requerido" }
```

- 404 Usuario o cuenta inexistente
```json
{ "detail": "Usuario no existe" }
```
```json
{ "detail": "El usuario no tiene cuenta" }
```

### GET `/cuenta/api/transferencias/recibidas/`

Lista las transferencias recibidas por el usuario (donde su cuenta es cuenta_destino).

Parámetros y ejemplos: mismos que el endpoint de enviadas.

Respuesta (200):
```json
{
  "count": 1,
  "results": [
    {
      "id": 7,
      "cuenta_origen_id": 3,
      "cuenta_destino_id": 1,
      "monto": "2500.00",
      "concepto": "Reembolso",
      "estado": "COMPLETADA",
      "fecha_creacion": "2025-10-05T12:00:00.000000Z",
      "fecha_procesamiento": "2025-10-05T12:00:00.500000Z",
      "referencia": "TRF20251005XYZ98765"
    }
  ]
}
```

---

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

# Listar transferencias por usuario (enviadas)
curl "http://localhost:8000/cuenta/api/transferencias/enviadas/?username=karen"

# Listar transferencias por usuario (recibidas)
curl "http://localhost:8000/cuenta/api/transferencias/recibidas/?username=karen"
```

## Validaciones implementadas:

1. **Formato JSON válido**: El cuerpo de la petición debe ser JSON válido
2. **Parámetros requeridos**: cuenta_origen, cuenta_destino y monto son obligatorios
3. **Monto válido**: Debe ser un número mayor a 0
4. **Cuentas existentes**: Ambas cuentas deben existir y estar activas
5. **Cuentas diferentes**: No se puede transferir a la misma cuenta
6. **Saldo suficiente**: La cuenta origen debe tener saldo suficiente
7. **Transaccionalidad**: La operación es atómica (todo o nada)

### Validaciones adicionales para listados por usuario
- `username` es obligatorio
- Si el usuario no existe → 404
- Si el usuario no tiene cuenta → 404

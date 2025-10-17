# API de Tarjetas de Crédito

## Endpoints Disponibles

### 1. Solicitar Nueva Tarjeta de Crédito (ACTUALIZADO)

**POST** `/tarjeta-credito/api/solicitar/`

Permite solicitar una nueva tarjeta de crédito para un usuario SIN sesión. Requiere `username` en el body.

#### Parámetros de entrada (JSON):
```json
{
    "username": "usuario_destino",
    "marca": "CABAL",
    "limite_credito": 100000
}
```

- **username** (string, requerido): Username del titular de la tarjeta
- **marca** (string, opcional): Marca de la tarjeta. Opciones según el modelo: "CABAL", "CREDICARD". Por defecto: "CABAL"
- **limite_credito** (number, opcional): Límite de crédito solicitado entre $10,000 y $500,000. Por defecto: $50,000

#### Respuesta exitosa (201):
```json
{
    "success": true,
    "message": "Tarjeta de crédito creada exitosamente",
    "tarjeta": {
        "id": 1,
        "numero_enmascarado": "**** **** **** 1234",
        "marca": "CABAL",
        "marca_display": "Cabal",
        "ultimos_4_digitos": "1234",
        "fecha_vencimiento": "2028-10-03",
        "estado": "ACTIVA",
        "estado_display": "Activa",
        "limite_credito": "100000.00",
        "credito_disponible": "100000.00",
        "fecha_creacion": "2025-10-03T14:30:00.123456Z",
        "usuario": "usuario_destino"
    }
}
```

#### Errores comunes
- 400 username requerido
```json
{ "success": false, "error": "username requerido", "message": "Debe indicar el username del titular de la tarjeta" }
```
- 404 Usuario no encontrado
```json
{ "success": false, "error": "Usuario no encontrado", "message": "No existe un usuario con username: <username>" }
```
- 400 Marca inválida / Límite inválido

---

### 2. Consultar Tarjeta por Número (NUEVO)

**GET** `/tarjeta-credito/api/consultar-numero/<numero_tarjeta>/`

**FUNCIONALIDAD PRINCIPAL**: Consulta una tarjeta de crédito usando únicamente su número de 16 dígitos y retorna su identificador único.

#### Ejemplo de uso:
```
GET /tarjeta-credito/api/consultar-numero/1234567890123456/
```

#### Respuesta exitosa (200):
```json
{
    "success": true,
    "encontrada": true,
    "message": "Tarjeta encontrada exitosamente",
    "tarjeta": {
        "identificador_unico": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "numero_enmascarado": "**** **** **** 3456",
        "marca": "CABAL",
        "marca_display": "Cabal",
        "estado": "ACTIVA",
        "estado_display": "Activa",
        "usuario": "nombre_usuario"
    }
}
```

#### Respuesta cuando no se encuentra la tarjeta (404):
```json
{
    "success": false,
    "encontrada": false,
    "error": "Tarjeta no encontrada",
    "message": "No existe una tarjeta con el número: 1234567890123456",
    "tarjeta": null
}
```

---

### 3. Consultar Tarjeta por ID Interno

**GET** `/tarjeta-credito/api/consultar/<tarjeta_id>/`

Consulta una tarjeta de crédito usando su ID interno del sistema.

#### Respuesta exitosa (200):
```json
{
    "success": true,
    "tarjeta": {
        "id": 1,
        "numero_enmascarado": "**** **** **** 1234",
        "marca": "CABAL",
        "marca_display": "Cabal",
        "ultimos_4_digitos": "1234",
        "fecha_vencimiento": "2028-10-03",
        "estado": "ACTIVA",
        "estado_display": "Activa",
        "limite_credito": "100000.00",
        "credito_disponible": "100000.00",
        "credito_utilizado": "0.00",
        "esta_vencida": false,
        "fecha_creacion": "2025-10-03T14:30:00.123456Z",
        "usuario": "nombre_usuario"
    }
}
```

---

### 4. Listar Tarjetas por Usuario (NUEVO)

**GET** `/tarjeta-credito/api/tarjetas/?username=<usuario>`

Lista todas las tarjetas pertenecientes al usuario indicado por `username`.

#### Respuesta exitosa (200):
```json
{
  "success": true,
  "usuario": "karen",
  "count": 2,
  "results": [
    {
      "id": 10,
      "identificador_unico": "2b9e3d24-...",
      "numero_enmascarado": "**** **** **** 1234",
      "marca": "CABAL",
      "marca_display": "Cabal",
      "ultimos_4_digitos": "1234",
      "fecha_vencimiento": "2028-10-03",
      "estado": "ACTIVA",
      "estado_display": "Activa",
      "limite_credito": 100000.0,
      "credito_disponible": 80000.0,
      "fecha_creacion": "2025-10-03T14:30:00.123456Z"
    }
  ]
}
```

#### Errores comunes
- 400 Falta username en query string
- 404 Usuario no encontrado

---

## Casos de Uso del Identificador Único

### ¿Por qué usar el identificador único?

1. **Seguridad**: El número de tarjeta es información sensible que no debería exponerse en URLs o logs
2. **Escalabilidad**: El identificador UUID permite referencias únicas sin exponer información interna
3. **APIs Futuras**: Permite crear endpoints seguros usando el identificador en lugar del número de tarjeta

### Flujo de Trabajo Recomendado:

```bash
# 1. Solicitar una nueva tarjeta (sin sesión)
curl -X POST http://localhost:8000/tarjeta-credito/api/solicitar/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_destino",
    "marca": "CABAL",
    "limite_credito": 150000
  }'

# 2. Consultar tarjeta por número para obtener identificador único
curl -X GET http://localhost:8000/tarjeta-credito/api/consultar-numero/1234567890123456/

# 3. Consultar tarjeta por ID interno
curl -X GET http://localhost:8000/tarjeta-credito/api/consultar/1/

# 4. Listar tarjetas por usuario
curl -X GET "http://localhost:8000/tarjeta-credito/api/tarjetas/?username=karen"
```

---

## Validaciones Implementadas

### Para solicitar tarjeta:
- `username` requerido y usuario existente
- Marca válida según `MARCA_CHOICES`: CABAL, CREDICARD
- Límite entre 10,000 y 500,000
- Usuario no debe tener tarjeta activa/bloqueada

### Para consulta por número:
- **Formato de número**: Debe ser exactamente 16 dígitos
- **Existencia**: Verifica que la tarjeta existe en el sistema
- **Estado**: Retorna el estado actual de la tarjeta
- **Seguridad**: No expone información sensible como CVC o fecha de vencimiento

### Campos del Modelo TarjetaCredito:
- **identificador_unico**: UUID generado automáticamente, único e inmutable
- **numero_tarjeta**: Número de 16 dígitos único generado con algoritmo Luhn
- **ultimos_4_digitos**: Últimos 4 dígitos para visualización segura
- **marca**: CABAL o CREDICARD
- **cvc**: 3 dígitos (4 para American Express, actualmente deshabilitado)
- **fecha_vencimiento**: 3 años desde la creación
- **estado**: ACTIVA, BLOQUEADA, VENCIDA, CANCELADA
- **limite_credito** y **credito_disponible**: Gestión del crédito

# Modelo de Identidades - AbandonPro

Este documento describe el esquema de identificación de entidades del sistema AbandonPro.

---

## 1. Pozos

**Formato:** Código de campo petrolero (letra-número)

**Ejemplos:**
- X-123
- P-001
- A-321

**Validación:**
```python
def validar_pozo_id(pozo_id):
    return isinstance(pozo_id, str) and len(pozo_id) >= 3
```

---

## 2. Recursos (Personal)

**Formato:** NOMBRE_APELLIDO (todo mayúsculas, guión bajo)

**Ejemplos:**
- JUAN_PEREZ
- ROBERTO_RUIZ
- MARIA_GONZALEZ
- SEBASTIAN_CANES

**Validación:**
```python
def validar_recurso_id(recurso_id):
    return isinstance(recurso_id, str) and "_" in recurso_id
```

---

## 3. Equipos

**Formato:** TIPO_NUMERO (mayúsculas)

**Ejemplos:**
- PULLING_01
- CISTERNA_01
- CAMION_01
- RIG_001

**Tipos válidos:** PULLING, CISTERNA, CAMION, RIG, TRUCK

**Validación:**
```python
def validar_equipo_id(equipo_id):
    prefijos_validos = ("PULLING", "CISTERNA", "CAMION", "RIG", "TRUCK")
    return equipo_id.startswith(prefijos_validos) if equipo_id else False
```

---

## 4. Contratos

**Formato:** ID numérico incremental

**Ejemplos:**
- 1 (SureOil)
- 2 (YPF)
- 3 (Petrobras)

**Validación:**
```python
def validar_contrato_id(contrato_id):
    return isinstance(contrato_id, int) and contrato_id > 0
```

---

## 5. Expedientes

**Formato:** Hereda el ID del pozo

**Ejemplo:**
- X-123 (el mismo que el pozo)

---

## 6. Catálogo Maestro

Los catálogos de referencia están en:

| Entidad | Archivo |
|---------|---------|
| Pozos | `persistence_db.json` |
| Recursos | `mock_api_client.py` |
| Equipos | `mock_api_client.py` |
| Contratos | `financial_service_mock.py` |

---

## 7. Estrategia de Mapeo Externo (Futuro)

Cuando el sistema se conecte a fuentes externas (telemetría, SCADA, sistemas de terceros), se necesitará una tabla de mapeo.

### Tabla propuesta: `tbl_equipo_mapeo_externo`

| Campo | Descripción |
|-------|-------------|
| equipo_id_interno | ID interno del sistema (ej: PULLING_01) |
| equipo_id_fabricante | ID del fabricante (ej: RIG-17) |
| equipo_id_scada | ID en sistema SCADA |
| proveedor | Nombre del proveedor externo |

### Ejemplo de uso:

```
Interno: PULLING_01
Fabricante: RIG-17
SCADA: EQ-00417
```

### Implementación futura:

```python
def obtener_id_interno(fabricante_id):
    mapeo = {
        "RIG-17": "PULLING_01",
        "RIG-18": "PULLING_02",
    }
    return mapeo.get(fabricante_id, fabricante_id)
```

---

## 8. Reglas de Naming

1. **Pozos**: Siempre letra + número (código de campo)
2. **Recursos**: Siempre MAYÚSCULAS + guión bajo
3. **Equipos**: Siempre MAYÚSCULAS + guión bajo + número
4. **Contratos**: Siempre numérico

---

## 9. Notas

- Los IDs son case-sensitive
- No usar espacios ni caracteres especiales
- Mantener consistencia entre todos los módulos
- Validar antes de insertar en base de datos

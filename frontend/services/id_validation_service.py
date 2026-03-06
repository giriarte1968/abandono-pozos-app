"""
Servicio de Validación de IDs - AbandonPro

Validaciones livianas para prevenir errores de formato en IDs del sistema.

Uso:
    from services.id_validation_service import validar_pozo_id, validar_equipo_id, validar_recurso_id
"""

from typing import Union


def validar_pozo_id(pozo_id: str) -> bool:
    """
    Valida formato de ID de pozo.
    Formato esperado: X-123, P-001, A-321 (letra-número)
    
    Args:
        pozo_id: ID del pozo a validar
        
    Returns:
        True si el formato es válido
    """
    if not isinstance(pozo_id, str):
        return False
    if len(pozo_id) < 3:
        return False
    return True


def validar_recurso_id(recurso_id: str) -> bool:
    """
    Valida formato de ID de recurso (personal).
    Formato esperado: JUAN_PEREZ, ROBERTO_RUIZ (MAYUSCULAS_guión)
    
    Args:
        recurso_id: ID del recurso a validar
        
    Returns:
        True si el formato es válido
    """
    if not isinstance(recurso_id, str):
        return False
    if "_" not in recurso_id:
        return False
    if recurso_id != recurso_id.upper():
        return False
    return True


def validar_equipo_id(equipo_id: str) -> bool:
    """
    Valida formato de ID de equipo.
    Formato esperado: PULLING_01, CISTERNA_01 (TIPO_NUMERO)
    
    Args:
        equipo_id: ID del equipo a validar
        
    Returns:
        True si el formato es válido
    """
    if not isinstance(equipo_id, str):
        return False
    
    prefijos_validos = ("PULLING", "CISTERNA", "CAMION", "RIG", "TRUCK")
    
    if not any(equipo_id.startswith(p) for p in prefijos_validos):
        return False
    
    return True


def validar_contrato_id(contrato_id: Union[int, str]) -> bool:
    """
    Valida formato de ID de contrato.
    Formato esperado: 1, 2, 3 (numérico)
    
    Args:
        contrato_id: ID del contrato a validar
        
    Returns:
        True si el formato es válido
    """
    try:
        cid = int(contrato_id)
        return cid > 0
    except (ValueError, TypeError):
        return False


def validar_id_entidad(entidad: str, tipo: str) -> bool:
    """
    Validador genérico que redirige según el tipo de entidad.
    
    Args:
        entidad: ID a validar
        tipo: Tipo de entidad (pozo, recurso, equipo, contrato)
        
    Returns:
        True si la validación pasa
    """
    validadores = {
        "pozo": validar_pozo_id,
        "recurso": validar_recurso_id,
        "equipo": validar_equipo_id,
        "contrato": validar_contrato_id,
    }
    
    validator = validadores.get(tipo.lower())
    if validator:
        return validator(entidad)
    
    return False


def obtener_tipo_desde_id(id_entidad: str) -> str:
    """
    Infiere el tipo de entidad desde el formato del ID.
    
    Args:
        id_entidad: ID a analizar
        
    Returns:
        Tipo de entidad (pozo, recurso, equipo, contrato, desconocido)
    """
    if not id_entidad:
        return "desconocido"
    
    if "_" in id_entidad and id_entidad == id_entidad.upper():
        # Puede ser recurso o equipo
        if any(id_entidad.startswith(p) for p in ["PULLING", "CISTERNA", "CAMION", "RIG", "TRUCK"]):
            return "equipo"
        return "recurso"
    
    if "-" in id_entidad:
        return "pozo"
    
    try:
        int(id_entidad)
        return "contrato"
    except ValueError:
        pass
    
    return "desconocido"


# Testing
if __name__ == "__main__":
    # Pruebas de validación
    print("=== Pruebas de Validación de IDs ===\n")
    
    # Pozos
    print("POZOS:")
    print(f"  X-123: {validar_pozo_id('X-123')}")  # True
    print(f"  P-001: {validar_pozo_id('P-001')}")  # True
    print(f"  123: {validar_pozo_id('123')}")  # False
    
    # Recursos
    print("\nRECURSOS:")
    print(f"  JUAN_PEREZ: {validar_recurso_id('JUAN_PEREZ')}")  # True
    print(f"  Juan_Perez: {validar_recurso_id('Juan_Perez')}")  # False
    print(f"  ROBERTO: {validar_recurso_id('ROBERTO')}")  # False
    
    # Equipos
    print("\nEQUIPOS:")
    print(f"  PULLING_01: {validar_equipo_id('PULLING_01')}")  # True
    print(f"  CISTERNA_01: {validar_equipo_id('CISTERNA_01')}")  # True
    print(f"  CAMION_01: {validar_equipo_id('CAMION_01')}")  # True
    print(f"  EQUIPO_01: {validar_equipo_id('EQUIPO_01')}")  # False
    
    # Contratos
    print("\nCONTRATOS:")
    print(f"  1: {validar_contrato_id(1)}")  # True
    print(f"  '1': {validar_contrato_id('1')}")  # True
    print(f"  0: {validar_contrato_id(0)}")  # False
    print(f"  -1: {validar_contrato_id(-1)}")  # False
    
    # Inferencia de tipo
    print("\nINFERENCIA DE TIPO:")
    print(f"  X-123: {obtener_tipo_desde_id('X-123')}")  # pozo
    print(f"  JUAN_PEREZ: {obtener_tipo_desde_id('JUAN_PEREZ')}")  # recurso
    print(f"  PULLING_01: {obtener_tipo_desde_id('PULLING_01')}")  # equipo
    print(f"  1: {obtener_tipo_desde_id('1')}")  # contrato

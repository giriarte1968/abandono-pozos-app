import pandas as pd
from .database_service import DatabaseService
from .mock_api_client import MockApiClient
from .financial_service_mock import financial_service

class CapacidadContratoService:
    """
    Servicio para gestionar la capacidad operativa requerida vs disponible.
    """
    def __init__(self):
        self.db = DatabaseService()
        self.api_client = MockApiClient()

    def get_active_contracts(self):
        """Retorna lista de contratos activos desde el servicio financiero."""
        try:
            # Usamos el servicio financiero para consistencia (contiene SureOil, YPF, etc)
            contratos = financial_service.get_contratos()
            return [
                {
                    "ID_CONTRATO": c['ID_CONTRATO'], 
                    "NOMBRE_CONTRATO": c['NOMBRE_CONTRATO'], 
                    "CLIENTE": c['CLIENTE']
                } for c in contratos if c.get('ESTADO') == 'ACTIVO'
            ]
        except Exception as e:
            print(f"[CAPACIDAD] Error al obtener contratos: {e}")
            return []

    def get_contract_capacity_template(self, contract_id):
        """Retorna la plantilla de recursos requeridos para un contrato."""
        query = """
            SELECT rol_requerido, cantidad_requerida, tipo_recurso 
            FROM tbl_contrato_capacidad_operativa 
            WHERE id_contrato = %s AND activo = TRUE
        """
        res = []
        try:
            res = self.db.fetch_all(query, (contract_id,))
        except Exception as e:
            print(f"[CAPACIDAD] DB Error en template: {e}")

        # Si la DB no devuelve nada (vacia o sin conexión), usamos el fallback mock
        if not res:
            # Fallback mock consistente con 008/009 para BRACO-YPF y SureOil
            # Buscamos el nombre del contrato para el fallback
            contratos = financial_service.get_contratos()
            c = next((c for c in contratos if c['ID_CONTRATO'] == contract_id), None)
            
            if c and ("YPF" in c['NOMBRE_CONTRATO'] or "BRACO" in c['NOMBRE_CONTRATO']):
                return [
                    {"rol_requerido": "PULLING", "cantidad_requerida": 3, "tipo_recurso": "EQUIPO"},
                    {"rol_requerido": "CEMENTADOR", "cantidad_requerida": 2, "tipo_recurso": "EQUIPO"},
                    {"rol_requerido": "WIRELINE", "cantidad_requerida": 1, "tipo_recurso": "EQUIPO"},
                    {"rol_requerido": "SUPERVISION", "cantidad_requerida": 2, "tipo_recurso": "PERSONAL"},
                    {"rol_requerido": "WIRELINE", "cantidad_requerida": 2, "tipo_recurso": "PERSONAL"},
                    {"rol_requerido": "TRANSP_PERSONAL", "cantidad_requerida": 1, "tipo_recurso": "EQUIPO"}
                ]
            elif c and "SureOil" in c['NOMBRE_CONTRATO']:
                return [
                    {"rol_requerido": "PULLING", "cantidad_requerida": 1, "tipo_recurso": "EQUIPO"},
                    {"rol_requerido": "SUPERVISION", "cantidad_requerida": 1, "tipo_recurso": "PERSONAL"}
                ]
        return res

    def get_availability_report(self, contract_id):
        """
        Compara Requeridos vs Disponibles en Catálogo.
        """
        template = self.get_contract_capacity_template(contract_id)
        if not template:
            return pd.DataFrame()

        report = []
        
        # Obtener catálogos para ver disponibilidad real
        personnel = self.api_client.get_master_personnel()
        equipment = self.api_client.get_master_equipment()

        for req in template:
            rol = req['rol_requerido']
            tipo = req['tipo_recurso']
            required_qty = req['cantidad_requerida']
            
            available_qty = 0
            if tipo == 'PERSONAL':
                # Filtramos por rol_principal en el catálogo
                available_qty = len([p for p in personnel if p.get('rol_principal') == rol or p.get('role') == rol])
            else:
                # Filtramos por tipo_equipo en el catálogo
                available_qty = len([e for e in equipment if (e.get('tipo_equipo') == rol or e.get('type') == rol) and e.get('activo', True)])

            gap = available_qty - required_qty
            
            report.append({
                "Recurso": rol,
                "Tipo": tipo,
                "Requerido": required_qty,
                "Disponible Catálogo": available_qty,
                "Estado": "✅ OK" if gap >= 0 else f"⚠️ FALTA {abs(gap)}"
            })

        return pd.DataFrame(report)

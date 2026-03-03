import pandas as pd
from .database_service import DatabaseService
from .mock_api_client import MockApiClient

class CapacidadContratoService:
    """
    Servicio para gestionar la capacidad operativa requerida vs disponible.
    """
    def __init__(self):
        self.db = DatabaseService()
        self.api_client = MockApiClient()

    def get_active_contracts(self):
        """Retorna lista de contratos activos."""
        query = "SELECT ID_CONTRATO, NOMBRE_CONTRATO, CLIENTE FROM CONTRATOS WHERE ESTADO = 'ACTIVO'"
        try:
            return self.db.fetch_all(query)
        except:
            # Fallback mock si la DB falla
            return [
                {"ID_CONTRATO": 1, "NOMBRE_CONTRATO": "BRACO-YPF-ABANDONO-2026", "CLIENTE": "YPF"},
                {"ID_CONTRATO": 2, "NOMBRE_CONTRATO": "SureOil - Lote Norte", "CLIENTE": "SureOil"}
            ]

    def get_contract_capacity_template(self, contract_id):
        """Retorna la plantilla de recursos requeridos para un contrato."""
        query = """
            SELECT rol_requerido, cantidad_requerida, tipo_recurso 
            FROM tbl_contrato_capacidad_operativa 
            WHERE id_contrato = %s AND activo = TRUE
        """
        try:
            return self.db.fetch_all(query, (contract_id,))
        except:
            # Fallback mock consistente con 008
            if str(contract_id) == "1":
                return [
                    {"rol_requerido": "PULLING", "cantidad_requerida": 3, "tipo_recurso": "EQUIPO"},
                    {"rol_requerido": "CEMENTADOR", "cantidad_requerida": 2, "tipo_recurso": "EQUIPO"},
                    {"rol_requerido": "WIRELINE", "cantidad_requerida": 1, "tipo_recurso": "EQUIPO"},
                    {"rol_requerido": "SUPERVISION", "cantidad_requerida": 2, "tipo_recurso": "PERSONAL"},
                    {"rol_requerido": "WIRELINE", "cantidad_requerida": 2, "tipo_recurso": "PERSONAL"},
                    {"rol_requerido": "TRANSP_PERSONAL", "cantidad_requerida": 1, "tipo_recurso": "EQUIPO"}
                ]
            return []

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

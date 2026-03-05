import json, os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

class AsignacionOperativaService:
    
    # @deprecated - Ahora se obtiene dinámicamente desde financial_service
    # VALORES_CONTRACTUALES = {'X-123': 185000.00, 'A-321': 185000.00, 'Z-789': 185000.00, 'M-555': 185000.00, 'P-001': 195000.00}
    
    def __init__(self):
        self.mock_data_path = os.path.join(os.path.dirname(__file__), "asignacion_operativa_mock_data.json")
        self._mock_data = None
        self._financial_service = None
    
    def _get_financial_service(self):
        """Obtiene instancia de financial service para datos contractuales"""
        if self._financial_service is None:
            try:
                from services.financial_service_mock import financial_service
                self._financial_service = financial_service
            except:
                pass
        return self._financial_service

    def _load_mock_data(self):
        if self._mock_data is None:
            if os.path.exists(self.mock_data_path):
                with open(self.mock_data_path, "r", encoding="utf-8") as f:
                    self._mock_data = json.load(f)
            else:
                self._mock_data = {"asignaciones": [], "config": {"ultimo_id": 0, "version": "1.0"}}
        return self._mock_data

    def _save_mock_data(self):
        with open(self.mock_data_path, "w", encoding="utf-8") as f:
            json.dump(self._mock_data, f, indent=4, default=str, ensure_ascii=False)

    def create_asignacion(self, data: Dict) -> Dict:
        data = data.copy()
        required = ['id_expediente', 'id_recurso', 'tipo_recurso', 'nombre_recurso', 'fecha_operativa', 'etapa', 'tipo_actividad', 'horas_imputadas', 'costo_hora']
        for field in required:
            if field not in data:
                return {"success": False, "error": f"Campo requerido: {field}"}
        
        if float(data['horas_imputadas']) > 12 or float(data['horas_imputadas']) <= 0:
            return {"success": False, "error": "Horas deben ser entre 0.5 y 12"}
        
        data['impacto_margen'] = data['tipo_actividad'] == 'STANDBY'
        data['costo_total_calculado'] = float(data['horas_imputadas']) * float(data['costo_hora'])
        
        if self._check_duplicidad(data['id_expediente'], data['id_recurso'], data['fecha_operativa'], data['etapa']):
            return {"success": False, "error": "Ya existe asignación para este recurso/fecha/etapa"}
        
        mock = self._load_mock_data()
        data['id_asignacion'] = mock['config']['ultimo_id'] + 1
        data['ts_registro'] = datetime.now().isoformat()
        mock['asignaciones'].append(data)
        mock['config']['ultimo_id'] = data['id_asignacion']
        self._save_mock_data()
        
        return {"success": True, "data": data}

    def _check_duplicidad(self, id_expediente, id_recurso, fecha_operativa, etapa) -> bool:
        mock = self._load_mock_data()
        for a in mock['asignaciones']:
            if a['id_expediente'] == id_expediente and a['id_recurso'] == id_recurso and str(a['fecha_operativa']) == str(fecha_operativa) and a['etapa'] == etapa:
                return True
        return False

    def get_asignaciones_por_expediente(self, id_expediente: str) -> List[Dict]:
        mock = self._load_mock_data()
        asignaciones = [a for a in mock['asignaciones'] if a['id_expediente'] == id_expediente]
        return sorted(asignaciones, key=lambda x: x['fecha_operativa'])

    def get_resumen_costos_por_expediente(self, id_expediente: str) -> Dict:
        asignaciones = self.get_asignaciones_por_expediente(id_expediente)
        resumen = {'total_horas': 0.0, 'total_costo': 0.0, 'horas_standby': 0.0, 'costo_standby': 0.0, 'horas_operacion': 0.0, 'costo_operacion': 0.0, 'horas_traslado': 0.0, 'costo_traslado': 0.0, 'horas_montaje': 0.0, 'costo_montaje': 0.0, 'cantidad_registros': len(asignaciones)}
        
        for a in asignaciones:
            horas = float(a['horas_imputadas'])
            costo = float(a['costo_total_calculado'])
            resumen['total_horas'] += horas
            resumen['total_costo'] += costo
            
            if a['tipo_actividad'] == 'STANDBY':
                resumen['horas_standby'] += horas
                resumen['costo_standby'] += costo
            elif a['tipo_actividad'] == 'OPERACION':
                resumen['horas_operacion'] += horas
                resumen['costo_operacion'] += costo
            elif a['tipo_actividad'] == 'TRASLADO':
                resumen['horas_traslado'] += horas
                resumen['costo_traslado'] += costo
            elif a['tipo_actividad'] == 'MONTAJE':
                resumen['horas_montaje'] += horas
                resumen['costo_montaje'] += costo
        return resumen

    def validar_limite_horas_diarias(self, id_recurso: str, fecha_operativa: str) -> Dict:
        mock = self._load_mock_data()
        horas_acumuladas = 0.0
        for a in mock['asignaciones']:
            if a['id_recurso'] == id_recurso and str(a['fecha_operativa']) == str(fecha_operativa):
                horas_acumuladas += float(a['horas_imputadas'])
        return {'horas_acumuladas': horas_acumuladas, 'horas_restantes': max(0, 12 - horas_acumuladas), 'puede_imputar': horas_acumuladas < 12, 'porcentaje_usado': (horas_acumuladas / 12) * 100}

    def calcular_desviacion_contractual(self, id_expediente: str) -> Dict:
        resumen = self.get_resumen_costos_por_expediente(id_expediente)
        
        # Obtener valor contractual desde tabla normalizada (financial_service)
        fin_svc = self._get_financial_service()
        if fin_svc:
            valor_contractual = fin_svc.get_valor_contractual_pozo(id_expediente)
        else:
            # Fallback si no hay acceso a financial_service
            valor_contractual = 0
        
        costo_real = resumen['total_costo']
        desviacion_usd = costo_real - valor_contractual
        desviacion_pct = (desviacion_usd / valor_contractual * 100) if valor_contractual > 0 else 0
        return {'id_expediente': id_expediente, 'valor_contractual': valor_contractual, 'costo_real': costo_real, 'desviacion_usd': desviacion_usd, 'desviacion_pct': desviacion_pct, 'estado': 'SOBRE COSTO' if desviacion_usd > 0 else 'BAJO COSTO'}

    def get_recursos_disponibles(self) -> Dict:
        return {
            'PERSONAL': [
                {'id': 'JUAN_PEREZ', 'nombre': 'Juan Pérez', 'rol': 'Supervisor', 'costo_hora': 85.00},
                {'id': 'ROBERTO_RUIZ', 'nombre': 'Roberto Ruiz', 'rol': 'Operario', 'costo_hora': 65.00},
                {'id': 'MARIA_GONZALEZ', 'nombre': 'Maria Gonzalez', 'rol': 'HSE', 'costo_hora': 75.00},
                {'id': 'SEBASTIAN_CANES', 'nombre': 'Sebastian Cannes', 'rol': 'Gerente', 'costo_hora': 120.00}
            ],
            'EQUIPO': [
                {'id': 'PULLING_01', 'nombre': 'Pulling Unit #01', 'tipo': 'PULLING', 'costo_hora': 450.00},
                {'id': 'CISTERNA_01', 'nombre': 'Cisterna 25m3 #1', 'tipo': 'CISTERNA', 'costo_hora': 180.00},
                {'id': 'CAMION_01', 'nombre': 'Camion de Apoyo', 'tipo': 'CAMION', 'costo_hora': 150.00}
            ]
        }

    def get_etapas(self) -> List[str]:
        return ['LOGISTICA', 'EJECUCION', 'DTM', 'SUPERVISION']

    def get_tipos_actividad(self) -> List[str]:
        return ['TRASLADO', 'OPERACION', 'MONTAJE', 'STANDBY']

asignacion_operativa_service = AsignacionOperativaService()

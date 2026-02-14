"""
Financial Service Mock - Módulo Financiero INTEGRADO
Integración con sistema operativo (MockApiClient)
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
# Importar servicio operativo para integración
try:
    from .mock_api_client import MockApiClient
except ImportError:
    # Fallback para cuando se ejecuta standalone
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from mock_api_client import MockApiClient


class FinancialServiceMock:
    """Servicio financiero integrado con operaciones"""
    
    def __init__(self, persistence_file: str = "frontend/services/persistence_db.json"):
        self.persistence_file = persistence_file
        self.api_client = MockApiClient()  # Conexión con operaciones
        
        # Datos específicos de finanzas (mantenemos separados)
        self.contratos: List[Dict] = []
        self.certificaciones: List[Dict] = []
        self.facturas: List[Dict] = []
        self.cobranzas: List[Dict] = []
        self.costos_reales: List[Dict] = []
        self.parametros_macro: Dict = {}
        
        # Cargar datos iniciales
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Inicializa datos financieros (pozos vienen de operaciones)"""
        
        base_date = datetime(2025, 1, 15)
        
        # ==========================================
        # CONTRATOS (3)
        # ==========================================
        self.contratos = [
            {
                'ID_CONTRATO': 1,
                'NOMBRE_CONTRATO': 'Contrato SureOil - Lote Norte',
                'CLIENTE': 'SureOil Argentina S.A.',
                'CANTIDAD_POZOS': 4,
                'VALOR_UNITARIO_BASE_USD': 185000.00,
                'MONTO_TOTAL_CONTRACTUAL': 740000.00,
                'BACKLOG_RESTANTE': 555000.00,
                'PLAZO_PAGO_DIAS': 30,
                'FECHA_INICIO': base_date,
                'FECHA_FIN': base_date + timedelta(days=365),
                'ESTADO': 'ACTIVO',
                'total_certificaciones': 1,
                'pozos_asignados': ['X-123', 'A-321', 'Z-789', 'M-555']
            },
            {
                'ID_CONTRATO': 2,
                'NOMBRE_CONTRATO': 'Contrato YPF - Abandono Integral',
                'CLIENTE': 'YPF S.A.',
                'CANTIDAD_POZOS': 3,
                'VALOR_UNITARIO_BASE_USD': 195000.00,
                'MONTO_TOTAL_CONTRACTUAL': 585000.00,
                'BACKLOG_RESTANTE': 390000.00,
                'PLAZO_PAGO_DIAS': 45,
                'FECHA_INICIO': base_date - timedelta(days=30),
                'FECHA_FIN': base_date + timedelta(days=335),
                'ESTADO': 'ACTIVO',
                'total_certificaciones': 1,
                'pozos_asignados': ['P-001', 'P-002', 'H-101']
            },
            {
                'ID_CONTRATO': 3,
                'NOMBRE_CONTRATO': 'Contrato Petrobras - Mantenimiento',
                'CLIENTE': 'Petrobras Argentina S.A.',
                'CANTIDAD_POZOS': 3,
                'VALOR_UNITARIO_BASE_USD': 175000.00,
                'MONTO_TOTAL_CONTRACTUAL': 525000.00,
                'BACKLOG_RESTANTE': 525000.00,
                'PLAZO_PAGO_DIAS': 30,
                'FECHA_INICIO': base_date + timedelta(days=15),
                'FECHA_FIN': base_date + timedelta(days=380),
                'ESTADO': 'ACTIVO',
                'total_certificaciones': 0,
                'pozos_asignados': ['H-102', 'T-201', 'C-301']
            }
        ]
        
        # ==========================================
        # CERTIFICACIONES (3)
        # ==========================================
        self.certificaciones = [
            {
                'ID_CERTIFICACION': 1,
                'ID_CONTRATO': 1,
                'ID_WELL': 'X-123',
                'WELL_NAME': 'Pozo X-123',
                'FECHA_CERTIFICACION': base_date - timedelta(days=15),
                'MONTO_CERTIFICADO': 185000.00,
                'PORCENTAJE_AVANCE': 100.0,
                'ESTADO': 'FACTURADO',
                'SINCRONIZADO_OPERACIONES': True
            },
            {
                'ID_CERTIFICACION': 2,
                'ID_CONTRATO': 2,
                'ID_WELL': 'P-001',
                'WELL_NAME': 'Pozo P-001 (YPF)',
                'FECHA_CERTIFICACION': base_date - timedelta(days=10),
                'MONTO_CERTIFICADO': 195000.00,
                'PORCENTAJE_AVANCE': 100.0,
                'ESTADO': 'FACTURADO',
                'SINCRONIZADO_OPERACIONES': True
            },
            {
                'ID_CERTIFICACION': 3,
                'ID_CONTRATO': 1,
                'ID_WELL': 'A-321',
                'WELL_NAME': 'Pozo A-321',
                'FECHA_CERTIFICACION': base_date - timedelta(days=5),
                'MONTO_CERTIFICADO': 185000.00,
                'PORCENTAJE_AVANCE': 100.0,
                'ESTADO': 'PENDIENTE_FACTURA',
                'SINCRONIZADO_OPERACIONES': False
            }
        ]
        
        # ==========================================
        # FACTURAS (Auto-generadas)
        # ==========================================
        self.facturas = []
        factura_counter = 1001
        for cert in self.certificaciones:
            contrato = next((c for c in self.contratos if c['ID_CONTRATO'] == cert['ID_CONTRATO']), None)
            if contrato:
                plazo_pago = contrato['PLAZO_PAGO_DIAS']
                fecha_factura = cert['FECHA_CERTIFICACION']
                fecha_vencimiento = fecha_factura + timedelta(days=plazo_pago)
                
                factura = {
                    'ID_FACTURA': len(self.facturas) + 1,
                    'ID_CERTIFICACION': cert['ID_CERTIFICACION'],
                    'NUMERO_FACTURA': f'F-2025-{factura_counter}',
                    'FECHA_FACTURA': fecha_factura,
                    'FECHA_VENCIMIENTO': fecha_vencimiento,
                    'MONTO': cert['MONTO_CERTIFICADO'],
                    'ESTADO': 'PENDIENTE' if cert['ESTADO'] == 'PENDIENTE_FACTURA' else 'EMITIDA',
                    'CLIENTE': contrato['CLIENTE']
                }
                self.facturas.append(factura)
                factura_counter += 1
        
        # ==========================================
        # COBRANZAS (2)
        # ==========================================
        self.cobranzas = [
            {
                'ID_COBRANZA': 1,
                'ID_FACTURA': 1,
                'FECHA_COBRANZA': base_date - timedelta(days=5),
                'MONTO_COBRADO': 185000.00,
                'MEDIO_PAGO': 'TRANSFERENCIA',
                'ESTADO': 'COMPLETADA'
            },
            {
                'ID_COBRANZA': 2,
                'ID_FACTURA': 2,
                'FECHA_COBRANZA': base_date - timedelta(days=2),
                'MONTO_COBRADO': 195000.00,
                'MEDIO_PAGO': 'CHEQUE',
                'ESTADO': 'COMPLETADA'
            }
        ]
        
        # Actualizar estado de facturas cobradas
        for cob in self.cobranzas:
            factura = next((f for f in self.facturas if f['ID_FACTURA'] == cob['ID_FACTURA']), None)
            if factura:
                factura['ESTADO'] = 'COBRADA'
        
        # ==========================================
        # COSTOS REALES (Integrados con operaciones)
        # ==========================================
        self.costos_reales = []
        self._sincronizar_costos_operaciones()
        
        # ==========================================
        # PARÁMETROS MACRO
        # ==========================================
        self.parametros_macro = {
            'COTIZACION_DOLAR': {'valor': 1050.00, 'unidad': 'ARS/USD', 'fecha': base_date},
            'INFLACION_ANUAL': {'valor': 25.50, 'unidad': '%', 'fecha': base_date},
            'TASA_INTERES': {'valor': 45.00, 'unidad': '%', 'fecha': base_date},
        }
        
        self._persist_data()
    
    # ==========================================
    # INTEGRACIÓN CON OPERACIONES
    # ==========================================
    
    def get_pozos(self) -> List[Dict]:
        """Obtiene pozos desde el sistema operativo (MockApiClient)"""
        try:
            proyectos = self.api_client.get_projects()
            pozos = []
            for proyecto in proyectos:
                pozo = {
                    'ID_WELL': proyecto['id'],
                    'WELL_NAME': proyecto['nombre'],
                    'ESTADO_PROYECTO': proyecto['estado_proyecto'],
                    'PROGRESO': proyecto.get('progreso', 0),
                    'YACIMIENTO': proyecto.get('yacimiento', ''),
                    'CAMPANA': proyecto.get('campana', ''),
                    'RESPONSABLE': proyecto.get('responsable', ''),
                    'LAT': proyecto.get('lat', 0),
                    'LON': proyecto.get('lon', 0),
                    'WORKFLOW_STATUS': proyecto.get('workflow_status', '')
                }
                pozos.append(pozo)
            return pozos
        except Exception as e:
            print(f"[FINANCIAL] Error al obtener pozos de operaciones: {e}")
            # Fallback a lista vacía
            return []
    
    def get_pozo_by_id(self, well_id: str) -> Optional[Dict]:
        """Obtiene un pozo específico desde operaciones"""
        pozos = self.get_pozos()
        return next((p for p in pozos if p['ID_WELL'] == well_id), None)
    
    def _sincronizar_costos_operaciones(self):
        """Sincroniza costos desde operaciones hacia finanzas"""
        # Aquí se integrarían costos reales de operaciones
        # Por ahora mantenemos los costos mock específicos de finanzas
        base_date = datetime(2025, 1, 15)
        
        self.costos_reales = [
            {
                'ID_COSTO': 1,
                'ID_WELL': 'X-123',
                'ETAPA': 'PREPARACION',
                'CONCEPTO': 'Mano de obra especializada',
                'MONTO_USD': 45000.00,
                'FECHA': base_date - timedelta(days=30),
                'ORIGEN': 'OPERACIONES'  # Indica que viene de operaciones
            },
            {
                'ID_COSTO': 2,
                'ID_WELL': 'X-123',
                'ETAPA': 'EJECUCION',
                'CONCEPTO': 'Equipo de perforación',
                'MONTO_USD': 85000.00,
                'FECHA': base_date - timedelta(days=20),
                'ORIGEN': 'OPERACIONES'
            },
            {
                'ID_COSTO': 3,
                'ID_WELL': 'P-001',
                'ETAPA': 'PREPARACION',
                'CONCEPTO': 'Transporte y logística',
                'MONTO_USD': 32000.00,
                'FECHA': base_date - timedelta(days=25),
                'ORIGEN': 'OPERACIONES'
            },
            {
                'ID_COSTO': 4,
                'ID_WELL': 'P-001',
                'ETAPA': 'EJECUCION',
                'CONCEPTO': 'Cemento y materiales',
                'MONTO_USD': 78000.00,
                'FECHA': base_date - timedelta(days=15),
                'ORIGEN': 'OPERACIONES'
            }
        ]
    
    def certificar_pozo(self, id_contrato: int, well_id: str, monto: float, 
                       porcentaje_avance: float) -> Dict:
        """Certifica un pozo y actualiza estado en operaciones"""
        
        # Verificar contrato
        contrato = self.get_contrato_by_id(id_contrato)
        if not contrato:
            raise ValueError(f"Contrato {id_contrato} no encontrado")
        
        # Verificar pozo existe en operaciones
        pozo = self.get_pozo_by_id(well_id)
        if not pozo:
            raise ValueError(f"Pozo {well_id} no encontrado en operaciones")
        
        # Verificar que el pozo esté asignado al contrato
        if well_id not in contrato.get('pozos_asignados', []):
            raise ValueError(f"Pozo {well_id} no está asignado al contrato {id_contrato}")
        
        # Verificar que no esté ya certificado
        cert_existente = next((c for c in self.certificaciones 
                              if c['ID_WELL'] == well_id and c['ESTADO'] != 'ANULADA'), None)
        if cert_existente:
            raise ValueError(f"Pozo {well_id} ya tiene una certificación activa")
        
        # Crear certificación
        nueva_cert = {
            'ID_CERTIFICACION': len(self.certificaciones) + 1,
            'ID_CONTRATO': id_contrato,
            'ID_WELL': well_id,
            'WELL_NAME': pozo['WELL_NAME'],
            'FECHA_CERTIFICACION': datetime.now(),
            'MONTO_CERTIFICADO': monto,
            'PORCENTAJE_AVANCE': porcentaje_avance,
            'ESTADO': 'FACTURADO',
            'SINCRONIZADO_OPERACIONES': False
        }
        
        self.certificaciones.append(nueva_cert)
        
        # Generar factura automática
        plazo_pago = contrato['PLAZO_PAGO_DIAS']
        fecha_vencimiento = nueva_cert['FECHA_CERTIFICACION'] + timedelta(days=plazo_pago)
        
        nueva_factura = {
            'ID_FACTURA': len(self.facturas) + 1,
            'ID_CERTIFICACION': nueva_cert['ID_CERTIFICACION'],
            'NUMERO_FACTURA': f'F-2025-{1001 + len(self.facturas)}',
            'FECHA_FACTURA': nueva_cert['FECHA_CERTIFICACION'],
            'FECHA_VENCIMIENTO': fecha_vencimiento,
            'MONTO': monto,
            'ESTADO': 'EMITIDA',
            'CLIENTE': contrato['CLIENTE']
        }
        
        self.facturas.append(nueva_factura)
        
        # Actualizar backlog
        contrato['BACKLOG_RESTANTE'] -= monto
        contrato['total_certificaciones'] += 1
        
        # Persistir
        self._persist_data()
        
        return {
            'certificacion': nueva_cert,
            'factura_generada': nueva_factura,
            'mensaje': f"Pozo {well_id} certificado exitosamente"
        }
    
    def sincronizar_estado_pozo_operaciones(self, well_id: str, nuevo_estado: str):
        """Actualiza el estado de un pozo en el sistema operativo"""
        # En una implementación real, esto llamaría a la API de operaciones
        # Por ahora es un placeholder para mostrar la intención
        print(f"[SINCRONIZACIÓN] Actualizando pozo {well_id} a estado {nuevo_estado} en operaciones")
        # Aquí iría: self.api_client.update_well_status(well_id, nuevo_estado)
    
    def get_costos_pozo(self, well_id: str) -> List[Dict]:
        """Obtiene todos los costos asociados a un pozo"""
        return [c for c in self.costos_reales if c['ID_WELL'] == well_id]
    
    # ==========================================
    # MÉTODOS EXISTENTES (mantenidos)
    # ==========================================
    
    def _persist_data(self):
        """Guarda datos financieros en persistencia"""
        data = {
            'contratos': self.contratos,
            'certificaciones': self.certificaciones,
            'facturas': self.facturas,
            'cobranzas': self.cobranzas,
            'costos_reales': self.costos_reales,
            'parametros_macro': self.parametros_macro,
            'last_updated': datetime.now().isoformat()
        }
        
        def serialize_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_dates(item) for item in obj]
            return obj
        
        data = serialize_dates(data)
        
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        with open(self.persistence_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_contratos(self) -> List[Dict]:
        """Retorna lista de contratos"""
        return self.contratos
    
    def get_contrato_by_id(self, id_contrato: int) -> Optional[Dict]:
        """Retorna un contrato por ID"""
        return next((c for c in self.contratos if c['ID_CONTRATO'] == id_contrato), None)
    
    def get_certificaciones(self) -> List[Dict]:
        """Retorna lista de certificaciones"""
        return self.certificaciones
    
    def get_facturas(self) -> List[Dict]:
        """Retorna lista de facturas"""
        return self.facturas
    
    def get_cobranzas(self) -> List[Dict]:
        """Retorna lista de cobranzas"""
        return self.cobranzas
    
    def get_pozos_by_contrato(self, id_contrato: int) -> List[Dict]:
        """Retorna pozos asignados a un contrato (desde operaciones)"""
        contrato = self.get_contrato_by_id(id_contrato)
        if contrato:
            pozo_ids = contrato.get('pozos_asignados', [])
            todos_pozos = self.get_pozos()
            return [p for p in todos_pozos if p['ID_WELL'] in pozo_ids]
        return []
    
    def get_kpis_dashboard(self) -> Dict[str, Any]:
        """Calcula KPIs para el dashboard financiero"""
        backlog_contractual = sum(c['BACKLOG_RESTANTE'] for c in self.contratos)
        
        total_pozos = sum(c['CANTIDAD_POZOS'] for c in self.contratos)
        pozos_certificados = len(self.certificaciones)
        avance_fisico_pct = (pozos_certificados / total_pozos) * 100 if total_pozos > 0 else 0
        
        total_contractual = sum(c['MONTO_TOTAL_CONTRACTUAL'] for c in self.contratos)
        total_certificado = sum(cert['MONTO_CERTIFICADO'] for cert in self.certificaciones)
        avance_financiero_pct = (total_certificado / total_contractual) * 100 if total_contractual > 0 else 0
        
        costo_mensual_promedio = sum(c['MONTO_TOTAL_CONTRACTUAL'] for c in self.contratos) / 12 * 0.65
        capital_trabajo = costo_mensual_promedio * 3
        
        total_cobrado = sum(cob['MONTO_COBRADO'] for cob in self.cobranzas)
        total_costos = sum(costo['MONTO_USD'] for costo in self.costos_reales)
        saldo_caja = total_cobrado - total_costos
        
        costo_diario = costo_mensual_promedio / 30
        dias_cobertura = saldo_caja / costo_diario if costo_diario > 0 else 0
        
        return {
            'backlog_contractual': backlog_contractual,
            'avance_fisico_pct': avance_fisico_pct,
            'avance_financiero_pct': avance_financiero_pct,
            'capital_trabajo': capital_trabajo,
            'saldo_caja': saldo_caja,
            'dias_cobertura': dias_cobertura,
            'alerta_cobertura': dias_cobertura < 45
        }
    
    def get_flujo_fondos(self, meses: int = 12) -> pd.DataFrame:
        """Genera proyección de flujo de fondos"""
        fecha_inicio = datetime.now().replace(day=1) + timedelta(days=32)
        fecha_inicio = fecha_inicio.replace(day=1)
        
        flujo_data = []
        saldo_acumulado = 0
        
        for i in range(meses):
            fecha_periodo = fecha_inicio + timedelta(days=30*i)
            periodo = fecha_periodo.strftime('%Y-%m')
            
            total_backlog = sum(c['BACKLOG_RESTANTE'] for c in self.contratos)
            ingreso_mensual_base = total_backlog / 12
            import random
            variacion = random.uniform(0.8, 1.2)
            ingresos = ingreso_mensual_base * variacion
            egresos = ingresos * 0.65
            
            saldo_mensual = ingresos - egresos
            saldo_acumulado += saldo_mensual
            
            flujo_data.append({
                'PERIODO': periodo,
                'INGRESOS_PROYECTADOS': ingresos,
                'EGRESOS_OPERATIVOS': egresos,
                'SALDO_MENSUAL': saldo_mensual,
                'ACUMULADO': saldo_acumulado
            })
        
        return pd.DataFrame(flujo_data)
    
    def registrar_cobranza(self, id_factura: int, monto: float, medio_pago: str) -> Dict:
        """Registra una cobranza"""
        factura = next((f for f in self.facturas if f['ID_FACTURA'] == id_factura), None)
        if not factura:
            raise ValueError(f"Factura {id_factura} no encontrada")
        
        nueva_cobranza = {
            'ID_COBRANZA': len(self.cobranzas) + 1,
            'ID_FACTURA': id_factura,
            'FECHA_COBRANZA': datetime.now(),
            'MONTO_COBRADO': monto,
            'MEDIO_PAGO': medio_pago,
            'ESTADO': 'COMPLETADA'
        }
        
        self.cobranzas.append(nueva_cobranza)
        factura['ESTADO'] = 'COBRADA'
        self._persist_data()
        
        return nueva_cobranza


# Instancia singleton
financial_service = FinancialServiceMock()

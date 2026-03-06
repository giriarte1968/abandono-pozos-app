"""
Análisis Operacional Service - Root Cause Analysis
Detecta patrones de ineficiencia operativa basándose en datos de telemetría y eventos.

Metodología:
- Análisis estadístico simple de datos agregados
- Correlaciones entre parámetros de telemetría
- Reglas heurísticas para detección de patrones
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime


class AnalisisOperacionalService:
    
    # Umbrales para detección de patrones (heurísticas)
    UMBRALES = {
        'hook_load': {
            'max_normal': 22.0,  # tn
            'alto': 25.0,
            'descripcion': 'Hook Load'
        },
        'annular_pressure': {
            'max_normal': 100.0,  # psi
            'alto': 120.0,
            'descripcion': 'Presión Anular'
        },
        'trip_speed': {
            'min_normal': 150.0,  # m/h
            'bajo': 120.0,
            'descripcion': 'Velocidad de Tripping'
        },
        'pump_pressure': {
            'max_normal': 1000.0,  # psi
            'alto': 1100.0,
            'descripcion': 'Presión de Bomba'
        },
        'standby': {
            'max_normal': 4.0,  # horas/día
            'alto': 8.0,
            'descripcion': 'Tiempo Standby'
        }
    }
    
    def __init__(self):
        self.telemetria_path = os.path.join(os.path.dirname(__file__), "telemetria_mock_data.json")
        self.asignacion_service = None
    
    def _load_telemetria(self) -> List[Dict]:
        """Carga datos de telemetría mock"""
        if os.path.exists(self.telemetria_path):
            with open(self.telemetria_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get('datos', [])
        return []
    
    def _get_asignacion_service(self):
        """Obtiene servicio de asignaciones"""
        if self.asignacion_service is None:
            try:
                from services.asignacion_operativa_service import asignacion_operativa_service
                self.asignacion_service = asignacion_operativa_service
            except:
                pass
        return self.asignacion_service
    
    def analizar_eficiencia_pozo(self, pozo_id: str) -> Dict[str, Any]:
        """
        Analiza la eficiencia de un pozo basándose en:
        - Datos de telemetría
        - Eventos operativos (standby)
        - Comparación con umbrales
        """
        telemetria = [t for t in self._load_telemetria() if t['pozo_id'] == pozo_id]
        
        if not telemetria:
            return {'error': f'No hay datos de telemetría para {pozo_id}'}
        
        # Calcular promedios del período
        n = len(telemetria)
        avg_hook_load = sum(t['hook_load_avg'] for t in telemetria) / n
        max_hook_load = max(t['hook_load_max'] for t in telemetria)
        avg_annular = sum(t['annular_pressure_avg'] for t in telemetria) / n
        avg_trip_speed = sum(t['trip_speed_avg'] for t in telemetria) / n
        avg_pump_pressure = sum(t['pump_pressure_avg'] for t in telemetria) / n
        
        # Obtener datos de standby
        asign_svc = self._get_asignacion_service()
        if asign_svc:
            resumen = asign_svc.get_resumen_costos_por_expediente(pozo_id)
            horas_standby = resumen.get('horas_standby', 0)
            horas_totales = resumen.get('total_horas', 0)
        else:
            horas_standby = sum(t.get('horas_standby', 0) for t in telemetria)
            horas_totales = sum(t.get('horas_operacion', 0) + t.get('horas_standby', 0) for t in telemetria)
        
        # Detectar patrones
        patrones = self._detectar_patrones(
            avg_hook_load, max_hook_load, avg_annular, 
            avg_trip_speed, avg_pump_pressure, horas_standby, n
        )
        
        # Calcular impacto
        impacto = self._calcular_impacto(patrones, horas_totales, horas_standby)
        
        return {
            'pozo_id': pozo_id,
            'periodo_dias': n,
            'promedios': {
                'hook_load': avg_hook_load,
                'hook_load_max': max_hook_load,
                'annular_pressure': avg_annular,
                'trip_speed': avg_trip_speed,
                'pump_pressure': avg_pump_pressure
            },
            'horas_totales': horas_totales,
            'horas_standby': horas_standby,
            'patrones': patrones,
            'impacto': impacto
        }
    
    def _detectar_patrones(self, hook_load, hook_load_max, annular, trip_speed, pump_pressure, standby, dias) -> List[Dict]:
        """Detecta patrones de ineficiencia usando reglas heurísticas"""
        patrones = []
        
        # Hook load elevado
        if hook_load > self.UMBRALES['hook_load']['max_normal']:
            severity = 'alto' if hook_load > self.UMBRALES['hook_load']['alto'] else 'medio'
            patrones.append({
                'tipo': 'hook_load_elevado',
                'nombre': 'Hook Load Elevado',
                'valor': hook_load,
                'umbral': self.UMBRALES['hook_load']['max_normal'],
                'severidad': severity,
                'descripcion': f'Hook load promedio de {hook_load:.1f} tn supera el umbral de {self.UMBRALES["hook_load"]["max_normal"]} tn',
                'causa_probable': 'Fricción anormal en sarta o wellbore',
                'impacto_horas': 8 if severity == 'alto' else 4,
                'impacto_costo_pct': 10 if severity == 'alto' else 5
            })
        
        # Presión anular alta
        if annular > self.UMBRALES['annular_pressure']['max_normal']:
            severity = 'alto' if annular > self.UMBRALES['annular_pressure']['alto'] else 'medio'
            patrones.append({
                'tipo': 'presion_anular_alta',
                'nombre': 'Presión Anular Alta',
                'valor': annular,
                'umbral': self.UMBRALES['annular_pressure']['max_normal'],
                'severidad': severity,
                'descripcion': f'Presión anular promedio de {annular:.0f} psi supera el umbral',
                'causa_probable': 'Pegas de sarta oWell control issues',
                'impacto_horas': 6 if severity == 'alto' else 3,
                'impacto_costo_pct': 8 if severity == 'alto' else 4
            })
        
        # Velocidad de tripping baja
        if trip_speed < self.UMBRALES['trip_speed']['min_normal']:
            severity = 'alto' if trip_speed < self.UMBRALES['trip_speed']['bajo'] else 'medio'
            patrones.append({
                'tipo': 'tripping_lento',
                'nombre': 'Velocidad de Tripping Baja',
                'valor': trip_speed,
                'umbral': self.UMBRALES['trip_speed']['min_normal'],
                'severidad': severity,
                'descripcion': f'Velocidad promedio de {trip_speed:.0f} m/h está por debajo del optimal',
                'causa_probable': 'Dificultad para trip o井壁 inestable',
                'impacto_horas': 6 if severity == 'alto' else 3,
                'impacto_costo_pct': 8 if severity == 'alto' else 4
            })
        
        # Standby alto
        standby_diario = standby / dias if dias > 0 else 0
        if standby_diario > self.UMBRALES['standby']['max_normal']:
            severity = 'alto' if standby_diario > self.UMBRALES['standby']['alto'] else 'medio'
            patrones.append({
                'tipo': 'standby_alto',
                'nombre': 'Tiempo Standby Excesivo',
                'valor': standby_diario,
                'umbral': self.UMBRALES['standby']['max_normal'],
                'severidad': severity,
                'descripcion': f'{standby:.1f} horas de standby en {dias} días ({standby_diario:.1f} hrs/día)',
                'causa_probable': 'Clima, logística o espera de equipo',
                'impacto_horas': standby_diario * 0.5 if severity == 'alto' else standby_diario * 0.25,
                'impacto_costo_pct': 12 if severity == 'alto' else 6
            })
        
        return patrones
    
    def _calcular_impacto(self, patrones: List[Dict], horas_totales: float, horas_standby: float) -> Dict:
        """Calcula el impacto total en horas y costos"""
        impacto_horas = sum(p['impacto_horas'] for p in patrones)
        impacto_costo_pct = max((p['impacto_costo_pct'] for p in patrones), default=0)
        
        # Estimar costo por hora promedio
        costo_hora_promedio = 150  # USD/hr estimado
        impacto_costo_usd = horas_totales * (impacto_costo_pct / 100) * costo_hora_promedio
        
        return {
            'horas_extras_estimadas': impacto_horas,
            'costo_adicional_estimado_pct': impacto_costo_pct,
            'costo_adicional_estimado_usd': impacto_costo_usd,
            'es_critico': len([p for p in patrones if p['severidad'] == 'alto']) > 0
        }
    
    def generar_reporte_root_cause(self, pozo_id: str) -> str:
        """Genera un reporte de Root Cause Analysis en formato texto"""
        analisis = self.analizar_eficiencia_pozo(pozo_id)
        
        if 'error' in analisis:
            return f"Error: {analisis['error']}"
        
        lineas = []
        lineas.append(f"=" * 60)
        lineas.append(f"ROOT CAUSE ANALYSIS - Pozo {pozo_id}")
        lineas.append(f"=" * 60)
        lineas.append(f"")
        lineas.append(f"Período: {analisis['periodo_dias']} días")
        lineas.append(f"Horas totales: {analisis['horas_totales']:.1f}")
        lineas.append(f"Horas standby: {analisis['horas_standby']:.1f}")
        lineas.append(f"")
        
        if analisis['patrones']:
            lineas.append(f"FACTORES DE INEFFICIENCIA DETECTADOS:")
            lineas.append("-" * 60)
            
            for i, p in enumerate(analisis['patrones'], 1):
                lineas.append(f"{i}. {p['nombre']} ({p['severidad'].upper()})")
                lineas.append(f"   Valor: {p['valor']:.1f} (umbral: {p['umbral']})")
                lineas.append(f"   Causa probable: {p['causa_probable']}")
                lineas.append(f"   Impacto: +{p['impacto_horas']} hrs, +{p['impacto_costo_pct']}% costo")
                lineas.append(f"")
            
            lineas.append(f"IMPACTO TOTAL ESTIMADO:")
            lineas.append("-" * 60)
            imp = analisis['impacto']
            lineas.append(f"Horas extras: +{imp['horas_extras_estimadas']:.1f}")
            lineas.append(f"Costo adicional: +{imp['costo_adicional_estimado_usd']:.0f} USD ({imp['costo_adicional_estimado_pct']}%)")
            lineas.append(f"Estado: {'CRÍTICO' if imp['es_critico'] else 'ATENCIÓN'}")
            lineas.append(f"")
            
            lineas.append(f"RECOMENDACIONES:")
            lineas.append("-" * 60)
            for p in analisis['patrones']:
                if p['tipo'] == 'hook_load_elevado':
                    lineas.append(f"- Reducir carga de izaje a <22 tn")
                elif p['tipo'] == 'presion_anular_alta':
                    lineas.append(f"- Revisar estado de wellbore y presión de kill line")
                elif p['tipo'] == 'tripping_lento':
                    lineas.append(f"- Optimizar velocidad de tripping")
                elif p['tipo'] == 'standby_alto':
                    lineas.append(f"- Revisar logística y planificación")
        else:
            lineas.append("✅ No se detectaron patrones de ineficiencia significativos.")
        
        lineas.append(f"")
        lineas.append("=" * 60)
        
        return "\n".join(lineas)
    
    def get_resumen_global(self) -> List[Dict]:
        """Retorna análisis de todos los pozos"""
        pozos = ['X-123', 'P-001', 'A-321']
        resultados = []
        
        for pozo in pozos:
            analisis = self.analizar_eficiencia_pozo(pozo)
            if 'error' not in analisis:
                resultados.append({
                    'pozo': pozo,
                    'patrones_encontrados': len(analisis['patrones']),
                    'es_critico': analisis['impacto']['es_critico'],
                    'impacto_horas': analisis['impacto']['horas_extras_estimadas'],
                    'impacto_costo_pct': analisis['impacto']['costo_adicional_estimado_pct']
                })
        
        return sorted(resultados, key=lambda x: x['impacto_horas'], reverse=True)


# Instancia singleton
analisis_operacional_service = AnalisisOperacionalService()

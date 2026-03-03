import json
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd
from services.database_service import DatabaseService

class RecursoEstadoService:
    """
    Servicio para la gestión del estado operativo diario de los recursos (Personal y Equipos).
    Interactúa con MySQL y usa JSON local como fallback.
    """
    def __init__(self, persistence_file: str = "frontend/services/recurso_estado_db.json"):
        self.db = DatabaseService()
        self.persistence_file = persistence_file
        self.use_mock = not self.db.is_available()
        self.mock_data = []
        if self.use_mock:
            self._init_mock_db()
        else:
            self._ensure_table_exists()

    def _ensure_table_exists(self):
        query = """
        CREATE TABLE IF NOT EXISTS tbl_recurso_estado_diario (
            id_estado INT AUTO_INCREMENT PRIMARY KEY,
            id_recurso VARCHAR(50) NOT NULL,
            tipo_recurso ENUM('PERSONAL', 'EQUIPO') NOT NULL,
            fecha DATE NOT NULL,
            estado_operativo ENUM('ACTIVO', 'STANDBY', 'LICENCIA', 'FRANCO', 'MANTENIMIENTO', 'ASIGNADO') NOT NULL,
            id_pozo VARCHAR(50) NULL,
            observaciones TEXT NULL,
            ts_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY idx_recurso_fecha (id_recurso, fecha)
        )
        """
        self.db.execute(query)

    def _init_mock_db(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r') as f:
                    self.mock_data = json.load(f)
            except Exception:
                self.mock_data = []
        else:
            self.mock_data = []
            
        # Si sigue vacío (primera ejecución o sin archivo), generamos datos de simulación
        # extraídos orgánicamente de MockApiClient para dar sensación de MVP vivo.
        if not self.mock_data:
            self._generate_initial_simulation()
            
    def _generate_initial_simulation(self):
        """Genera datos de simulación iniciales basados en MockApiClient."""
        from services.mock_api_client import MockApiClient
        api = MockApiClient()
        today_str = date.today().isoformat()
        
        # Iteramos sobre los proyectos para simular estados coherentes
        pozos = api.get_all_wells()
        for pozo in pozos:
            detail = api.get_project_detail(pozo['id'])
            if not detail: continue
            
            estado_proj = pozo['estado_proyecto']
            
            # Simulamos Equipos
            for eq in detail.get('equipment_list', []):
                # Determinar estado en base a la info del proyecto
                if eq.get('status') == 'FALLA CRITICA':
                    estado_op = 'MANTENIMIENTO'
                elif eq.get('is_on_location', False):
                    estado_op = 'ACTIVO'
                elif eq.get('assigned', False):
                    estado_op = 'ASIGNADO'
                else:
                    estado_op = 'STANDBY'
                    
                self.mock_data.append({
                    'id_estado': len(self.mock_data) + 1,
                    'id_recurso': eq['name'], # Equipos en el mock usan nombre como ID visual
                    'tipo_recurso': 'EQUIPO',
                    'fecha': today_str,
                    'estado_operativo': estado_op,
                    'id_pozo': pozo['id'] if estado_op in ['ACTIVO', 'ASIGNADO'] else None,
                    'observaciones': 'Autogenerado por simulación MVP' if estado_op == 'MANTENIMIENTO' else '',
                    'ts_creacion': datetime.now().isoformat()
                })
                
            # Simulamos Personal
            for p in detail.get('personnel_list', []):
                # Determinar estado
                if not p.get('medical_ok', True) or not p.get('induction_ok', True):
                    estado_op = 'LICENCIA'
                elif p.get('present', False) and estado_proj in ['EN_EJECUCION', 'BLOQUEADO']:
                    estado_op = 'ACTIVO'
                else:
                    estado_op = 'STANDBY'
                    
                # Buscar ID real si existe en el maestro, sino usar nombre
                recurso_id = p.get('name', 'Desconocido')
                
                self.mock_data.append({
                    'id_estado': len(self.mock_data) + 1,
                    'id_recurso': recurso_id,
                    'tipo_recurso': 'PERSONAL',
                    'fecha': today_str,
                    'estado_operativo': estado_op,
                    'id_pozo': pozo['id'] if estado_op == 'ACTIVO' else None,
                    'observaciones': 'Bloqueado por HSE' if estado_op == 'LICENCIA' else '',
                    'ts_creacion': datetime.now().isoformat()
                })
        
        # Añadir algunos en Standby desde el catálogo que no están asignados
        for m_eq in api.get_master_equipment():
            if not any(r['id_recurso'] == m_eq['name'] for r in self.mock_data):
                self.mock_data.append({
                    'id_estado': len(self.mock_data) + 1,
                    'id_recurso': m_eq['name'],
                    'tipo_recurso': 'EQUIPO',
                    'fecha': today_str,
                    'estado_operativo': 'STANDBY',
                    'id_pozo': None,
                    'observaciones': '',
                    'ts_creacion': datetime.now().isoformat()
                })
                
        for m_pe in api.get_master_personnel():
            if not any(r['id_recurso'] == m_pe['name'] for r in self.mock_data):
                self.mock_data.append({
                    'id_estado': len(self.mock_data) + 1,
                    'id_recurso': m_pe['name'],
                    'tipo_recurso': 'PERSONAL',
                    'fecha': today_str,
                    'estado_operativo': 'STANDBY',
                    'id_pozo': None,
                    'observaciones': '',
                    'ts_creacion': datetime.now().isoformat()
                })
        
        self._persist_mock()
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        with open(self.persistence_file, 'w') as f:
            json.dump(self.mock_data, f, indent=2)

    def get_estados(self, fecha: Optional[date] = None, tipo_recurso: Optional[str] = None) -> List[Dict]:
        """Obtiene la lista de estados filtrada."""
        if self.use_mock:
            results = self.mock_data
            if fecha:
                fecha_str = fecha.isoformat() if isinstance(fecha, date) else str(fecha)
                results = [r for r in results if r['fecha'] == fecha_str]
            if tipo_recurso and tipo_recurso != 'TODOS':
                results = [r for r in results if r['tipo_recurso'] == tipo_recurso]
            return results
        else:
            query = "SELECT * FROM tbl_recurso_estado_diario WHERE 1=1"
            params = []
            if fecha:
                query += " AND fecha = %s"
                params.append(fecha)
            if tipo_recurso and tipo_recurso != 'TODOS':
                query += " AND tipo_recurso = %s"
                params.append(tipo_recurso)
            query += " ORDER BY ts_creacion DESC"
            return self.db.fetch_all(query, params)

    def add_estado(self, id_recurso: str, tipo_recurso: str, fecha: date, estado_operativo: str, id_pozo: str = None, observaciones: str = None) -> Dict:
        """Agrega o reemplaza un estado diario para un recurso."""
        fecha_str = fecha.isoformat() if isinstance(fecha, date) else str(fecha)
        
        if self.use_mock:
            # Check for duplicates and replace if exists
            existing_idx = next((i for i, r in enumerate(self.mock_data) if r['id_recurso'] == id_recurso and r['fecha'] == fecha_str), None)
            
            new_record = {
                'id_estado': len(self.mock_data) + 1 if existing_idx is None else self.mock_data[existing_idx]['id_estado'],
                'id_recurso': id_recurso,
                'tipo_recurso': tipo_recurso,
                'fecha': fecha_str,
                'estado_operativo': estado_operativo,
                'id_pozo': id_pozo,
                'observaciones': observaciones,
                'ts_creacion': datetime.now().isoformat()
            }
            if existing_idx is not None:
                self.mock_data[existing_idx] = new_record
            else:
                self.mock_data.append(new_record)
            
            self._persist_mock()
            return {"success": True, "msg": "Estado registrado localmente."}
        else:
            # MySQL REPLACE INTO to handle duplicates via UNIQUE KEY
            query = """
            REPLACE INTO tbl_recurso_estado_diario
            (id_recurso, tipo_recurso, fecha, estado_operativo, id_pozo, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (id_recurso, tipo_recurso, fecha, estado_operativo, id_pozo, observaciones)
            rows = self.db.execute(query, params)
            if rows > 0:
                return {"success": True, "msg": "Estado registrado en DB."}
            else:
                return {"success": False, "msg": "No se pudo registrar en DB."}

    def delete_estado(self, id_estado: int) -> bool:
        if self.use_mock:
            self.mock_data = [r for r in self.mock_data if r['id_estado'] != id_estado]
            self._persist_mock()
            return True
        else:
            query = "DELETE FROM tbl_recurso_estado_diario WHERE id_estado = %s"
            rows = self.db.execute(query, (id_estado,))
            return rows > 0

    def get_resumen_indicadores(self, fecha: date) -> Dict:
        """Obtiene conteos agregados para el dashboard."""
        estados = self.get_estados(fecha=fecha)
        
        resumen = {
            'PERSONAL': {'ACTIVO': 0, 'STANDBY': 0, 'LICENCIA': 0, 'FRANCO': 0, 'TOTAL': 0},
            'EQUIPO': {'ACTIVO': 0, 'STANDBY': 0, 'MANTENIMIENTO': 0, 'ASIGNADO': 0, 'TOTAL': 0}
        }
        
        for e in estados:
            tipo = e['tipo_recurso']
            estado = e['estado_operativo']
            if tipo in resumen and estado in resumen[tipo]:
                resumen[tipo][estado] += 1
                resumen[tipo]['TOTAL'] += 1
            # Para manejar estados que apliquen cruzado
            elif tipo in resumen and estado not in resumen[tipo]:
                resumen[tipo][estado] = 1
                resumen[tipo]['TOTAL'] += 1
                
        return resumen

recurso_estado_service = RecursoEstadoService()

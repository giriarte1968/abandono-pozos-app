import hashlib
import json
import os
from datetime import datetime


class ClosureService:
    """
    Servicio de Cierre Técnico de Pozo.
    Gestiona el checklist obligatorio, bloqueos automáticos y aprobación final.
    Principio: Ningún pozo cerrado sin validación + evidencia + calidad.
    """

    ITEMS_OBLIGATORIOS = [
        "Cementación validada",
        "Evidencia certificada",
        "Integridad verificada",
        "Acta firmada digitalmente",
        "Control calidad OK",
    ]

    def __init__(self, audit_service=None, cementation_service=None, compliance_service=None):
        self.audit_service = audit_service
        self.cementation_svc = cementation_service
        self.compliance_svc = compliance_service
        self.mock_data_path = os.path.join(
            os.path.dirname(__file__), "closure_mock_data.json"
        )
        self._mock_data = None

    # ─── Mock Data Access ───────────────────────────────────────

    def _load_mock_data(self):
        if self._mock_data is None:
            if os.path.exists(self.mock_data_path):
                with open(self.mock_data_path, "r", encoding="utf-8") as f:
                    self._mock_data = json.load(f)
            else:
                self._mock_data = {
                    "documentos_evidencia": [], "certificaciones": [],
                    "cierres": [], "checklists": [], "exportaciones": [],
                }
        return self._mock_data

    def _save_mock_data(self):
        with open(self.mock_data_path, "w", encoding="utf-8") as f:
            json.dump(self._mock_data, f, indent=4, default=str, ensure_ascii=False)

    # ─── Documentos de Evidencia ────────────────────────────────

    def get_documentos(self, pozo_id):
        data = self._load_mock_data()
        return [d for d in data["documentos_evidencia"]
                if d["id_pozo"] == pozo_id and d["estado"] == "ACTIVO"]

    def get_certificacion(self, doc_id):
        data = self._load_mock_data()
        for c in data["certificaciones"]:
            if c["documento_evidencia_id"] == doc_id and c["estado"] == "VIGENTE":
                return c
        return None

    def documento_tiene_hash(self, doc_id):
        data = self._load_mock_data()
        for d in data["documentos_evidencia"]:
            if d["documento_evidencia_id"] == doc_id:
                return bool(d.get("hash_sha256"))
        return False

    # ─── Cierre Técnico ────────────────────────────────────────

    def get_cierre(self, pozo_id):
        data = self._load_mock_data()
        for c in data["cierres"]:
            if c["id_pozo"] == pozo_id:
                return c
        return None

    def iniciar_cierre(self, pozo_id, user_id):
        """Inicia proceso de cierre técnico y genera checklist de 5 items."""
        data = self._load_mock_data()
        existing = self.get_cierre(pozo_id)
        if existing:
            return False, "Ya existe un proceso de cierre para este pozo", existing

        new_id = max((c["cierre_tecnico_pozo_id"] for c in data["cierres"]), default=0) + 1
        cierre = {
            "cierre_tecnico_pozo_id": new_id,
            "id_pozo": pozo_id,
            "fecha_inicio_cierre": datetime.now().strftime("%Y-%m-%d"),
            "fecha_fin_cierre": None,
            "estado_cierre": "EN_PROCESO",
            "aprobado_por": None,
            "fecha_aprobacion": None,
            "dictamen_final": None,
            "hash_consolidado": None,
            "creado_por": user_id,
        }
        data["cierres"].append(cierre)

        # Generar checklist obligatorio
        base_id = max((ch["checklist_cierre_id"] for ch in data["checklists"]), default=0)
        for i, item in enumerate(self.ITEMS_OBLIGATORIOS):
            data["checklists"].append({
                "checklist_cierre_id": base_id + i + 1,
                "cierre_tecnico_pozo_id": new_id,
                "item_control": item,
                "estado_item": "PENDIENTE",
                "observacion": None,
                "validado_por": None,
                "fecha_validacion": None,
            })

        self._save_mock_data()

        if self.audit_service:
            self.audit_service.log_event(
                user_id=user_id, user_role="Gerente",
                event_type="CIERRE_INICIADO", entity="POZO",
                entity_id=pozo_id,
                new_state={"cierre_id": new_id},
            )

        return True, "Proceso de cierre iniciado con 5 items de control", cierre

    def get_checklist(self, cierre_id):
        data = self._load_mock_data()
        return [ch for ch in data["checklists"] if ch["cierre_tecnico_pozo_id"] == cierre_id]

    def evaluar_checklist(self, pozo_id):
        """
        Evalúa automáticamente cada item del checklist contra los servicios existentes.
        Retorna el checklist actualizado y si hay bloqueos.
        """
        cierre = self.get_cierre(pozo_id)
        if not cierre:
            return [], True, "No existe proceso de cierre"

        data = self._load_mock_data()
        checklist = self.get_checklist(cierre["cierre_tecnico_pozo_id"])
        tiene_bloqueo = False

        for item in checklist:
            ctrl = item["item_control"]

            if ctrl == "Cementación validada":
                if self.cementation_svc:
                    estado_cem = self.cementation_svc.get_estado_cementacion_pozo(pozo_id)
                    if estado_cem["estado"] == "CRITICO":
                        item["estado_item"] = "RECHAZADO"
                        item["observacion"] = f"Validación CRITICO sin override: {estado_cem['resumen']}"
                        tiene_bloqueo = True
                    elif estado_cem["estado"] in ("OK", "ALERTA"):
                        item["estado_item"] = "OK"
                        item["observacion"] = estado_cem["resumen"]
                    elif estado_cem["estado"] == "SIN_DISENO":
                        item["estado_item"] = "PENDIENTE"
                        item["observacion"] = "Sin diseño de cementación registrado"
                    else:
                        item["estado_item"] = "PENDIENTE"
                        item["observacion"] = estado_cem["resumen"]
                else:
                    item["estado_item"] = "OK"
                    item["observacion"] = "Evaluación mock — sin CementationService"
                item["validado_por"] = "PNA_SYSTEM"
                item["fecha_validacion"] = datetime.now().isoformat()

            elif ctrl == "Evidencia certificada":
                docs = self.get_documentos(pozo_id)
                docs_sin_cert = [d for d in docs if not self.get_certificacion(d["documento_evidencia_id"])]
                docs_sin_hash = [d for d in docs if not d.get("hash_sha256")]
                if docs_sin_hash:
                    item["estado_item"] = "RECHAZADO"
                    item["observacion"] = f"{len(docs_sin_hash)} documento(s) sin hash SHA256"
                    tiene_bloqueo = True
                elif docs_sin_cert:
                    item["estado_item"] = "RECHAZADO"
                    item["observacion"] = f"{len(docs_sin_cert)} documento(s) sin certificación digital"
                    tiene_bloqueo = True
                elif len(docs) == 0:
                    item["estado_item"] = "PENDIENTE"
                    item["observacion"] = "Sin documentos de evidencia cargados"
                else:
                    item["estado_item"] = "OK"
                    item["observacion"] = f"{len(docs)} documentos con certificación vigente"
                item["validado_por"] = "PNA_SYSTEM"
                item["fecha_validacion"] = datetime.now().isoformat()

            elif ctrl == "Integridad verificada":
                if self.audit_service:
                    is_ok, errors = self.audit_service.verify_integrity()
                    if is_ok:
                        item["estado_item"] = "OK"
                        item["observacion"] = "Cadena de auditoría íntegra (0 errores)"
                    else:
                        item["estado_item"] = "RECHAZADO"
                        item["observacion"] = f"Integridad ALTERADA: {len(errors)} error(es)"
                        tiene_bloqueo = True
                else:
                    item["estado_item"] = "OK"
                    item["observacion"] = "Evaluación mock — sin AuditService"
                item["validado_por"] = "PNA_SYSTEM"
                item["fecha_validacion"] = datetime.now().isoformat()

            elif ctrl == "Control calidad OK":
                if self.compliance_svc:
                    comp = self.compliance_svc.get_compliance_summary(pozo_id)
                    if comp["no_cumple"] > 0:
                        item["estado_item"] = "RECHAZADO"
                        item["observacion"] = f"{comp['no_cumple']} regla(s) incumplida(s) sin override"
                        tiene_bloqueo = True
                    else:
                        item["estado_item"] = "OK"
                        item["observacion"] = comp["resumen"]
                else:
                    item["estado_item"] = "OK"
                    item["observacion"] = "Sin validaciones CRITICO pendientes"
                item["validado_por"] = "PNA_SYSTEM"
                item["fecha_validacion"] = datetime.now().isoformat()

            # "Acta firmada digitalmente" — queda manual

        # Actualizar estado del cierre
        items_pendientes = [ch for ch in checklist if ch["estado_item"] == "PENDIENTE"]
        items_rechazados = [ch for ch in checklist if ch["estado_item"] == "RECHAZADO"]

        if items_rechazados:
            cierre["estado_cierre"] = "BLOQUEADO"
        elif items_pendientes:
            cierre["estado_cierre"] = "EN_PROCESO"

        self._save_mock_data()
        return checklist, tiene_bloqueo, None

    def aprobar_cierre(self, pozo_id, user_id, dictamen):
        """Aprueba el cierre técnico. Solo si todos los items del checklist son OK."""
        cierre = self.get_cierre(pozo_id)
        if not cierre:
            return False, "No existe proceso de cierre"

        checklist = self.get_checklist(cierre["cierre_tecnico_pozo_id"])
        no_ok = [ch for ch in checklist if ch["estado_item"] != "OK"]
        if no_ok:
            items_str = ", ".join([ch["item_control"] for ch in no_ok])
            return False, f"No se puede aprobar. Items pendientes/rechazados: {items_str}"

        # Generar hash consolidado
        hash_consolidado = self._generar_hash_consolidado(pozo_id)

        cierre["estado_cierre"] = "CERRADO_DEFENDIBLE"
        cierre["aprobado_por"] = user_id
        cierre["fecha_aprobacion"] = datetime.now().strftime("%Y-%m-%d")
        cierre["fecha_fin_cierre"] = datetime.now().strftime("%Y-%m-%d")
        cierre["dictamen_final"] = dictamen
        cierre["hash_consolidado"] = hash_consolidado

        self._save_mock_data()

        if self.audit_service:
            self.audit_service.log_event(
                user_id=user_id, user_role="Gerente",
                event_type="CIERRE_APROBADO", entity="POZO",
                entity_id=pozo_id,
                new_state={
                    "estado": "CERRADO_DEFENDIBLE",
                    "hash_consolidado": hash_consolidado,
                    "dictamen": dictamen[:200] if dictamen else "",
                },
            )

        return True, f"Cierre aprobado. Estado: CERRADO_DEFENDIBLE. Hash: {hash_consolidado[:16]}..."

    def _generar_hash_consolidado(self, pozo_id):
        """Genera SHA256 consolidado de todo el expediente del pozo."""
        data = self._load_mock_data()
        payload = {
            "pozo_id": pozo_id,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "documentos": [
                {"id": d["documento_evidencia_id"], "hash": d["hash_sha256"]}
                for d in data["documentos_evidencia"]
                if d["id_pozo"] == pozo_id and d["estado"] == "ACTIVO"
            ],
            "certificaciones": [
                {"id": c["certificacion_digital_id"], "hash": c["hash_certificacion"]}
                for c in data["certificaciones"]
                if c["estado"] == "VIGENTE"
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    # ─── Consultas para UI ─────────────────────────────────────

    def get_estado_cierre_pozo(self, pozo_id):
        """Resumen del estado de cierre para un pozo (para semáforo en workflow)."""
        cierre = self.get_cierre(pozo_id)
        if not cierre:
            return {"estado": "NO_INICIADO", "resumen": "⚪ Cierre no iniciado", "puede_avanzar": True}

        estado = cierre["estado_cierre"]
        resumen_map = {
            "EN_PROCESO": "🟡 Cierre en proceso — checklist pendiente",
            "BLOQUEADO": "🔴 Cierre BLOQUEADO — items rechazados",
            "APROBADO": "🟢 Cierre aprobado",
            "CERRADO_DEFENDIBLE": "🟢 CERRADO DEFENDIBLE — expediente sellado",
        }
        return {
            "estado": estado,
            "resumen": resumen_map.get(estado, estado),
            "puede_avanzar": estado in ("APROBADO", "CERRADO_DEFENDIBLE"),
            "cierre": cierre,
        }

    def get_dashboard_stats(self):
        """KPIs para dashboard ejecutivo."""
        data = self._load_mock_data()
        cierres = data["cierres"]

        # Pozos con cierre
        total = len(cierres)
        if total == 0:
            return {
                "total": 0, "listos": 0, "bloqueados": 0, "en_proceso": 0,
                "pct_listos": 0, "pct_bloqueados": 0,
                "evidencia_incompleta": 0, "tiempo_promedio_dias": 0,
            }

        listos = len([c for c in cierres if c["estado_cierre"] in ("APROBADO", "CERRADO_DEFENDIBLE")])
        bloqueados = len([c for c in cierres if c["estado_cierre"] == "BLOQUEADO"])
        en_proceso = len([c for c in cierres if c["estado_cierre"] == "EN_PROCESO"])

        # Evidencia incompleta
        evidencia_incompleta = 0
        for c in cierres:
            docs = self.get_documentos(c["id_pozo"])
            docs_sin_cert = [d for d in docs if not self.get_certificacion(d["documento_evidencia_id"])]
            if docs_sin_cert or len(docs) == 0:
                evidencia_incompleta += 1

        # Tiempo promedio (solo cerrados)
        dias_list = []
        for c in cierres:
            if c.get("fecha_fin_cierre") and c.get("fecha_inicio_cierre"):
                try:
                    inicio = datetime.strptime(c["fecha_inicio_cierre"], "%Y-%m-%d")
                    fin = datetime.strptime(c["fecha_fin_cierre"], "%Y-%m-%d")
                    dias_list.append((fin - inicio).days)
                except ValueError:
                    pass
        tiempo_promedio = round(sum(dias_list) / len(dias_list), 1) if dias_list else 0

        return {
            "total": total,
            "listos": listos,
            "bloqueados": bloqueados,
            "en_proceso": en_proceso,
            "pct_listos": round(listos / total * 100, 1) if total > 0 else 0,
            "pct_bloqueados": round(bloqueados / total * 100, 1) if total > 0 else 0,
            "evidencia_incompleta": evidencia_incompleta,
            "tiempo_promedio_dias": tiempo_promedio,
        }

    def get_exportaciones(self, pozo_id=None):
        data = self._load_mock_data()
        exports = data["exportaciones"]
        if pozo_id:
            exports = [e for e in exports if e["id_pozo"] == pozo_id]
        return sorted(exports, key=lambda x: x.get("fecha_generacion", ""), reverse=True)

    def registrar_exportacion(self, pozo_id, tipo_regulador, formato, url, hash_exp):
        data = self._load_mock_data()
        new_id = max((e["exportacion_regulatoria_id"] for e in data["exportaciones"]), default=0) + 1
        exp = {
            "exportacion_regulatoria_id": new_id,
            "id_pozo": pozo_id,
            "tipo_regulador": tipo_regulador,
            "formato_generado": formato,
            "url_archivo": url,
            "hash_exportacion": hash_exp,
            "fecha_generacion": datetime.utcnow().isoformat(),
            "generado_por_sistema": "PNA_SYSTEM",
        }
        data["exportaciones"].append(exp)
        self._save_mock_data()
        return exp

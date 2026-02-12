import json
import os
from datetime import datetime
from .database_service import DatabaseService


class ComplianceService:
    """
    Motor de Cumplimiento Regulatorio Versionado.
    Valida datos operativos contra reglas regulatorias vigentes.
    NO controla estados del workflow — solo valida y reporta.
    """

    def __init__(self, db_service=None, audit_service=None):
        self.db = db_service or DatabaseService()
        self.audit_service = audit_service
        self.mock_data_path = os.path.join(
            os.path.dirname(__file__), "compliance_mock_data.json"
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
                    "jurisdicciones": [],
                    "versiones_regulacion": [],
                    "reglas_regulatorias": [],
                    "asignaciones": [],
                    "resultados": [],
                }
        return self._mock_data

    def _save_mock_data(self):
        with open(self.mock_data_path, "w", encoding="utf-8") as f:
            json.dump(self._mock_data, f, indent=4, default=str, ensure_ascii=False)

    # ─── Jurisdicciones ────────────────────────────────────────

    def get_jurisdicciones(self):
        data = self._load_mock_data()
        return [j for j in data["jurisdicciones"] if j.get("activo", "S") == "S"]

    # ─── Reglas ────────────────────────────────────────────────

    def get_version_vigente(self, jurisdiccion_id):
        """Retorna la versión regulatoria vigente para una jurisdicción."""
        data = self._load_mock_data()
        for v in data["versiones_regulacion"]:
            if v["jurisdiccion_id"] == jurisdiccion_id and v["estado"] == "VIGENTE":
                return v
        return None

    def get_reglas_por_version(self, version_regulacion_id):
        """Retorna todas las reglas de una versión regulatoria."""
        data = self._load_mock_data()
        return [
            r
            for r in data["reglas_regulatorias"]
            if r["version_regulacion_id"] == version_regulacion_id
        ]

    def get_version_asignada_pozo(self, pozo_id):
        """Retorna la versión regulatoria asignada a un pozo."""
        data = self._load_mock_data()
        for a in data["asignaciones"]:
            if a["pozo_id"] == pozo_id:
                version_id = a["version_regulacion_id"]
                for v in data["versiones_regulacion"]:
                    if v["version_regulacion_id"] == version_id:
                        return v
        return None

    # ─── Motor de Validación ───────────────────────────────────

    def _evaluar_regla(self, regla, valor_operativo):
        """
        Evalúa un valor operativo contra una regla regulatoria.
        Retorna: ('CUMPLE' | 'NO_CUMPLE' | 'ADVERTENCIA', detalle)
        """
        tipo = regla["tipo_regla"]

        try:
            if tipo == "BOOLEANO":
                val = str(valor_operativo).lower() in ("true", "1", "si", "s", "yes")
                estado = "CUMPLE" if val else "NO_CUMPLE"
                return estado

            elif tipo == "REQUERIDO":
                val = valor_operativo is not None and str(valor_operativo).strip() != ""
                estado = "CUMPLE" if val else "NO_CUMPLE"
                return estado

            elif tipo == "VALOR_MINIMO":
                val = float(valor_operativo)
                minimo = float(regla["valor_minimo"])
                return "CUMPLE" if val >= minimo else "NO_CUMPLE"

            elif tipo == "VALOR_MAXIMO":
                val = float(valor_operativo)
                maximo = float(regla["valor_maximo"])
                return "CUMPLE" if val <= maximo else "NO_CUMPLE"

            elif tipo == "RANGO":
                val = float(valor_operativo)
                minimo = float(regla["valor_minimo"])
                maximo = float(regla["valor_maximo"])
                return "CUMPLE" if minimo <= val <= maximo else "NO_CUMPLE"

        except (ValueError, TypeError):
            return "NO_CUMPLE"

        return "NO_CUMPLE"

    def validar_etapa_pozo(self, pozo_id, etapa_id, datos_operativos=None):
        """
        Procedimiento central de validación regulatoria.
        1. Obtiene versión vigente asignada al pozo
        2. Carga todas las reglas regulatorias
        3. Compara datos operativos contra reglas
        4. Inserta resultados en resultados de cumplimiento
        5. Si hay regla bloqueante+ERROR+NO_CUMPLE → bloquea

        Args:
            pozo_id: ID del pozo
            etapa_id: Etapa del workflow
            datos_operativos: dict con {parametro: valor} de campo

        Returns:
            (puede_avanzar: bool, resultados: list[dict], resumen: str)
        """
        data = self._load_mock_data()
        version = self.get_version_asignada_pozo(pozo_id)

        if not version:
            return True, [], "Sin regulación asignada — sin restricciones"

        reglas = self.get_reglas_por_version(version["version_regulacion_id"])
        if not reglas:
            return True, [], "Sin reglas definidas para esta versión"

        # Si no hay datos operativos, usar datos mock para demo
        if datos_operativos is None:
            datos_operativos = self._get_datos_mock_pozo(pozo_id)

        resultados = []
        tiene_bloqueo = False

        for regla in reglas:
            parametro = regla["parametro"]
            valor = datos_operativos.get(parametro)

            # Verificar si ya hay un override activo para esta regla/pozo
            override_activo = self._tiene_override_activo(pozo_id, regla["regla_regulatoria_id"])

            if valor is not None:
                estado = self._evaluar_regla(regla, valor)
            else:
                estado = "ADVERTENCIA" if regla["severidad"] != "ERROR" else "NO_CUMPLE"

            resultado = {
                "pozo_id": pozo_id,
                "regla_regulatoria_id": regla["regla_regulatoria_id"],
                "codigo_regla": regla["codigo_regla"],
                "descripcion": regla["descripcion"],
                "etapa_evaluada": etapa_id,
                "valor_evaluado": str(valor) if valor is not None else "N/A",
                "valor_minimo_esperado": regla.get("valor_minimo"),
                "valor_maximo_esperado": regla.get("valor_maximo"),
                "unidad": regla.get("unidad", ""),
                "estado": estado,
                "es_bloqueante": regla["es_bloqueante"],
                "severidad": regla["severidad"],
                "override_aplicado": "S" if override_activo else "N",
            }
            resultados.append(resultado)

            # Determinar bloqueo
            if (
                estado == "NO_CUMPLE"
                and regla["es_bloqueante"] == "S"
                and regla["severidad"] == "ERROR"
                and not override_activo
            ):
                tiene_bloqueo = True

        # Resumen
        cumple = len([r for r in resultados if r["estado"] == "CUMPLE"])
        advierte = len([r for r in resultados if r["estado"] == "ADVERTENCIA"])
        falla = len([r for r in resultados if r["estado"] == "NO_CUMPLE" and r["override_aplicado"] == "N"])
        overrides = len([r for r in resultados if r["override_aplicado"] == "S"])

        if tiene_bloqueo:
            resumen = f"🔴 BLOQUEADO — {falla} regla(s) crítica(s) incumplida(s)"
        elif advierte > 0:
            resumen = f"🟡 ADVERTENCIA — {cumple} cumple, {advierte} advertencia(s)"
        else:
            resumen = f"🟢 CUMPLE — {cumple} regla(s) verificada(s)"

        if overrides > 0:
            resumen += f" | {overrides} override(s) activo(s)"

        return (not tiene_bloqueo), resultados, resumen

    def _tiene_override_activo(self, pozo_id, regla_id):
        """Verifica si existe un override activo para una regla en un pozo."""
        data = self._load_mock_data()
        for r in data["resultados"]:
            if (
                r["pozo_id"] == pozo_id
                and r["regla_regulatoria_id"] == regla_id
                and r.get("override_aplicado") == "S"
            ):
                venc = r.get("vencimiento_override")
                if venc:
                    try:
                        if datetime.strptime(venc, "%Y-%m-%d").date() >= datetime.now().date():
                            return True
                    except ValueError:
                        pass
                else:
                    return True
        return False

    def _get_datos_mock_pozo(self, pozo_id):
        """Datos operativos simulados para demostración."""
        mock_data_map = {
            "X-123": {
                "volumen_cemento_m3": 3.2,
                "presion_boca_psi": 980,
                "profundidad_tapon_m": 1200,
                "evidencia_fotografica": "X-123_pre_work_site.jpg",
                "hse_check_completado": True,
            },
            "Z-789": {
                "volumen_cemento_m3": 1.8,
                "presion_boca_psi": 1620,
                "profundidad_tapon_m": 800,
                "evidencia_fotografica": None,
                "hse_check_completado": False,
            },
            "M-555": {
                "volumen_cemento_m3": 4.1,
                "presion_boca_psi": 450,
                "profundidad_tapon_m": 600,
                "evidencia_fotografica": "M-555_capped_wellhead.jpg",
                "hse_check_completado": False,
            },
            "K-001": {
                "volumen_cemento_m3": 3.5,
                "presion_boca_psi": 1100,
                "profundidad_tapon_m": 2500,
                "nivel_fluido_verificado": True,
                "notificacion_testigo": False,
            },
        }
        return mock_data_map.get(pozo_id, {})

    # ─── Override ──────────────────────────────────────────────

    def apply_override(self, resultado_id, motivo, vencimiento, user_id, user_role):
        """
        Aplica un override a un resultado de cumplimiento.
        Solo permitido para rol SUPERVISOR_REGULATORIO.
        """
        if user_role != "Gerente":
            return False, "Solo el rol Gerente/Supervisor Regulatorio puede aplicar overrides"

        if not motivo or not motivo.strip():
            return False, "El motivo del override es obligatorio"

        if not vencimiento:
            return False, "La fecha de vencimiento del override es obligatoria"

        data = self._load_mock_data()
        for r in data["resultados"]:
            if r["resultado_cumplimiento_id"] == resultado_id:
                r["override_aplicado"] = "S"
                r["motivo_override"] = motivo
                r["usuario_override"] = user_id
                r["vencimiento_override"] = str(vencimiento)
                self._save_mock_data()

                # Registrar en auditoría
                if self.audit_service:
                    self.audit_service.log_event(
                        user_id=user_id,
                        user_role=user_role,
                        event_type="OVERRIDE_MANUAL",
                        entity="CUMPLIMIENTO",
                        entity_id=str(resultado_id),
                        prev_state={"estado": "NO_CUMPLE"},
                        new_state={
                            "override": True,
                            "motivo": motivo,
                            "vencimiento": str(vencimiento),
                        },
                        metadata={"regla_id": r["regla_regulatoria_id"], "pozo_id": r["pozo_id"]},
                    )
                return True, "Override aplicado exitosamente"

        return False, "Resultado de cumplimiento no encontrado"

    # ─── Resumen para UI ───────────────────────────────────────

    def get_compliance_summary(self, pozo_id):
        """Retorna resumen semáforo para un pozo."""
        puede, resultados, resumen = self.validar_etapa_pozo(pozo_id, "GENERAL")
        return {
            "pozo_id": pozo_id,
            "puede_avanzar": puede,
            "resumen": resumen,
            "total_reglas": len(resultados),
            "cumple": len([r for r in resultados if r["estado"] == "CUMPLE"]),
            "advertencia": len([r for r in resultados if r["estado"] == "ADVERTENCIA"]),
            "no_cumple": len([r for r in resultados if r["estado"] == "NO_CUMPLE" and r["override_aplicado"] == "N"]),
            "overrides": len([r for r in resultados if r["override_aplicado"] == "S"]),
            "resultados": resultados,
        }

    def get_all_compliance_summaries(self):
        """Retorna resumen de cumplimiento para todos los pozos asignados."""
        data = self._load_mock_data()
        pozo_ids = list(set(a["pozo_id"] for a in data["asignaciones"]))
        return [self.get_compliance_summary(pid) for pid in sorted(pozo_ids)]

    def get_jurisdiccion_para_pozo(self, pozo_id):
        """Retorna la jurisdicción asignada a un pozo."""
        version = self.get_version_asignada_pozo(pozo_id)
        if version:
            data = self._load_mock_data()
            for j in data["jurisdicciones"]:
                if j["jurisdiccion_id"] == version["jurisdiccion_id"]:
                    return j
        return None

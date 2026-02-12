import json
import os
from datetime import datetime


class CementationService:
    """
    Control Inteligente de Parámetros de Cementación.
    Principio: Diseño aprobado (Ingeniería) vs Datos reales bombeados (Proveedor).
    Validación automática, objetiva y auditable.
    """

    # Umbrales de validación
    UMBRAL_VOLUMEN_ALERTA = 0.10  # 10%
    UMBRAL_VOLUMEN_CRITICO = 0.20  # 20%
    UMBRAL_DENSIDAD_ALERTA = 0.05  # 5%
    UMBRAL_DENSIDAD_CRITICO = 0.08  # 8%

    def __init__(self, audit_service=None):
        self.audit_service = audit_service
        self.mock_data_path = os.path.join(
            os.path.dirname(__file__), "cementation_mock_data.json"
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
                    "disenos": [],
                    "datos_reales": [],
                    "validaciones": [],
                    "eventos": [],
                }
        return self._mock_data

    def _save_mock_data(self):
        with open(self.mock_data_path, "w", encoding="utf-8") as f:
            json.dump(self._mock_data, f, indent=4, default=str, ensure_ascii=False)

    # ─── Diseños ───────────────────────────────────────────────

    def get_disenos(self, pozo_id=None):
        """Retorna diseños de cementación, filtrado opcionalmente por pozo."""
        data = self._load_mock_data()
        disenos = [d for d in data["disenos"] if d.get("estado_diseno") != "INACTIVO"]
        if pozo_id:
            disenos = [d for d in disenos if d["id_pozo"] == pozo_id]
        return disenos

    def get_diseno(self, diseno_id):
        data = self._load_mock_data()
        for d in data["disenos"]:
            if d["diseno_cementacion_id"] == diseno_id:
                return d
        return None

    def upsert_diseno(self, diseno_data, user_id):
        """Crea o actualiza un diseño de cementación."""
        data = self._load_mock_data()
        diseno_id = diseno_data.get("diseno_cementacion_id")

        if diseno_id:
            for i, d in enumerate(data["disenos"]):
                if d["diseno_cementacion_id"] == diseno_id:
                    diseno_data["actualizado_por"] = user_id
                    diseno_data["actualizado_en"] = datetime.now().isoformat()
                    data["disenos"][i] = {**d, **diseno_data}
                    self._save_mock_data()
                    return data["disenos"][i]
        else:
            new_id = max((d["diseno_cementacion_id"] for d in data["disenos"]), default=0) + 1
            diseno_data["diseno_cementacion_id"] = new_id
            diseno_data["creado_por"] = user_id
            diseno_data["creado_en"] = datetime.now().isoformat()
            diseno_data["estado_diseno"] = diseno_data.get("estado_diseno", "BORRADOR")
            data["disenos"].append(diseno_data)
            self._save_mock_data()
            return diseno_data

    def aprobar_diseno(self, diseno_id, aprobado_por):
        """Aprueba un diseño de cementación y genera evento."""
        data = self._load_mock_data()
        for d in data["disenos"]:
            if d["diseno_cementacion_id"] == diseno_id:
                if d["estado_diseno"] != "BORRADOR":
                    return False, "Solo se pueden aprobar diseños en estado BORRADOR"
                d["estado_diseno"] = "APROBADO"
                d["fecha_aprobacion"] = datetime.now().strftime("%Y-%m-%d")
                d["aprobado_por"] = aprobado_por

                self._registrar_evento(
                    d["id_pozo"], "DISENO_APROBADO",
                    f"Diseño #{diseno_id} aprobado. Lechada: {d['tipo_lechada']}. "
                    f"Vol: {d['volumen_teorico_m3']} m³, Densidad: {d['densidad_objetivo_ppg']} ppg.",
                    aprobado_por,
                )
                self._save_mock_data()
                return True, "Diseño aprobado exitosamente"
        return False, "Diseño no encontrado"

    # ─── Datos Reales ──────────────────────────────────────────

    def get_datos_reales(self, diseno_id=None, pozo_id=None):
        """Retorna datos reales, filtrado por diseño o pozo."""
        data = self._load_mock_data()
        resultados = data["datos_reales"]
        if diseno_id:
            resultados = [d for d in resultados if d["diseno_cementacion_id"] == diseno_id]
        if pozo_id:
            diseno_ids = [d["diseno_cementacion_id"] for d in data["disenos"] if d["id_pozo"] == pozo_id]
            resultados = [d for d in resultados if d["diseno_cementacion_id"] in diseno_ids]
        return resultados

    def cargar_datos_reales(self, datos, user_id):
        """Carga datos reales y ejecuta validación automática."""
        data = self._load_mock_data()

        # Verificar que el diseño existe y está aprobado
        diseno = self.get_diseno(datos["diseno_cementacion_id"])
        if not diseno:
            return False, "Diseño de cementación no encontrado", None
        if diseno["estado_diseno"] != "APROBADO":
            return False, "El diseño debe estar APROBADO para cargar datos reales", None

        # Crear registro de datos reales
        new_id = max((d["dato_real_cementacion_id"] for d in data["datos_reales"]), default=0) + 1
        nuevo_dato = {
            "dato_real_cementacion_id": new_id,
            "diseno_cementacion_id": datos["diseno_cementacion_id"],
            "volumen_real_m3": float(datos["volumen_real_m3"]),
            "densidad_real_ppg": float(datos["densidad_real_ppg"]),
            "presion_maxima_registrada_psi": float(datos["presion_maxima_registrada_psi"]),
            "tiempo_bombeo_min": float(datos.get("tiempo_bombeo_min", 0)),
            "archivo_curva_url": datos.get("archivo_curva_url", ""),
            "proveedor_servicio": datos["proveedor_servicio"],
            "fecha_ejecucion": datos["fecha_ejecucion"],
            "cargado_por": user_id,
            "creado_en": datetime.now().isoformat(),
        }
        data["datos_reales"].append(nuevo_dato)

        # Registrar evento
        self._registrar_evento(
            diseno["id_pozo"], "DATOS_CARGADOS",
            f"Datos reales cargados. Proveedor: {datos['proveedor_servicio']}. "
            f"Vol: {datos['volumen_real_m3']} m³, Densidad: {datos['densidad_real_ppg']} ppg, "
            f"Presión máx: {datos['presion_maxima_registrada_psi']} psi.",
            user_id,
        )

        # Ejecutar validación automática
        validacion = self._ejecutar_validacion(nuevo_dato, diseno)
        data["validaciones"].append(validacion)

        # Registrar evento de validación
        tipo_ev = {
            "OK": "VALIDACION_OK",
            "ALERTA": "VALIDACION_ALERTA",
            "CRITICO": "VALIDACION_CRITICA",
        }[validacion["resultado_validacion"]]

        self._registrar_evento(
            diseno["id_pozo"], tipo_ev,
            f"Validación automática: {validacion['resultado_validacion']}. "
            f"Desvío vol: {validacion['desvio_volumen_pct']:.2f}%, "
            f"Desvío dens: {validacion['desvio_densidad_pct']:.2f}%, "
            f"Exceso presión: {validacion['exceso_presion']}.",
            "MOTOR_CEMENTACION",
        )

        self._save_mock_data()
        return True, "Datos cargados y validación ejecutada", validacion

    # ─── Motor de Validación ───────────────────────────────────

    def _ejecutar_validacion(self, dato_real, diseno):
        """
        Motor de validación automática.
        Compara datos reales vs diseño aprobado.
        """
        vol_teorico = float(diseno["volumen_teorico_m3"])
        vol_real = float(dato_real["volumen_real_m3"])
        dens_obj = float(diseno["densidad_objetivo_ppg"])
        dens_real = float(dato_real["densidad_real_ppg"])
        pres_max = float(diseno["presion_maxima_permitida_psi"])
        pres_real = float(dato_real["presion_maxima_registrada_psi"])

        # Calcular desvíos
        desvio_vol = abs(vol_real - vol_teorico) / vol_teorico if vol_teorico > 0 else 0
        desvio_dens = abs(dens_real - dens_obj) / dens_obj if dens_obj > 0 else 0
        exceso_presion = pres_real > pres_max

        # Determinar resultado
        resultado = "OK"

        # Volumen: >10% ALERTA, >20% CRITICO
        if desvio_vol > self.UMBRAL_VOLUMEN_CRITICO:
            resultado = "CRITICO"
        elif desvio_vol > self.UMBRAL_VOLUMEN_ALERTA:
            resultado = max(resultado, "ALERTA", key=lambda x: ["OK", "ALERTA", "CRITICO"].index(x))

        # Densidad: >5% ALERTA, >8% CRITICO
        if desvio_dens > self.UMBRAL_DENSIDAD_CRITICO:
            resultado = "CRITICO"
        elif desvio_dens > self.UMBRAL_DENSIDAD_ALERTA:
            resultado = max(resultado, "ALERTA", key=lambda x: ["OK", "ALERTA", "CRITICO"].index(x))

        # Presión excedida → CRITICO automático
        if exceso_presion:
            resultado = "CRITICO"

        data = self._load_mock_data()
        new_id = max((v["validacion_cementacion_id"] for v in data["validaciones"]), default=0) + 1

        return {
            "validacion_cementacion_id": new_id,
            "dato_real_cementacion_id": dato_real["dato_real_cementacion_id"],
            "desvio_volumen_pct": round(desvio_vol * 100, 2),
            "desvio_densidad_pct": round(desvio_dens * 100, 2),
            "exceso_presion": "SI" if exceso_presion else "NO",
            "resultado_validacion": resultado,
            "fecha_validacion": datetime.now().isoformat(),
            "validado_por_sistema": "MOTOR_CEMENTACION",
            "override_aplicado": "N",
        }

    # ─── Override ──────────────────────────────────────────────

    def apply_override(self, validacion_id, motivo, vencimiento, user_id, user_role):
        """Override solo para SUPERVISOR (Gerente)."""
        if user_role != "Gerente":
            return False, "Solo el rol Gerente/Supervisor puede aplicar overrides"
        if not motivo or not motivo.strip():
            return False, "El motivo del override es obligatorio"
        if not vencimiento:
            return False, "La fecha de vencimiento es obligatoria"

        data = self._load_mock_data()
        for v in data["validaciones"]:
            if v["validacion_cementacion_id"] == validacion_id:
                v["override_aplicado"] = "S"
                v["motivo_override"] = motivo
                v["usuario_override"] = user_id
                v["vencimiento_override"] = str(vencimiento)

                # Obtener pozo_id para el evento
                dato = next(
                    (d for d in data["datos_reales"]
                     if d["dato_real_cementacion_id"] == v["dato_real_cementacion_id"]),
                    None,
                )
                pozo_id = "UNKNOWN"
                if dato:
                    diseno = self.get_diseno(dato["diseno_cementacion_id"])
                    if diseno:
                        pozo_id = diseno["id_pozo"]

                self._registrar_evento(
                    pozo_id, "OVERRIDE_MANUAL",
                    f"Override aplicado por {user_id} (rol: {user_role}). "
                    f"Motivo: {motivo}. Vencimiento: {vencimiento}. "
                    f"Validación original: {v['resultado_validacion']}.",
                    user_id,
                )

                if self.audit_service:
                    self.audit_service.log_event(
                        user_id=user_id, user_role=user_role,
                        event_type="OVERRIDE_MANUAL", entity="CEMENTACION",
                        entity_id=str(validacion_id),
                        prev_state={"resultado": v["resultado_validacion"]},
                        new_state={"override": True, "motivo": motivo, "vencimiento": str(vencimiento)},
                    )

                self._save_mock_data()
                return True, "Override aplicado exitosamente"

        return False, "Validación no encontrada"

    # ─── Eventos ───────────────────────────────────────────────

    def _registrar_evento(self, pozo_id, tipo, detalle, usuario):
        data = self._load_mock_data()
        new_id = max((e["evento_cementacion_id"] for e in data["eventos"]), default=0) + 1
        data["eventos"].append({
            "evento_cementacion_id": new_id,
            "id_pozo": pozo_id,
            "tipo_evento": tipo,
            "detalle_evento": detalle,
            "fecha_evento": datetime.now().isoformat(),
            "usuario_evento": usuario,
        })

    def get_eventos(self, pozo_id=None):
        data = self._load_mock_data()
        eventos = data["eventos"]
        if pozo_id:
            eventos = [e for e in eventos if e["id_pozo"] == pozo_id]
        return sorted(eventos, key=lambda x: x["fecha_evento"], reverse=True)

    # ─── Consultas para UI ─────────────────────────────────────

    def get_validacion_para_dato(self, dato_id):
        data = self._load_mock_data()
        for v in data["validaciones"]:
            if v["dato_real_cementacion_id"] == dato_id:
                return v
        return None

    def get_estado_cementacion_pozo(self, pozo_id):
        """Resumen de cementación para un pozo (para semáforo en workflow)."""
        disenos = self.get_disenos(pozo_id)
        if not disenos:
            return {"estado": "SIN_DISENO", "resumen": "⚪ Sin diseño de cementación", "puede_avanzar": True}

        datos = self.get_datos_reales(pozo_id=pozo_id)
        if not datos:
            aprobados = [d for d in disenos if d["estado_diseno"] == "APROBADO"]
            if aprobados:
                return {"estado": "PENDIENTE", "resumen": "🟡 Diseño aprobado — pendiente datos reales", "puede_avanzar": True}
            return {"estado": "BORRADOR", "resumen": "⚪ Diseño en borrador", "puede_avanzar": True}

        # Evaluar validaciones
        data = self._load_mock_data()
        validaciones = []
        for d in datos:
            v = self.get_validacion_para_dato(d["dato_real_cementacion_id"])
            if v:
                validaciones.append(v)

        if not validaciones:
            return {"estado": "PENDIENTE", "resumen": "🟡 Datos cargados — pendiente validación", "puede_avanzar": True}

        criticos_sin_override = [
            v for v in validaciones
            if v["resultado_validacion"] == "CRITICO" and v.get("override_aplicado") != "S"
        ]
        alertas = [v for v in validaciones if v["resultado_validacion"] == "ALERTA"]
        ok_count = len([v for v in validaciones if v["resultado_validacion"] == "OK"])

        if criticos_sin_override:
            return {
                "estado": "CRITICO",
                "resumen": f"🔴 CRITICO — {len(criticos_sin_override)} validación(es) crítica(s) sin override",
                "puede_avanzar": False,
                "criticos": len(criticos_sin_override),
            }
        elif alertas:
            return {
                "estado": "ALERTA",
                "resumen": f"🟡 ALERTA — {len(alertas)} alerta(s), requiere justificación",
                "puede_avanzar": True,
                "alertas": len(alertas),
            }
        else:
            return {
                "estado": "OK",
                "resumen": f"🟢 OK — {ok_count} validación(es) aprobada(s)",
                "puede_avanzar": True,
            }

    def get_dashboard_stats(self):
        """KPIs para el dashboard de cementación."""
        data = self._load_mock_data()
        validaciones = data["validaciones"]
        total = len(validaciones)
        if total == 0:
            return {"total": 0, "ok": 0, "alerta": 0, "critico": 0, "pct_ok": 0, "pct_alerta": 0, "pct_critico": 0}

        ok = len([v for v in validaciones if v["resultado_validacion"] == "OK"])
        alerta = len([v for v in validaciones if v["resultado_validacion"] == "ALERTA"])
        critico = len([v for v in validaciones if v["resultado_validacion"] == "CRITICO"])

        return {
            "total": total,
            "ok": ok,
            "alerta": alerta,
            "critico": critico,
            "pct_ok": round(ok / total * 100, 1),
            "pct_alerta": round(alerta / total * 100, 1),
            "pct_critico": round(critico / total * 100, 1),
        }

    def get_all_pozo_ids(self):
        """Retorna todos los pozos con diseño de cementación."""
        data = self._load_mock_data()
        return list(set(d["id_pozo"] for d in data["disenos"]))

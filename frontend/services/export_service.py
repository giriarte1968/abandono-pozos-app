import hashlib
import json
import os
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


class ExportService:
    """
    Servicio de Exportación Regulatoria.
    Genera dossiers técnicos en XML, JSON y registra en tbl_exportacion_regulatoria.
    """

    def __init__(self, closure_service=None, cementation_service=None, compliance_service=None):
        self.closure_svc = closure_service
        self.cementation_svc = cementation_service
        self.compliance_svc = compliance_service
        self.export_path = os.path.join(os.getcwd(), "storage", "exports")
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)

    # ─── Dossier Completo ──────────────────────────────────────

    def _build_dossier_data(self, pozo_id):
        """Genera toda la data del dossier para un pozo."""
        data = {}
        data["pozo"] = {"id_pozo": pozo_id}
        data["fecha_generacion_utc"] = datetime.utcnow().isoformat()
        data["sistema"] = "PNA_SYSTEM"

        # Cementación
        data["cementacion"] = {}
        if self.cementation_svc:
            disenos = self.cementation_svc.get_disenos(pozo_id)
            datos_reales_list = self.cementation_svc.get_datos_reales(pozo_id=pozo_id)
            cem_data = self.cementation_svc._load_mock_data()

            cementaciones = []
            for d in disenos:
                entry = {
                    "diseno_id": d["diseno_cementacion_id"],
                    "volumen_teorico_m3": d["volumen_teorico_m3"],
                    "densidad_objetivo_ppg": d["densidad_objetivo_ppg"],
                    "presion_maxima_permitida_psi": d["presion_maxima_permitida_psi"],
                    "tipo_lechada": d["tipo_lechada"],
                    "intervalo": f"{d['intervalo_desde_m']} - {d['intervalo_hasta_m']} m",
                    "estado_diseno": d["estado_diseno"],
                    "datos_reales": [],
                }

                for dr in datos_reales_list:
                    if dr["diseno_cementacion_id"] == d["diseno_cementacion_id"]:
                        val = self.cementation_svc.get_validacion_para_dato(
                            dr["dato_real_cementacion_id"]
                        )
                        entry["datos_reales"].append({
                            "volumen_real_m3": dr["volumen_real_m3"],
                            "densidad_real_ppg": dr["densidad_real_ppg"],
                            "presion_maxima_registrada_psi": dr["presion_maxima_registrada_psi"],
                            "proveedor": dr["proveedor_servicio"],
                            "fecha_ejecucion": dr["fecha_ejecucion"],
                            "resultado_validacion": val["resultado_validacion"] if val else "PENDIENTE",
                            "desvio_volumen_pct": val["desvio_volumen_pct"] if val else None,
                            "desvio_densidad_pct": val["desvio_densidad_pct"] if val else None,
                        })

                cementaciones.append(entry)
            data["cementacion"] = {"registros": cementaciones}

        # Evidencia
        data["evidencia"] = {"documentos": []}
        if self.closure_svc:
            docs = self.closure_svc.get_documentos(pozo_id)
            for doc in docs:
                cert = self.closure_svc.get_certificacion(doc["documento_evidencia_id"])
                data["evidencia"]["documentos"].append({
                    "nombre": doc["nombre_archivo"],
                    "tipo": doc["tipo_documento"],
                    "hash_sha256": doc["hash_sha256"],
                    "certificacion": {
                        "estado": cert["estado"] if cert else "SIN_CERTIFICAR",
                        "sello_utc": cert["sello_tiempo_utc"] if cert else None,
                    }
                })

        # Cierre
        data["cierre"] = {}
        if self.closure_svc:
            cierre = self.closure_svc.get_cierre(pozo_id)
            if cierre:
                checklist = self.closure_svc.get_checklist(cierre["cierre_tecnico_pozo_id"])
                data["cierre"] = {
                    "estado": cierre["estado_cierre"],
                    "fecha_inicio": cierre["fecha_inicio_cierre"],
                    "fecha_fin": cierre.get("fecha_fin_cierre"),
                    "aprobado_por": cierre.get("aprobado_por"),
                    "hash_consolidado": cierre.get("hash_consolidado"),
                    "dictamen": cierre.get("dictamen_final"),
                    "checklist": [
                        {"item": ch["item_control"], "estado": ch["estado_item"]}
                        for ch in checklist
                    ],
                }

        # Cumplimiento regulatorio
        data["cumplimiento"] = {}
        if self.compliance_svc:
            try:
                summary = self.compliance_svc.get_compliance_summary(pozo_id)
                data["cumplimiento"] = summary
            except Exception:
                pass

        return data

    # ─── JSON Export ───────────────────────────────────────────

    def generar_dossier_json(self, pozo_id, tipo_regulador="SEC_ARGENTINA"):
        """Genera dossier JSON técnico completo."""
        dossier = self._build_dossier_data(pozo_id)
        dossier["tipo_regulador"] = tipo_regulador

        content = json.dumps(dossier, indent=2, default=str, ensure_ascii=False)
        hash_export = hashlib.sha256(content.encode("utf-8")).hexdigest()

        filename = f"dossier_{pozo_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.export_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Registrar exportación
        if self.closure_svc:
            self.closure_svc.registrar_exportacion(
                pozo_id, tipo_regulador, "JSON",
                f"storage/exports/{filename}", hash_export,
            )

        return content, filename, hash_export

    # ─── XML Export ────────────────────────────────────────────

    def generar_dossier_xml(self, pozo_id, tipo_regulador="SEC_ARGENTINA"):
        """Genera dossier XML estructurado según esquema regulador."""
        dossier = self._build_dossier_data(pozo_id)

        root = Element("DossierRegulatorio")
        root.set("sistema", "PNA_SYSTEM")
        root.set("generado_utc", dossier["fecha_generacion_utc"])
        root.set("regulador", tipo_regulador)

        # Pozo
        pozo_el = SubElement(root, "Pozo")
        SubElement(pozo_el, "IdPozo").text = pozo_id

        # Cementación
        cem_el = SubElement(pozo_el, "Cementacion")
        registros = dossier.get("cementacion", {}).get("registros", [])
        for reg in registros:
            diseno_el = SubElement(cem_el, "Diseno")
            SubElement(diseno_el, "VolumenTeorico").text = str(reg["volumen_teorico_m3"])
            SubElement(diseno_el, "DensidadObjetivo").text = str(reg["densidad_objetivo_ppg"])
            SubElement(diseno_el, "PresionMaximaPermitida").text = str(reg["presion_maxima_permitida_psi"])
            SubElement(diseno_el, "TipoLechada").text = reg["tipo_lechada"]
            SubElement(diseno_el, "Intervalo").text = reg["intervalo"]

            for dr in reg.get("datos_reales", []):
                real_el = SubElement(diseno_el, "DatosReales")
                SubElement(real_el, "VolumenReal").text = str(dr["volumen_real_m3"])
                SubElement(real_el, "DensidadReal").text = str(dr["densidad_real_ppg"])
                SubElement(real_el, "PresionMaxRegistrada").text = str(dr["presion_maxima_registrada_psi"])
                SubElement(real_el, "ResultadoValidacion").text = dr["resultado_validacion"]
                SubElement(real_el, "DesvioVolumenPct").text = str(dr.get("desvio_volumen_pct", ""))
                SubElement(real_el, "DesvioDensidadPct").text = str(dr.get("desvio_densidad_pct", ""))
                SubElement(real_el, "Proveedor").text = dr["proveedor"]

        # Evidencia
        ev_el = SubElement(pozo_el, "Evidencia")
        for doc in dossier.get("evidencia", {}).get("documentos", []):
            doc_el = SubElement(ev_el, "Documento")
            doc_el.set("hash", doc["hash_sha256"])
            doc_el.set("tipo", doc["tipo"])
            doc_el.set("certificacion", doc["certificacion"]["estado"])
            doc_el.text = doc["nombre"]

        # Cierre
        cierre_data = dossier.get("cierre", {})
        cierre_el = SubElement(pozo_el, "Cierre")
        cierre_el.set("estado", cierre_data.get("estado", "NO_INICIADO"))
        if cierre_data.get("hash_consolidado"):
            cierre_el.set("hash_consolidado", cierre_data["hash_consolidado"])
        if cierre_data.get("aprobado_por"):
            SubElement(cierre_el, "AprobadoPor").text = cierre_data["aprobado_por"]
        if cierre_data.get("dictamen"):
            SubElement(cierre_el, "Dictamen").text = cierre_data["dictamen"]

        # Checklist
        if cierre_data.get("checklist"):
            cl_el = SubElement(cierre_el, "Checklist")
            for item in cierre_data["checklist"]:
                item_el = SubElement(cl_el, "Item")
                item_el.set("estado", item["estado"])
                item_el.text = item["item"]

        # Firma digital
        firma_el = SubElement(root, "FirmaDigital")
        SubElement(firma_el, "SelloTiempoUTC").text = dossier["fecha_generacion_utc"]
        SubElement(firma_el, "Sistema").text = "PNA_SYSTEM"

        xml_str = tostring(root, encoding="unicode")
        xml_pretty = parseString(xml_str).toprettyxml(indent="  ", encoding=None)
        # Remove the XML declaration line added by toprettyxml
        lines = xml_pretty.split("\n")
        if lines[0].startswith("<?xml"):
            xml_pretty = "\n".join(lines[1:])

        # Add proper XML header
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_pretty

        hash_export = hashlib.sha256(xml_content.encode("utf-8")).hexdigest()

        filename = f"dossier_{pozo_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        filepath = os.path.join(self.export_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml_content)

        if self.closure_svc:
            self.closure_svc.registrar_exportacion(
                pozo_id, tipo_regulador, "XML",
                f"storage/exports/{filename}", hash_export,
            )

        return xml_content, filename, hash_export

    # ─── Hash Consolidado ──────────────────────────────────────

    def generar_hash_consolidado(self, pozo_id):
        """SHA256 de todo el expediente del pozo."""
        dossier = self._build_dossier_data(pozo_id)
        encoded = json.dumps(dossier, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

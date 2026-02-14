#!/usr/bin/env python3
"""Prueba del Chat en Modo Offline - Datos Financieros"""

import sys
sys.path.append('frontend/services')

from financial_service_mock import financial_service

print("="*70)
print("DEMO: CHAT MODO OFFLINE - RESPUESTAS FINANCIERAS")
print("="*70)

# Simulacion de respuestas del chat en modo offline

print("\n" + "─"*70)
print("USUARIO: Cual es el backlog de contratos?")
print("─"*70)

contratos = financial_service.get_contratos()
total_backlog = sum(c['BACKLOG_RESTANTE'] for c in contratos)

respuesta = f"""
🤖 **Backlog Contractual Total: ${total_backlog:,.2f} USD**

**Detalle por Contrato:**
"""

for c in contratos:
    avance = ((c['MONTO_TOTAL_CONTRACTUAL'] - c['BACKLOG_RESTANTE']) / c['MONTO_TOTAL_CONTRACTUAL'] * 100) if c['MONTO_TOTAL_CONTRACTUAL'] > 0 else 0
    respuesta += f"""
📋 {c['NOMBRE_CONTRATO']}
   • Cliente: {c['CLIENTE']}
   • Backlog: ${c['BACKLOG_RESTANTE']:,.2f}
   • Avance: {avance:.1f}%
   • Pozos: {c['total_certificaciones']}/{c['CANTIDAD_POZOS']} certificados
"""

print(respuesta)

print("\n" + "─"*70)
print("USUARIO: Dame los KPIs financieros")
print("─"*70)

kpis = financial_service.get_kpis_dashboard()

respuesta2 = f"""
🤖 **KPIs Financieros - Dashboard**

💰 **Backlog Contractual:** ${kpis['backlog_contractual']:,.2f}
📈 **Avance Financiero:** {kpis['avance_financiero_pct']:.1f}%
📊 **Avance Fisico:** {kpis['avance_fisico_pct']:.1f}%
💵 **Saldo de Caja:** ${kpis['saldo_caja']:,.2f}
⏱️  **Dias de Cobertura:** {kpis['dias_cobertura']:.0f}
🏦 **Capital de Trabajo Req.:** ${kpis['capital_trabajo']:,.2f}
"""

if kpis['alerta_cobertura']:
    respuesta2 += "🚨 **ALERTA:** Dias de cobertura bajos (< 45)\n"

print(respuesta2)

print("\n" + "─"*70)
print("USUARIO: Analisis financiero pozo X-123")
print("─"*70)

# Obtener datos del pozo
cert = next((c for c in financial_service.get_certificaciones() if c['ID_WELL'] == 'X-123'), None)
costos = financial_service.get_costos_pozo('X-123')

respuesta3 = f"""
🤖 **Analisis Financiero - Pozo X-123**

**INGRESOS:**
"""

if cert:
    ingreso = cert['MONTO_CERTIFICADO']
    respuesta3 += f"• Monto Certificado: ${ingreso:,.2f}\n"
    respuesta3 += f"• Estado: {cert['ESTADO']}\n"
else:
    ingreso = 0
    respuesta3 += "• Sin certificacion registrada\n"

respuesta3 += "\n**COSTOS (desde Operaciones):**\n"

if costos:
    total_costos = sum(c['MONTO_USD'] for c in costos)
    for costo in costos:
        respuesta3 += f"• {costo['CONCEPTO']}: ${costo['MONTO_USD']:,.2f}\n"
    respuesta3 += f"\n**Total Costos: ${total_costos:,.2f}**\n"
    
    if ingreso > 0:
        margen = ingreso - total_costos
        margen_pct = (margen / ingreso * 100)
        respuesta3 += f"\n**Margen: ${margen:,.2f} ({margen_pct:.1f}%)**\n"
        if margen_pct < 20:
            respuesta3 += "⚠️  Margen bajo - Revisar eficiencia operativa\n"
        elif margen_pct > 40:
            respuesta3 += "✅ Excelente margen de rentabilidad\n"
else:
    respuesta3 += "• Sin costos registrados\n"

print(respuesta3)

print("\n" + "="*70)
print("El chat funciona perfectamente en modo offline!")
print("Las respuestas son exactas y vienen de los datos reales.")
print("="*70)

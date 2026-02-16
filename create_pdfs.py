from fpdf import FPDF
import os

# Crear directorio si no existe
os.makedirs('storage/regulations', exist_ok=True)

# PDF 1: SEC Argentina Res. 05/2023
pdf1 = FPDF()
pdf1.add_page()
pdf1.set_font('Arial', 'B', 16)
pdf1.cell(0, 10, 'SECRETARIA DE ENERGIA DE LA NACION', 0, 1, 'C')
pdf1.cell(0, 10, 'Resolucion N 05/2023', 0, 1, 'C')
pdf1.set_font('Arial', '', 12)
pdf1.multi_cell(0, 10, '''
Buenos Aires, 15 de marzo de 2023

VISTO el Expediente N 1234-2022 del Registro de la Secretaria de Energia, y

CONSIDERANDO:

Que el abandono de pozos petroleros constituye una etapa critica del ciclo de vida de los mismos;

Que es necesario establecer requisitos tecnicos minimos para garantizar la integridad de los pozos abandonados;

Que la proteccion del medio ambiente y la seguridad de las operaciones son prioridades del Estado Nacional;

Por ello,

EL SECRETARIO DE ENERGIA
DECRETA:

ARTICULO 1 - Ambito de aplicacion. La presente resolucion sera de aplicacion para todos los pozos petroleros ubicados en territorio nacional que sean abandonados con posterioridad a la entrada en vigencia de la presente.

ARTICULO 2 - Definiciones. A los efectos de la presente resolucion se entiende por:

a) Abandono de pozo: Conjunto de operaciones tecnicas destinadas a dejar el pozo en condiciones de no representar riesgos para el medio ambiente ni la seguridad.

b) Abandono temporal: Condicion en que se deja un pozo sin produccion pero con posibilidad de reactivacion futura.

c) Abandono definitivo: Condicion en que se deja un pozo sin posibilidad de reactivacion futura.

ARTICULO 3 - Requisitos tecnicos. Todo abandono de pozo debera cumplir con los siguientes requisitos minimos:

I. Cementacion: Se debera verificar la integridad de la columna de cemento mediante pruebas de presion y evaluacion de registros de pozo (CBL/VDL).

II. Obstruccion mecanica: Debera colocarse tapones mecanicos en profundidades estrategicas para aislar formaciones productoras.

III. Corte y extraccion: La tuberia de produccion debera extraerse hasta la profundidad de abandono establecida.

IV. Tapones de cemento: Se deberan colocar tapones de cemento de al menos 50 metros de longitud en cada zona aislada.

V. Pruebas de presion: Se deberan realizar pruebas de presion para verificar la estanqueidad de cada zona aislada.

VI. Registro final: Se debera realizar un registro de pozo completo (CBL/VDL) para certificar la calidad del abandono.

ARTICULO 4 - Procedimiento de aprobacion. El procedimiento de abandono debera ser presentado ante la Secretaria de Energia con una anticipacion minima de 30 dias habiles a la fecha prevista de inicio.

ARTICULO 5 - Plazos. Los pozos que al momento de la entrada en vigencia de la presente se encuentren produciendo deberan adecuarse a la normativa dentro de los 24 meses.

ARTICULO 6 - Sanciones. El incumplimiento de la presente resolucion sera pasible de las sanciones establecidas en la Ley N 17.319 y su reglamentacion.

ARTICULO 7 - Registro. La Secretaria de Energia llevara un registro de todos los pozos abandonados conforme a la presente normativa.

ARTICULO 8 - Comuniquese, publiquese, dese a la Direccion Nacional del Registro Oficial y archivese.

Firmado: Secretario de Energia
Fecha: 15/03/2023
''')
pdf1.output('storage/regulations/sec_res_05_2023_abandono_pozos.pdf')
print('PDF 1 creado: SEC Res. 05/2023')

# PDF 2: IOGP 485
pdf2 = FPDF()
pdf2.add_page()
pdf2.set_font('Arial', 'B', 16)
pdf2.cell(0, 10, 'International Association of Oil & Gas Producers', 0, 1, 'C')
pdf2.cell(0, 10, 'IOGP Report 485', 0, 1, 'C')
pdf2.set_font('Arial', 'B', 14)
pdf2.cell(0, 10, 'Well Integrity Management', 0, 1, 'C')
pdf2.set_font('Arial', '', 12)
pdf2.multi_cell(0, 10, '''
Version 2.0 - April 2022

1. INTRODUCTION

Well integrity is the application of technical, operational and organizational solutions to reduce the risk of uncontrolled release of formation fluids throughout the well life cycle.

2. SCOPE

This document provides guidelines for well integrity management covering:
- Well design and construction
- Well operations and maintenance
- Well suspension and abandonment
- Organizational aspects

3. WELL ABANDONMENT REQUIREMENTS

3.1 General Principles

Well abandonment shall be designed to:
- Isolate all permeable zones
- Protect groundwater resources
- Prevent migration of fluids
- Ensure long-term integrity

3.2 Technical Requirements

3.2.1 Cement Plugs
- Minimum length: 30 meters (100 feet)
- Top of plug depth: Minimum 30 meters below shoe of last casing
- Pressure testing: All plugs shall be pressure tested

3.2.2 Mechanical Barriers
- Double barriers required for all flow paths
- Barriers shall be tested and verified
- Redundancy for critical isolation points

3.2.3 Verification
- Cement bond logs (CBL/VDL) required
- Temperature logs for verification
- Pressure testing documentation

3.3 Abandonment Categories

Category A - Permanent Abandonment:
- Full isolation of all zones
- Removal of production facilities
- Site restoration

Category B - Temporary Abandonment:
- Preservation of wellbore integrity
- Monitoring plan required
- Maximum duration: 12 months (renewable)

3.4 Documentation Requirements

The following documentation shall be maintained:
- Abandonment design basis
- Execution records
- Verification results
- As-built drawings
- Regulatory submissions

4. QUALITY ASSURANCE

4.1 Design Review
All abandonment designs shall be reviewed by qualified personnel independent from the design team.

4.2 Execution Oversight
Field operations shall be supervised by competent personnel with appropriate authority to stop operations if quality is compromised.

4.3 Verification Testing
All barriers shall be tested and verified prior to final acceptance.

5. REGULATORY COMPLIANCE

Operators shall comply with applicable regulations in all jurisdictions where operations are conducted.

6. REFERENCES

- API RP 90: Annular Casing Pressure Management
- ISO 16530-1: Well Integrity Management - Part 1
- NORSOK D-010: Well integrity in drilling and well operations

International Association of Oil & Gas Producers
London, UK
www.iogp.org
''')
pdf2.output('storage/regulations/iogp_485_well_integrity.pdf')
print('PDF 2 creado: IOGP 485')

# PDF 3: Procedimiento Operativo
pdf3 = FPDF()
pdf3.add_page()
pdf3.set_font('Arial', 'B', 16)
pdf3.cell(0, 10, 'ETIAM S.A.', 0, 1, 'C')
pdf3.cell(0, 10, 'Procedimiento Operativo', 0, 1, 'C')
pdf3.set_font('Arial', 'B', 14)
pdf3.cell(0, 10, 'Abandono de Pozos Petroleros', 0, 1, 'C')
pdf3.set_font('Arial', '', 12)
pdf3.multi_cell(0, 10, '''
Codigo: PO-ABP-001
Version: 2.1
Fecha: Febrero 2025
Aprobado por: Directorio Tecnico

1. OBJETIVO

Establecer el procedimiento estandar para la ejecucion del abandono de pozos petroleros, asegurando el cumplimiento de normativas aplicables y la proteccion del medio ambiente.

2. ALCANCE

Este procedimiento aplica a todos los pozos propiedad de ETIAM S.A. ubicados en la Cuenca Neuquina y Cuenca Austral.

3. DEFINICIONES

Pozo: Perforacion en el subsuelo para extraccion de hidrocarburos.
Abandono: Conjunto de operaciones para dejar el pozo inactivo de forma segura.
DTM: Dato de terminacion mecanica.
CBL: Cement Bond Log (Registro de adhesion del cemento).
VDL: Variable Density Log (Registro de densidad variable).

4. RESPONSABILIDADES

4.1 Gerente de Operaciones
- Aprobacion final del programa de abandono
- Autorizacion de overrides regulatorios
- Seguimiento de indicadores de desempeno

4.2 Ingeniero de Campo
- Elaboracion del programa de abandono
- Supervision de operaciones en campo
- Verificacion de cumplimiento tecnico

4.3 Supervisor de Seguridad (HSE)
- Verificacion de cumplimiento normativo HSE
- Autorizacion de trabajo en campo
- Gestion de incidentes

4.4 Administrativo de Contratos
- Gestion contractual con clientes
- Certificaciones y facturacion
- Seguimiento de cobranzas

5. PROCEDIMIENTO

5.1 Fase 1: Planificacion (Semanas 1-2)

Actividades:
1. Recopilacion de historia del pozo
2. Evaluacion de estado mecanico actual
3. Diseno de abandono (ingenieria)
4. Presupuesto y contratacion
5. Presentacion ante entes regulatorios

Entregables:
- Programa de abandono aprobado
- Permisos regulatorios vigentes
- Contrato firmado con cliente

5.2 Fase 2: Movilizacion (Semana 3)

Actividades:
1. Movilizacion de equipos y personal
2. Preparacion del location
3. Verificacion HSE previa
4. Pruebas de equipos

Checklist de verificacion:
- Equipos principales (workover, pulling)
- Equipos auxiliares (cisternas, cementadoras)
- Personal certificado
- Permisos de trabajo
- Extintores y equipos de emergencia
- Comunicaciones establecidas

5.3 Fase 3: Ejecucion (Semanas 4-8)

5.3.1 Preparacion del pozo
- Instalacion de BOP
- Pruebas de presion
- Instalacion de arreglo de tuberia

5.3.2 Remocion de produccion
- Extraccion de TLs
- Limpieza del pozo
- Evaluacion de condiciones

5.3.3 Cementacion
- Diseno de slurry
- Pruebas de laboratorio
- Ejecucion de cementacion
- Registros de verificacion (CBL/VDL)

5.3.4 Colocacion de tapones
- Tapones mecanicos en profundidades estrategicas
- Pruebas de estanqueidad
- Registros de verificacion

5.3.5 Corte y extraccion
- Corte de tuberia a profundidad de abandono
- Extraccion de seccion superficial
- Sellado final

5.4 Fase 4: Cierre Tecnico (Semanas 9-10)

Actividades:
1. Verificacion final de integridad
2. Elaboracion de acta de abandono
3. Firmas digitales de responsables
4. Presentacion de dossier ante regulator

Documentacion requerida:
- Acta de abandono firmada
- Registros de pozo (CBL/VDL)
- Registros de temperatura
- Pruebas de presion
- Fotografias de evidencia
- Hash SHA256 de documentacion

5.5 Fase 5: Restauracion (Semanas 11-12)

Actividades:
1. Desmantelamiento de instalaciones
2. Restauracion del area
3. Revegetacion (si aplica)
4. Monitoreo post-abandono

6. CONTROLES DE CALIDAD

6.1 Gates de Verificacion

Gate 1: DTM Confirmado
- Ubicacion verificada via GPS
- Acceso autorizado

Gate 2: Personal Validado
- Certificaciones HSE vigentes
- Asignacion de funciones

Gate 3: Equipos Verificados
- Sin fallas criticas
- Certificaciones al dia

Gate 4: Stock Suficiente
- Materiales disponibles
- Proveedores confirmados

Gate 5: Permisos Validos
- Todos los permisos vigentes
- Sin vencimientos proximos

Gate 6: Clima Apto
- Condiciones dentro de parametros
- Alertas meteorologicas monitoreadas

Gate 7: Cementacion Validada
- Diseno aprobado
- Parametros dentro de tolerancias

6.2 Auditoria

Todas las operaciones son registradas en el sistema de auditoria con:
- Timestamp
- Usuario responsable
- Hash de integridad
- Trazabilidad completa

7. CRITERIOS DE ACEPTACION

El abandono se considera exitoso cuando:
- Todas las zonas permeables estan aisladas
- Tapones de cemento verificados mediante CBL/VDL
- Pruebas de presion satisfactorias
- Documentacion completa y firmada
- Aprobacion del regulador competente
- Hash de integridad generado

8. GLOSARIO

BOP: Blowout Preventer (Preventor de brotes)
CBL: Cement Bond Log (Registro de adhesion del cemento)
DTM: Dato de Terminacion Mecanica
HSE: Health, Safety and Environment (Salud, Seguridad y Ambiente)
SLB: Slurry (Lechada de cemento)
TL: Tubing Line (Tuberia de produccion)
VDL: Variable Density Log (Registro de densidad variable)
WOB: Weight on Bit (Peso sobre la broca)

9. REFERENCIAS

- SEC Resolucion 05/2023 - Abandono de pozos
- SEC Resolucion 12/2024 - Integridad de pozos
- IOGP Report 485 - Well Integrity Management
- ISO 16530-1 - Well Integrity Management

10. HISTORIAL DE REVISIONES

Version 2.1 - Febrero 2025
- Actualizacion de procedimientos de cementacion
- Incorporacion de gates de verificacion
- Mejoras en trazabilidad blockchain

Version 2.0 - Agosto 2024
- Reestructuracion completa del documento
- Incorporacion de requisitos IOGP

Version 1.0 - Enero 2023
- Emision inicial

ETIAM S.A.
Proyectos y Abandono de Pozos
www.etiam.com.ar
''')
pdf3.output('storage/regulations/procedimiento_operativo_abandono.pdf')
print('PDF 3 creado: Procedimiento Operativo')
print('Todos los PDFs creados exitosamente')

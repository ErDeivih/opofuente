"""Borrador del catálogo de materias de I.6 (La sociedad de la información, identidad y firma
electrónica, el DNI electrónico y la Agenda Digital).

I.6 no es **una** norma: mezcla la LSSI, la propiedad intelectual del software, la Administración
electrónica, la factura electrónica, la Ley 59/2003, el Reglamento europeo eIDAS, la Ley 6/2020, el
DNIe y los planes de agenda digital. Por eso se organiza **por materias** y, dentro de cada bloque
normativo, siguiendo la estructura de esa ley (los artículos que se citan en los enunciados).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

MATERIAS: tuple[Materia, ...] = (
    # --- I.6.1 La sociedad de la información ---------------------------------------------------
    Materia(
        key="lssi",
        epigraph_code="I.6.1",
        title="LSSI: servicios de la sociedad de la información y comercio electrónico",
        resumen=(
            "La Ley 34/2002: qué es un servicio de la sociedad de la información, las obligaciones "
            "de información del prestador, la contratación electrónica, la responsabilidad de los "
            "intermediarios, la tarificación adicional y el régimen de infracciones y sanciones."
        ),
        patrones=(
            r"ley 34 2002",
            r"\blssi\b",
            r"sociedad de la informacion",
            r"comercio electronico",
            r"prestador(es)? de servicios",
            r"tarificacion adicional",
            r"infracciones? (leves|graves|muy graves)",
            r"contratacion electronica",
            r"nombre de dominio",
            r"comunicaciones? comerciales? electronic",
        ),
        patrones_debiles=(r"\blssi\b", r"prestador", r"infraccion"),
        prioridad=10,
    ),
    Materia(
        key="propiedad-intelectual",
        epigraph_code="I.6.1",
        title="Propiedad intelectual: programas de ordenador, bases de datos y licencias",
        resumen=(
            "Los derechos de autor sobre el software (título VII del texto refundido de la Ley de "
            "Propiedad Intelectual), el derecho «sui generis» sobre las bases de datos, las "
            "licencias de software libre (GPL) y la titularidad de la obra."
        ),
        patrones=(
            r"propiedad intelectual",
            r"programas? de ordenador",
            r"software libre",
            r"\bgpl\b",
            r"licencias? (de )?(software|libre|publica)",
            r"sui generis",
            r"bases? de datos",
            r"codigo fuente",
            r"derechos? de autor",
            r"obra (colectiva|derivada|originaria)",
        ),
        patrones_debiles=(r"software", r"licencia", r"autor"),
        prioridad=11,
    ),
    Materia(
        key="administracion-electronica",
        epigraph_code="I.6.1",
        title="Administración electrónica: documentos, copias y reutilización",
        resumen=(
            "El documento electrónico y su valor probatorio, las copias electrónicas, la "
            "ventanilla "
            "única y los puntos de acceso, el Esquema Nacional de Interoperabilidad, la "
            "reutilización "
            "de los documentos y la accesibilidad."
        ),
        patrones=(
            r"administracion(es)? (publicas?|electronica)",
            r"ventanilla unica",
            r"puntos? de acceso",
            r"documentos? electronicos?",
            r"valor probatorio",
            r"copias? electronicas?",
            r"reutilizacion",
            r"datos abiertos",
            r"2019 1024",
            r"informacion del sector publico",
            r"representacion.*acredit",
            r"\beni\b",
            r"esquema nacional",
            r"sede electronica",
            r"registro electronic",
            r"expediente electronic",
            r"accesibilidad",
            r"certificados? de (firma )?empleado publico",
        ),
        patrones_debiles=(r"documento", r"administracion", r"electronic"),
        prioridad=12,
    ),
    Materia(
        key="datos-personales",
        epigraph_code="I.6.1",
        title="Protección de datos personales y derechos digitales",
        resumen=(
            "La Ley Orgánica 3/2018 (LOPDGDD) y la garantía de los derechos digitales: qué "
            "protege, "
            "los derechos de las personas y el papel de la Agencia Española de Protección de Datos."
        ),
        patrones=(
            r"lopdgdd",
            r"proteccion de datos",
            r"datos personales",
            r"derechos digitales",
            r"agencia espanola de proteccion de datos",
            r"consentimiento",
            r"reglamento general de proteccion de datos",
            r"\brgpd\b",
        ),
        patrones_debiles=(r"datos", r"personales"),
        prioridad=15,
    ),
    Materia(
        key="factura-electronica",
        epigraph_code="I.6.1",
        title="Factura electrónica y medidas de impulso de la sociedad de la información",
        resumen=(
            "La factura electrónica y su firma (Ley 56/2007, de medidas de impulso de la sociedad "
            "de "
            "la información), los requisitos de seguridad de la factura y los planes de impulso."
        ),
        patrones=(
            r"factura electr",
            r"ley 56 2007",
            r"medidas de impulso",
            r"facturacion electr",
            r"punto general de entrada de facturas",
            r"\bface\b",
        ),
        patrones_debiles=(r"factura",),
        prioridad=13,
    ),
    Materia(
        key="web-social",
        epigraph_code="I.6.1",
        title="Web 2.0, software social y herramientas de aprendizaje",
        resumen=(
            "La web 2.0 y sus servicios (folksonomías, etiquetado social, redes), el software "
            "social "
            "y las herramientas de teleaprendizaje y de formación de usuarios, con su licencia."
        ),
        patrones=(
            r"web 2 0",
            r"folksonom",
            r"software social",
            r"teleaprendizaje",
            r"\bmoodle\b",
            r"\bwiki",
            r"redes? sociales",
            r"\brss\b",
            r"\bblog",
            r"etiquetado social",
            r"comunidades? virtuales?",
        ),
        patrones_debiles=(r"social", r"formacion"),
        prioridad=14,
    ),
    # --- I.6.2 Identidad y firma electrónica ---------------------------------------------------
    Materia(
        key="ley-59-2003",
        epigraph_code="I.6.2",
        title="Ley 59/2003, de firma electrónica",
        resumen=(
            "La firma electrónica y sus clases, los prestadores de servicios de certificación, sus "
            "obligaciones y su régimen de inspección y sanción, y el documento nacional de "
            "identidad "
            "electrónico como norma habilitante."
        ),
        patrones=(
            r"ley 59 2003",
            r"prestador(es)? de servicios? de certificacion",
            r"\bpsc\b",
            r"actuacion inspectora",
            r"documento nacional de identidad electronic",
            r"firma electronica (avanzada|reconocida)",
        ),
        patrones_debiles=(r"firma electronica", r"prestador"),
        prioridad=20,
    ),
    Materia(
        key="eidas",
        epigraph_code="I.6.2",
        title="Reglamento eIDAS y Ley 6/2020: servicios electrónicos de confianza",
        resumen=(
            "El Reglamento (UE) 910/2014 y la Ley 6/2020: los servicios electrónicos de confianza "
            "(sello de tiempo, sello electrónico, entrega certificada, autenticación de sitios "
            "web), "
            "los prestadores cualificados y las normas europeas de estandarización."
        ),
        patrones=(
            r"\beidas\b",
            r"910 2014",
            r"ley 6 2020",
            r"servicios? electronicos? de confianza",
            r"sello cualificado",
            r"sello de tiempo",
            r"prestadores? cualificados?",
            r"\betsi\b",
            r"normas europeas",
            r"entrega electronica certificada",
            r"autenticacion de sitios web",
            r"espacio economico europeo",
            r"organismos? de supervision",
            r"supervision de los prestadores",
            r"2024 1183",
            r"cartera(s)? europea(s)? de identidad",
            r"articulo 26",
            r"actos de ejecucion",
            r"cooperacion entre estados",
            r"interoperabilidad de los sistemas",
            r"estados miembros cooperar",
            r"parte usuaria",
            r"proceso de registro",
            r"cartera(s)? (europea|de identidad)",
        ),
        patrones_debiles=(r"confianza", r"reglamento", r"cualificad"),
        prioridad=21,
    ),
    Materia(
        key="certificados",
        epigraph_code="I.6.2",
        title="Certificados electrónicos: clases, revocación y validación",
        resumen=(
            "El certificado electrónico: su contenido, las clases, los datos que comprueba la "
            "autoridad de certificación, la revocación y la suspensión, las listas de revocación, "
            "la "
            "validación y el proyecto CERES de la FNMT."
        ),
        patrones=(
            r"certificados? (electronicos?|digitales?|de (clase|firma|empleado))",
            r"autoridad(es)? de certificacion",
            r"autoridad(es)? de validacion",
            r"clase [123]\b",
            r"revocacion",
            r"\bcrl\b",
            r"\bocsp\b",
            r"\bceres\b",
            r"\bfnmt\b",
            r"fabrica nacional de moneda",
            r"politica de certificacion",
            r"datos de (creacion|verificacion) de firma",
        ),
        patrones_debiles=(r"certificado", r"certificad"),
        prioridad=22,
    ),
    Materia(
        key="firma-y-sello",
        epigraph_code="I.6.2",
        title="Firma y sello electrónicos: tipos, efectos y validación",
        resumen=(
            "Los tipos de firma electrónica y del sello, sus efectos jurídicos y probatorios, la "
            "validación de la firma y del sello, los elementos básicos y las condiciones mínimas "
            "de "
            "validación."
        ),
        patrones=(
            r"firma electronica",
            r"sello electronico",
            r"efectos? juridicos",
            r"no repudio",
            r"documento (publico|privado)",
            r"validacion de (la )?(firma|sello)",
            r"condiciones minimas",
        ),
        patrones_debiles=(r"firma", r"sello", r"validacion"),
        prioridad=23,
    ),
    Materia(
        key="identificacion-clave",
        epigraph_code="I.6.2",
        title="Sistemas de identificación electrónica (Cl@ve) y firma del ciudadano",
        resumen=(
            "Los sistemas de identificación y autenticación de las Administraciones Públicas "
            "(Cl@ve, con claves concertadas, certificado y DNIe) y la firma electrónica del "
            "ciudadano ante la Administración."
        ),
        patrones=(
            r"cl@ve",
            r"clave permanente",
            r"clave concertada",
            r"identificacion( )?(y autenticacion|electronica)",
            r"sistema( )?comun de identificacion",
            r"autenticacion de los ciudadanos",
        ),
        patrones_debiles=(r"identificacion", r"autenticacion"),
        prioridad=24,
    ),
    # --- I.6.3 El DNI electrónico ---------------------------------------------------------------
    Materia(
        key="dnie",
        epigraph_code="I.6.3",
        title="El DNI electrónico: certificados, PIN y validez",
        resumen=(
            "El documento nacional de identidad electrónico: sus certificados, la verificación de "
            "usuario y el PIN (intentos y bloqueo), los períodos de validez del documento según la "
            "edad del titular, sus usos y las diferencias entre versiones."
        ),
        patrones=(
            r"\bdnie?\b",
            r"documento nacional de identidad",
            r"\bpin\b",
            r"verificacion de usuario",
            r"bloqueo",
            r"periodo de validez",
            r"dn",
            r"signar digitalment",
        ),
        patrones_debiles=(r"validez", r"certificado"),
        prioridad=30,
    ),
    # --- I.6.4 La Agenda Digital para España ----------------------------------------------------
    Materia(
        key="agenda-digital",
        epigraph_code="I.6.4",
        title="Agenda Digital para España, planes y órganos asesores",
        resumen=(
            "La Agenda Digital para España y los planes que la desarrollan (Plan Conecta, plan de "
            "acceso a Internet), sus objetivos y los órganos que asesoran al Gobierno en materia "
            "de "
            "telecomunicaciones y sociedad de la información."
        ),
        patrones=(
            r"agenda digital",
            r"plan conecta",
            r"plan de acceso a internet",
            r"estrategia (digital|espanola)",
            r"banda ancha",
            r"organo asesor",
            r"telecomunicaciones",
            r"consejo asesor",
            r"unidad responsable de informacion",
        ),
        patrones_debiles=(r"plan", r"digital", r"internet"),
        prioridad=40,
    ),
)

#: El orden en que se **enseña** el índice de este tema: el de sus epígrafes oficiales y,
#: dentro de cada uno, el de la ley que se estudia. Es una decisión aparte del orden de
#: reparto (`prioridad`), que mira primero lo particular.
ORDEN: tuple[str, ...] = (
    "lssi",
    "propiedad-intelectual",
    "administracion-electronica",
    "datos-personales",
    "factura-electronica",
    "web-social",
    "ley-59-2003",
    "eidas",
    "certificados",
    "firma-y-sello",
    "identificacion-clave",
    "dnie",
    "agenda-digital",
)

__all__ = ["MATERIAS", "ORDEN"]

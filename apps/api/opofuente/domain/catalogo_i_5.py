"""El catálogo de materias de I.5 (igualdad, violencia de género, LGTBI, discapacidad y
dependencia).

I.5 es un tema **normativo**, así que su índice sigue la estructura de las normas que lo componen. Y
son cinco, cada una con su propio régimen:

- la **Ley Orgánica 3/2007**, para la igualdad efectiva de mujeres y hombres, que es la que manda en
  el tema (tres cuartas partes del banco la citan): los principios, los criterios generales de
  actuación, la transversalidad, los planes de igualdad, la igualdad en el empleo y la tutela;
- la **Ley Orgánica 1/2004**, de medidas de protección integral contra la violencia de género: el
  concepto y el ámbito, los derechos de las víctimas, las medidas en la educación y la publicidad y
  la tutela institucional;
- la **Ley 4/2023**, para la igualdad real y efectiva de las personas trans y la garantía de los
  derechos de las personas LGTBI: los conceptos, la igualdad de trato, la rectificación registral de
  la mención del sexo y las medidas de las administraciones públicas;
- el **Texto Refundido de la Ley General de derechos de las personas con discapacidad y de su
  inclusión social** (Real Decreto Legislativo 1/2013): las definiciones, la accesibilidad
  universal,
  la igualdad de oportunidades y la acción protectora;
- la **Ley 39/2006**, de promoción de la autonomía personal y atención a las personas en situación
de
  dependencia: los grados y niveles de dependencia, la valoración, el catálogo de servicios y
  prestaciones y su financiación.

Los tres epígrafes oficiales del tema son las políticas de igualdad y contra la violencia de género
(I.5.1), las políticas de igualdad de trato y no discriminación de las personas LGTBI (I.5.2) y la
discapacidad y la dependencia (I.5.3), y este catálogo los abre en catorce apartados:

- I.5.1, en **siete**: los principios y los criterios generales de actuación, los **planes de
  igualdad** y las políticas, la igualdad en el **empleo y la conciliación**, la **tutela** y las
  garantías, el **concepto y el ámbito** de la violencia de género, los **derechos de las víctimas**
  y la **tutela institucional**;
- I.5.2, en **tres**: los derechos y los conceptos, la **rectificación registral** de la mención
  relativa al sexo y las medidas públicas y el régimen sancionador;
- I.5.3, en **cuatro**: el concepto y los derechos de las personas con discapacidad, el empleo, la
  educación y la protección social, el **concepto, los grados y la valoración** de la dependencia y
  los **servicios y las prestaciones** del sistema.

Cuatro decisiones de redacción de los patrones, dichas donde se leen:

- las citas de una norma van **con su número y con su sigla** (`ley organica 3 2007`, `\blo 3
2007\b`,
  `ley 39 2006`, `1 2013`), porque el texto normalizado deja el número separado por espacios y
  porque el material cita unas veces por número y otras por nombre;
- **«igualdad» a secas no es un patrón propio de nadie**: aparece en las tres normas y en casi todos
  los enunciados del tema, así que vive en los `patrones_debiles` del apartado de principios. Lo
  particular gana a lo general, que es la regla de todos los catálogos del proyecto;
- la **violencia de género** y la **violencia doméstica** se separan por lo que el enunciado nombra
  (la Ley Orgánica 1/2004 es la de la violencia de género; la doméstica no está en su ámbito), y el
  apartado de derechos recoge las ayudas, la asistencia y los derechos laborales y funcionariales
  que
  el banco pregunta una y otra vez;
- la distinción entre **`dependencia-concepto-y-grados`** (qué es, cómo se valora y en qué grado) y
  **`dependencia-servicios-y-prestaciones`** (qué se recibe y quién lo paga) es la del propio título
  de la Ley 39/2006: el banco pregunta por las dos por separado y mezclarlas obligaría a estudiar el
  baremo dentro del catálogo de prestaciones.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las citas de las normas del tema, como las deja el texto normalizado («ley organica 3 2007»).
_LO_3_2007 = r"ley organica 3 2007|\blo 3 2007\b|\b3 2007\b|ley 3 2007|igualdad efectiva de mujeres"
_LO_1_2004 = (
    r"ley organica 1 2004|\blo 1 2004\b|\b1 2004\b|ley 1 2004|"
    r"violencia de genero|violencia sobre la mujer"
)
_LEY_4_2023 = (
    r"ley 4 2023|\b4 2023\b|igualdad real y efectiva de las personas trans|"
    r"personas? trans|personas? lgtbi|\blgtbi\b|\blgtb\b"
)
_RDL_1_2013 = (
    r"real decreto legislativo 1 2013|\brdl 1 2013\b|\b1 2013\b|"
    r"ley general de derechos de las personas con discapacidad|"
    r"personas? con discapacidad|discapacidad"
)
_LEY_39_2006 = (
    r"ley 39 2006|\b39 2006\b|promocion de la autonomia personal|"
    r"situacion de dependencia|\bdependencia\b"
)

MATERIAS: tuple[Materia, ...] = (
    # --- I.5.1 Políticas de igualdad y contra la violencia de género -----------------------------
    Materia(
        key="igualdad-principios-y-criterios",
        epigraph_code="I.5.1",
        title="Los principios de igualdad y los criterios de actuación de los poderes públicos",
        resumen=(
            "El marco de la igualdad efectiva de mujeres y hombres: el objeto y el ámbito de la "
            "Ley "
            "Orgánica 3/2007, el principio de igualdad de trato y de oportunidades, la igualdad "
            "como "
            "principio informador del ordenamiento y la transversalidad, los criterios generales "
            "de "
            "actuación de los poderes públicos, la composición equilibrada y la presencia "
            "equilibrada "
            "en las listas y en los órganos, la igualdad en el acceso a los bienes y servicios y "
            "en "
            "la contratación, la dimensión de género en las políticas públicas y los informes de "
            "impacto de género."
        ),
        patrones=(
            _LO_3_2007,
            r"principio(s)? de igualdad|igualdad (de trato|efectiva|real|entre (mujeres y hombres|"
            r"hombres y mujeres))",
            r"criterios? generales? de actuacion|poderes publicos.*(igualdad|actuacion)",
            r"transversalidad|perspectiva de genero|enfoque de genero|mainstreaming",
            r"composicion equilibrada|presencia equilibrada|presencia de mujeres",
            r"discriminacion (por razon de sexo|directa|indirecta)|discriminacion multiple",
            r"igualdad de oportunidades (entre )?(mujeres|hombres)",
            r"informe(s)? de impacto de genero|evaluacion previa del impacto",
            r"acciones? positivas?|medidas de accion positiva",
        ),
        patrones_debiles=(r"igualdad", r"mujeres", r"hombres", r"genero", r"sexo"),
        prioridad=60,
    ),
    Materia(
        key="igualdad-planes-y-politicas",
        epigraph_code="I.5.1",
        title="Los planes de igualdad y las políticas de igualdad",
        resumen=(
            "La planificación de la igualdad: los planes de igualdad de las empresas y su "
            "contenido, "
            "el diagnóstico de situación, el registro y el depósito de los planes, los planes de "
            "igualdad de la Administración General del Estado, los planes estratégicos de igualdad "
            "de "
            "oportunidades, los planes integrales y los municipales, la Conferencia Mundial de la "
            "mujer y su plataforma de acción, y las políticas de igualdad que el material pregunta."
        ),
        patrones=(
            r"plan(es)? (de|para la) igualdad|plan de igualdad de oportunidades|"
            r"plan integral de igualdad|plan estrategico de igualdad",
            r"plan de igualdad (en la administracion|de la age)|planes? municipales?",
            r"conferencia mundial (para la mujer|de la mujer)|plataforma de accion|pekin",
            r"diagnostico de (situacion|la situacion)|registro de planes de igualdad",
            r"politicas? de igualdad|politica de igualdad",
            r"(iv|iii|ii|i) plan (integral|de igualdad|estrategico)",
            r"medidas? (para la|de) (igualdad|promocion de la igualdad)",
        ),
        patrones_debiles=(r"plan", r"politica"),
        prioridad=41,
    ),
    Materia(
        key="igualdad-empleo-y-conciliacion",
        epigraph_code="I.5.1",
        title="La igualdad en el empleo, la conciliación y el acoso",
        resumen=(
            "La igualdad en el trabajo y en la vida personal: el derecho al trabajo en igualdad de "
            "oportunidades, la clasificación profesional y las retribuciones, la promoción y la "
            "formación, la igualdad en el empleo público y en el acceso a la función pública, la "
            "conciliación de la vida personal, familiar y laboral y la corresponsabilidad, los "
            "permisos y las excedencias, los derechos de las trabajadoras embarazadas, la "
            "protección "
            "frente al acoso sexual y al acoso por razón de sexo y sus protocolos, y el deber de "
            "negociación colectiva."
        ),
        patrones=(
            r"conciliacion|corresponsabilidad|vida personal, familiar y laboral",
            r"acoso sexual|acoso por razon de sexo|protocolo(s)? (contra el acoso|de acoso)|"
            r"acoso laboral|hostigamiento",
            r"empleo publico|funcion publica.*(igualdad|mujer)|acceso a la funcion publica",
            r"excedencia|permiso(s)? (por|de) (maternidad|paternidad|nacimiento|lactancia)",
            r"retribucion(es)?|clasificacion profesional|promocion profesional",
            r"negociacion colectiva|convenio colectivo|plan de igualdad en la empresa",
            r"embarazada|embarazo|riesgo durante la lactancia",
            r"derecho al trabajo|mercado de trabajo|insercion laboral.*mujer",
        ),
        patrones_debiles=(r"empleo", r"trabajo", r"conciliacion", r"acoso"),
        prioridad=42,
    ),
    Materia(
        key="igualdad-tutela-y-garantias",
        epigraph_code="I.5.1",
        title="La tutela de la igualdad y los organismos de igualdad",
        resumen=(
            "Cómo se exige la igualdad: la tutela judicial y administrativa, la legitimación y la "
            "inversión de la carga de la prueba, la indemnidad frente a represalias, la reparación "
            "del daño, los organismos de igualdad y las unidades de igualdad, la Comisión "
            "Interministerial de Igualdad, los órganos de coordinación de las políticas de "
            "igualdad, "
            "la tutela institucional y el régimen de infracciones y sanciones de la Ley Orgánica "
            "3/2007."
        ),
        patrones=(
            r"tutela (judicial|administrativa|efectiva)|reclamacion|demanda|recurso",
            r"(inversion de )?la carga de la prueba|indicios de discriminacion",
            r"indemnidad|represalia|represalias",
            r"unidad(es)? de igualdad|organismo(s)? de igualdad|"
            r"comision interministerial de igualdad",
            r"infraccion(es)? y sancion(es)?|regimen sancionador|sancion(es)? (por|de) "
            r"discriminacion",
            r"legitimacion|legitimad[oa]s? para|esta legitimad",
            r"reparacion (del dano|de la victima)|indemnizacion",
        ),
        patrones_debiles=(r"tutela", r"sancion", r"organismo"),
        prioridad=43,
    ),
    Materia(
        key="violencia-de-genero-concepto-y-ambito",
        epigraph_code="I.5.1",
        title="La violencia de género: concepto, ámbito y medidas de prevención",
        resumen=(
            "Qué es la violencia de género y qué hace el Estado frente a ella: el objeto y el "
            "ámbito "
            "de la Ley Orgánica 1/2004, el concepto de violencia de género y los tipos que "
            "comprende, "
            "los principios rectores, el derecho a la información, la sensibilización y la "
            "prevención, las medidas en el ámbito educativo (la escolarización, el Consejo Escolar "
            "y "
            "la formación del profesorado), las medidas en la publicidad y en los medios de "
            "comunicación, y las medidas de carácter social y económico."
        ),
        patrones=(
            _LO_1_2004,
            r"violencia (de genero|domestica|sobre la mujer)|victima(s)? de violencia",
            r"principios? rectores|objeto y ambito|ambito de aplicacion",
            r"medidas? (de )?(prevencion|sensibilizacion)|sensibilizacion (social|ciudadana)",
            r"ambito educativo|consejo escolar|escolarizacion|profesorado|sistema educativo",
            r"publicidad|medios de comunicacion|contenidos? (de|en los) medios",
            r"delegacion del gobierno( para la violencia de genero)?|observatorio",
            r"acreditacion de (la situacion|las situaciones) de violencia",
        ),
        patrones_debiles=(r"violencia", r"victima", r"genero"),
        prioridad=44,
    ),
    Materia(
        key="violencia-de-genero-derechos-de-las-victimas",
        epigraph_code="I.5.1",
        title="Los derechos de las víctimas de violencia de género",
        resumen=(
            "Lo que la víctima tiene derecho a recibir: la información y la asistencia social "
            "integral, la asistencia jurídica gratuita y el turno de oficio, los derechos "
            "laborales y "
            "de la función pública (la movilidad, la excedencia, la reducción de jornada, la "
            "suspensión del contrato y el traslado), las ayudas sociales y económicas, la renta "
            "activa de inserción y las ayudas de pago único, la acreditación de la situación de "
            "violencia, los derechos en materia de salud y de Seguridad Social, y la protección de "
            "los menores y de las personas especialmente vulnerables."
        ),
        patrones=(
            r"derecho(s)? de las victimas|derechos? (laborales?|funcionariales?|economicos?|"
            r"sociales?) de las (mujeres )?victimas",
            r"asistencia (social )?integral|asistencia juridica (gratuita|a las victimas)|"
            r"turno de oficio",
            r"ayudas? (sociales?|economicas?|de pago unico)|renta activa de insercion|"
            r"ayuda economica",
            r"funcionaria victima|movilidad (geografica|de la funcionaria)|"
            r"reduccion de jornada|suspension (del contrato|de la relacion laboral)|traslado",
            r"acreditacion|acreditar (la situacion|las situaciones)",
            r"asistencia sanitaria|derechos en materia de salud|seguridad social",
            r"menores?|hijos? (de las victimas|menores)|patria potestad|"
            r"personas especialmente vulnerables",
        ),
        patrones_debiles=(r"victima", r"ayuda", r"asistencia"),
        prioridad=45,
    ),
    Materia(
        key="violencia-de-genero-tutela-institucional",
        epigraph_code="I.5.1",
        title="La tutela institucional y las medidas penales de la violencia de género",
        resumen=(
            "Los órganos y los instrumentos que protegen: la Delegación del Gobierno contra la "
            "Violencia de Género, el Observatorio Estatal de Violencia sobre la Mujer, la Fiscalía "
            "especial, los juzgados de violencia sobre la mujer y las secciones de las Fuerzas y "
            "Cuerpos de Seguridad, las medidas judiciales y penales y las órdenes de protección, "
            "las "
            "medidas cautelares y de aseguramiento, las pulseras y el control telemático, los "
            "servicios de atención y los centros de acogida, y el régimen de infracciones y "
            "sanciones."
        ),
        patrones=(
            r"delegacion (del gobierno|especial)( para la violencia)?|"
            r"delegad[oa] del gobierno contra la violencia",
            r"observatorio( estatal)? (de )?(la )?violencia",
            r"fiscal(ia)? (especial|contra la violencia)|fiscalia de violencia",
            r"juzgado(s)? de (violencia|lo penal)|juez de violencia|orden de proteccion",
            r"medidas (penales|judiciales|cautelares)|prision|alejamiento|"
            r"control telematico|pulsera",
            r"fuerzas y cuerpos de seguridad|policia|guardia civil",
            r"centro(s)? de acogida|servicios? de atencion|dispositivo de emergencia|016",
            r"tutela institucional",
        ),
        patrones_debiles=(r"juzgado", r"fiscalia", r"orden de proteccion", r"observatorio"),
        prioridad=46,
    ),
    # --- I.5.2 Igualdad de trato y no discriminación de las personas LGTBI -----------------------
    Materia(
        key="lgtbi-derechos-y-conceptos",
        epigraph_code="I.5.2",
        title="Los derechos de las personas LGTBI y sus conceptos",
        resumen=(
            "El derecho a la igualdad real y efectiva de las personas LGTBI: el objeto y el ámbito "
            "de "
            "la Ley 4/2023, los conceptos de identidad sexual, expresión de género, orientación e "
            "identidad sexual y características sexuales, la intersexualidad, el derecho a la "
            "igualdad de trato y no discriminación y su prohibición, la prohibición de las "
            "prácticas "
            "de modificación de la orientación o la identidad sexual, y las medidas en educación, "
            "sanidad, empleo, cultura, familia, menores y personas mayores."
        ),
        patrones=(
            _LEY_4_2023,
            r"orientacion (sexual|e identidad)|identidad sexual|expresion de genero|"
            r"caracteristicas sexuales|intersexual",
            r"(igualdad de trato y )?no discriminacion.*(lgtbi|personas trans)",
            r"igualdad real y efectiva|ley 4 2023|para la igualdad real",
            r"terapias? de (conversion|aversion)|practicas de modificacion",
            r"personas? trans|transexual|transgenero|no binari",
            r"homosexual|lesbiana|bisexual|gay|intersexualidad",
        ),
        patrones_debiles=(r"lgtbi", r"trans", r"orientacion sexual", r"identidad"),
        prioridad=47,
    ),
    Materia(
        key="lgtbi-rectificacion-registral",
        epigraph_code="I.5.2",
        title="La rectificación registral de la mención relativa al sexo",
        resumen=(
            "El cambio de la mención registral del sexo y del nombre: la legitimación y la "
            "capacidad "
            "para solicitarlo, la autoridad competente para la tramitación del procedimiento, la "
            "documentación que hay que aportar, el procedimiento y sus plazos, la ausencia de "
            "requisitos médicos (el diagnóstico de disforia y los tratamientos), la reversibilidad "
            "de la rectificación y sus efectos en el Registro Civil y en los documentos."
        ),
        patrones=(
            r"rectificacion registral|mencion (registral |relativa al )?(del )?sexo|"
            r"cambio de (nombre|sexo) en el registro",
            r"registro civil|encargad[oa] del registro civil|"
            r"autoridad competente para la tramitacion",
            r"disforia|informe medico|tratamiento medico|requisitos medicos",
            r"reversibilidad|volver a solicitar|nueva rectificacion",
            r"nombre (propio|elegido)|cambio de la mencion",
        ),
        patrones_debiles=(r"rectificacion", r"registral", r"registro"),
        prioridad=48,
    ),
    Materia(
        key="lgtbi-medidas-publicas-y-sanciones",
        epigraph_code="I.5.2",
        title="Las medidas de las administraciones públicas y el régimen sancionador LGTBI",
        resumen=(
            "Lo que hacen las administraciones y lo que pasa si no lo hacen: las medidas y los "
            "servicios especializados (los equipos multidisciplinares de atención integral), la "
            "atención a la discriminación múltiple e interseccional y en el medio rural, las "
            "políticas públicas y los planes, la formación del personal, la protección de los "
            "menores "
            "en la adopción y el acogimiento, la igualdad en el acceso a bienes y servicios, y el "
            "régimen de infracciones y sanciones de la Ley 4/2023."
        ),
        patrones=(
            r"servicios? especializados?|equipos? multidisciplinares|"
            r"atencion integral a (las personas )?(lgtbi|trans)",
            r"discriminacion multiple|interseccional|medio rural",
            r"(administraciones|poderes) publicos.*(medidas|impulsar|promover|velar)",
            r"plan(es)? (de|para la) (igualdad|no discriminacion).*(lgtbi|trans)",
            r"infraccion(es)? y sancion(es)?|regimen sancionador.*(lgtbi|discriminacion)",
            r"adopcion|acogimiento|idoneidad|diversidad familiar",
            r"formacion (del personal|a los empleados)|sensibilizacion",
        ),
        patrones_debiles=(r"medidas", r"servicios", r"plan", r"sancion"),
        prioridad=49,
    ),
    # --- I.5.3 Discapacidad y dependencia --------------------------------------------------------
    Materia(
        key="discapacidad-concepto-y-derechos",
        epigraph_code="I.5.3",
        title="La discapacidad: concepto, accesibilidad y derechos",
        resumen=(
            "El régimen de los derechos de las personas con discapacidad: el objeto y el ámbito "
            "del "
            "Texto Refundido de la Ley General de derechos de las personas con discapacidad y de "
            "su "
            "inclusión social, las definiciones (la discapacidad, la persona con discapacidad, la "
            "discapacidad en grado igual o superior al treinta y tres por ciento, la accesibilidad "
            "universal, el diseño para todas las personas, la igualdad de oportunidades y la no "
            "discriminación), la discriminación directa e indirecta y el acoso por razón de "
            "discapacidad, los derechos y las obligaciones, la vida independiente, la capacidad "
            "jurídica y el ejercicio de los derechos."
        ),
        patrones=(
            _RDL_1_2013,
            r"definicion(es)? de (la )?discapacidad|"
            r"persona con discapacidad|discapacidad igual o superior al",
            r"accesibilidad universal|diseno para todas las personas|"
            r"ajustes? razonables?",
            r"igualdad de oportunidades|vida independiente|inclusion social",
            r"discriminacion (directa|indirecta) por razon de discapacidad|"
            r"acoso por razon de discapacidad|conducta no deseada",
            r"capacidad juridica|ejercicio de (la capacidad|sus derechos)|tutela",
            r"lengua de signos|braille|productos de apoyo|accesibilidad (cognitiva|intelectual)",
        ),
        patrones_debiles=(r"discapacidad", r"accesibilidad", r"minusval"),
        prioridad=50,
    ),
    Materia(
        key="discapacidad-empleo-educacion-y-proteccion",
        epigraph_code="I.5.3",
        title="El empleo, la educación y la protección social de las personas con discapacidad",
        resumen=(
            "Los ámbitos donde se juega la inclusión: el derecho al trabajo y el empleo protegido "
            "(los centros especiales de empleo, el enclave laboral y la cuota de reserva), la "
            "educación inclusiva y la atención a la diversidad, la atención temprana, la salud y "
            "los "
            "servicios sociales, la protección social y las prestaciones, la acción protectora del "
            "sistema especial de prestaciones sociales y económicas, las medidas de fomento y de "
            "defensa de los derechos, y el régimen de infracciones y sanciones."
        ),
        patrones=(
            r"(empleo|trabajo) (protegido|de las personas con discapacidad)|"
            r"centros? especiales? de empleo|cuota de reserva|enclave laboral|"
            r"insercion laboral",
            r"educacion inclusiva|atencion a la diversidad|necesidades educativas (especiales|"
            r"especificas)|escolarizacion.*(discapacidad|diversidad)",
            r"proteccion social|accion protectora|prestaciones? (sociales y economicas|"
            r"por discapacidad)|sistema especial de prestaciones",
            r"atención temprana|atencion temprana|servicios sociales",
            r"infraccion(es)? y sancion(es)?|medidas de (fomento|defensa)",
        ),
        patrones_debiles=(r"empleo", r"educacion", r"prestacion"),
        prioridad=51,
    ),
    Materia(
        key="dependencia-concepto-y-grados",
        epigraph_code="I.5.3",
        title="La dependencia: concepto, grados y valoración",
        resumen=(
            "Qué es la dependencia y cómo se mide: el objeto y los principios de la Ley 39/2006 y "
            "del "
            "Sistema para la Autonomía y Atención a la Dependencia, la autonomía personal y las "
            "necesidades de apoyo, el concepto de dependencia y las actividades de la vida diaria, "
            "los tres grados de dependencia (moderada, severa y gran dependencia) y sus dos "
            "niveles, "
            "la valoración por el órgano competente y el baremo, el reconocimiento de la situación "
            "y "
            "su revisión, la persona cuidadora y la capacidad de obrar."
        ),
        patrones=(
            _LEY_39_2006,
            r"grado(s)? (de|i{1,3}|1|2|3)? ?dependencia|dependencia (moderada|severa|"
            r"gran dependencia)|gran dependencia",
            r"autonomia personal|sistema para la autonomia y atencion a la dependencia|\bsaad\b|"
            r"sistema de autonomia",
            r"valoracion (de la dependencia|de la autonomia)|baremo|"
            r"equipo de valoracion|organo de valoracion",
            r"actividades (basicas|instrumentales) de la vida diaria|vida diaria",
            r"reconocimiento de (la situacion|las situaciones)|revision del grado",
            r"capacidad de obrar|movilidad reducida|necesidad de apoyo",
        ),
        patrones_debiles=(r"dependencia", r"grado", r"autonomia"),
        prioridad=52,
    ),
    Materia(
        key="dependencia-servicios-y-prestaciones",
        epigraph_code="I.5.3",
        title="Los servicios y las prestaciones de la dependencia y su financiación",
        resumen=(
            "Lo que el sistema ofrece a quien está en situación de dependencia: el catálogo de "
            "servicios (la prevención y la promoción de la autonomía personal, la teleasistencia, "
            "la "
            "ayuda a domicilio, los centros de día y de noche, los centros residenciales), las "
            "prestaciones económicas (la vinculada al servicio, la de asistencia personal y la de "
            "cuidados en el entorno familiar), la compatibilidad y las incompatibilidades entre "
            "ellas, la persona cuidadora no profesional y el convenio especial, la intensidad de "
            "la "
            "prestación, la financiación y la participación del beneficiario, y la excedencia y "
            "los "
            "derechos de las personas cuidadoras."
        ),
        patrones=(
            r"catalogo de (servicios|servicios y prestaciones)|"
            r"prestaciones? (economicas?|del sistema)|cuantia de la prestacion",
            r"teleasistencia|ayuda a domicilio|centro de dia|centro de noche|"
            r"centro(s)? residencial(es)?|residencia",
            r"prestacion economica vinculada|asistencia personal|"
            r"cuidados en el entorno familiar|cuidado (no profesional|familiar)",
            r"pessoa? cuidadora|cuidador(a)? no profesional|convenio especial",
            r"compatibilidad|incompatibilidad|se podran percibir",
            r"financiacion|participacion (del|de la) (beneficiario|usuario)|aportacion",
            r"excedencia (por cuidado|para el cuidado)|derechos de las personas cuidadoras",
            r"intensidad (de la prestacion|del servicio)|horas? de atencion",
        ),
        patrones_debiles=(r"servicio", r"prestacion", r"ayuda", r"residencia"),
        prioridad=53,
    ),
)

#: El orden en que se **enseña** el índice: primero la igualdad (los principios, los planes, el
# empleo,
#: la tutela y la violencia de género, que es el epígrafe I.5.1 en su orden), después el epígrafe
# LGTBI
#: (los derechos, la rectificación registral y las medidas públicas) y por último discapacidad y
#: dependencia (los derechos, el empleo y la protección social, y el sistema de dependencia), que es
#: el orden de los tres epígrafes del temario.
ORDEN: tuple[str, ...] = (
    "igualdad-principios-y-criterios",
    "igualdad-planes-y-politicas",
    "igualdad-empleo-y-conciliacion",
    "igualdad-tutela-y-garantias",
    "violencia-de-genero-concepto-y-ambito",
    "violencia-de-genero-derechos-de-las-victimas",
    "violencia-de-genero-tutela-institucional",
    "lgtbi-derechos-y-conceptos",
    "lgtbi-rectificacion-registral",
    "lgtbi-medidas-publicas-y-sanciones",
    "discapacidad-concepto-y-derechos",
    "discapacidad-empleo-educacion-y-proteccion",
    "dependencia-concepto-y-grados",
    "dependencia-servicios-y-prestaciones",
)

__all__ = ["MATERIAS", "ORDEN"]

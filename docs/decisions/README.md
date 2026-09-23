# Registro de decisiones (ADR)

Formato: `ADR-NNN-titulo.md` con contexto, opciones, datos, decisión, consecuencias y reversión
(`docs/product-spec/13_DECISIONS-AND-OPEN-QUESTIONS.md` §Resolución).

| ADR | Título | Estado |
|---|---|---|
| [ADR-001](ADR-001-herramientas-y-lockfiles.md) | Herramientas y lockfiles de Python y Node | aceptada |
| [ADR-002](ADR-002-contrato-openapi-y-tipos.md) | Generación del contrato OpenAPI y de los tipos TypeScript | aceptada |
| [ADR-003](ADR-003-cabeceras-y-origen-local.md) | Endurecimiento HTTP del backend local en el MVP | aceptada y ratificada por el propietario (14/09/2026) |
| [ADR-004](ADR-004-typescript-fijado.md) | Versión de TypeScript fijada a 5.9.x | aceptada |
| [ADR-005](ADR-005-modelo-de-perfiles-y-reglas-de-examen.md) | Modelo de perfiles: convocatorias, programa y reglas de examen | aceptada y ratificada por el propietario (14/09/2026): `exam_parts` y `exam_rules` |
| [ADR-006](ADR-006-fixtures-desde-fuentes-oficiales.md) | Fixtures de perfil desde fuentes oficiales y condiciones de uso | aceptada y ratificada por el propietario (14/09/2026), solo para uso local y privado |
| [ADR-007](ADR-007-nodos-con-material-asignado.md) | Nodos de programa con material asignado: bloquear la retirada, no borrarla | aceptada (S04), cierra DEBT-005 |
| [ADR-008](ADR-008-tramos-del-texto-plano.md) | Tramos del texto plano: un bloque por línea en blanco, sin adivinar jerarquía | aceptada (S06), cierra DEBT-009 |
| [ADR-009](ADR-009-activar-es-aprobar.md) | Activar una plantilla es aprobarla | aceptada (S06) |
| [ADR-010](ADR-010-aritmetica-exacta-y-calificacion-oficial.md) | La puntuación se calcula con fracciones exactas, y la calificación oficial no se inventa | aceptada (S07), cierra DEBT-006 |
| [ADR-011](ADR-011-forma-de-corregir-una-parte.md) | La forma de corregir una parte la fija su convocatoria | aceptada (S08) |
| [ADR-012](ADR-012-busqueda-lexica-sin-embeddings.md) | La búsqueda del corpus es léxica (FTS5) hasta que exista un proveedor de embeddings | aceptada (S09), pendiente de ratificación |
| [ADR-013](ADR-013-rutas-anadidas-al-contrato.md) | Rutas añadidas al contrato de la API: registro único de lo que se construyó fuera de §6–§11 | propuesta (revisión de S00–S11), pendiente de ratificación |
| [ADR-014](ADR-014-parte-detectada-y-datos-sin-lector.md) | Dónde vive lo que el importador lee y no puede guardar | aceptada (S12), cierra DEBT-010 |
| [ADR-015](ADR-015-tercera-oposicion-celador.md) | Tercera oposición: Celador/a del SACYL | aceptada (22/09/2026) por decisión del propietario |
| [ADR-016](ADR-016-anki-y-markdown-como-material.md) | Anki y Markdown entran como material, y con qué se lee una baraja | aceptada (S12.3) |
| [ADR-017](ADR-017-que-hace-la-aplicacion-sola.md) | Qué hace la aplicación sola y qué sigue pidiendo una persona | aceptada (S12.5) |
| [ADR-018](ADR-018-orden-de-rutas-literales.md) | Las rutas literales se declaran antes que las parametrizadas, con una prueba que lo vigila | propuesta (23/09/2026), pendiente de ratificación |

La deuda técnica obligatoria (con su slice y su criterio de cierre) se registra aparte en
[`docs/DEBT.md`](../DEBT.md).

Una decisión que afecte a arquitectura, privacidad o seguridad requiere ADR **antes** de codificar.

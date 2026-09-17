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

La deuda técnica obligatoria (con su slice y su criterio de cierre) se registra aparte en
[`docs/DEBT.md`](../DEBT.md).

Una decisión que afecte a arquitectura, privacidad o seguridad requiere ADR **antes** de codificar.

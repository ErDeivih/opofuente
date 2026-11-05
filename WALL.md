# WALL — OpoFuente (bloque 3 del MAPA-DE-OBJETIVOS)

> Derivado de `F:\EspacioCodigo\_flujo-dsh\MAPA-DE-OBJETIVOS.md`, bloque 3.
> Se marca una casilla cuando la tarea está **ejecutada y verificada**; la siguiente ya está escrita.
> Fuente de verdad: el `MAPA-DE-OBJETIVOS.md`. Este fichero solo refleja su estado.

**Objetivo final**: un temario común de todas las oposiciones de informática C1 (basado en TAI +
enriquecido), consultable, con convocatorias que lo referencian y progreso de estudio.

Falta:
- [x] B-004: API y contrato del temario común, particularidades y «en qué convocatorias aparece».
  (hecha 2026-11-05: `/curricula`, versiones, avance, `/convocations/{id}/temario`,
  `references`, ficha de nodo con `appears_in` y particularidades, marca de estudiado y migración
  `0022`; contrato y tipos regenerados)
- [x] B-005: interfaz del temario y ficha de tema.
  (hecha 2026-11-05: sección «Temario», búsqueda que perdona tildes, ficha con
  «en qué convocatorias aparece», particularidades por convocatoria y marca de estudiado)
- [x] Avance por bloque y total. (hecho 2026-11-05: tarjeta «Avance» con total, por bloque y «qué
  queda»; el porcentaje lo calcula el servidor)

- **Terminado cuando**: abro el temario, busco un tema, veo sus apuntes y en qué convocatorias sale,
  y marco lo estudiado.

**Estado del bloque: 3 de 3 casillas hechas (2026-11-05).** El criterio de «terminado» se cumple:
la sección «Temario» abre el temario común, la búsqueda perdona tildes, la ficha enseña apuntes y
convocatorias, y la marca de estudiado queda guardada con su fecha. El avance por bloque y total se
calcula en el servidor y se pinta en la misma pantalla.

## Trabajo previo del bloque (ya cerrado, no está en las casillas del MAPA)

- [x] B-001 — modelos del temario común y migración `0021` con downgrade probado.
- [x] B-002 — fixture del temario común v1, generador con huella y siembra idempotente.
- [x] B-003 — equivalencias TAI → común y re-atribución del banco con informe e inverso.

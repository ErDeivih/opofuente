# OpoFuente — especificación de interfaz y experiencia

## 1. Principios

- La aplicación se organiza alrededor de estudiar, no de administrar una base de datos.
- Ninguna pantalla depende solo del color para autoridad, confianza o estado.
- Toda acción automática importante explica qué hizo y permite deshacer.
- La evidencia se abre en contexto sin perder la pregunta o respuesta.
- Las operaciones largas nunca bloquean la navegación.
- Los estados vacíos enseñan el siguiente paso concreto.

## 2. Estructura general

Barra lateral de escritorio y navegación compacta responsive:

```text
OpoFuente
[selector oposición / convocatoria]
Inicio
Bandeja            [pendientes]
Programa
Biblioteca
Preguntas          [conflictos]
Estudiar
Errores            [vencidos]
Cambios            [revisar]
Ajustes
```

Cabecera: búsqueda global, estado de worker, privacidad/modelo activo y acceso a diagnóstico.

## 3. Inicio

Orden de contenido:

1. **Continuar estudiando**: repaso vencido o última sesión.
2. **Acciones necesarias**: importación con errores, clasificaciones, fuente cambiada.
3. **Estado del programa**: cobertura documental, preguntas y dominio en tarjetas separadas.
4. **Actividad reciente**: lotes y sesiones.

No mostrar gráficas decorativas ni «probabilidad de aprobar».

## 4. Bandeja

### Estado inicial

Tres acciones: seleccionar carpeta, soltar archivos, pegar texto/URL. Explicación visible: «OpoFuente
copia; nunca mueve ni borra los originales».

### Inventario previo

Muestra raíz abreviada, número/tamaño, formatos, omitidos, posibles riesgos y selector de muestra/todo.
Botón principal: `Importar una copia`. Cancelar no cambia nada.

### Lote en proceso

Progreso total y paso actual, últimos elementos, incidencias, pausar/cancelar. Cerrar la pestaña no
cancela el worker.

### Revisión

Tabla virtualizada con selección múltiple:

- nombre/origen;
- tipo propuesto;
- oposición;
- tema;
- confianza textual + porcentaje si calibrado;
- autoridad/derechos;
- incidencias;
- acciones.

Panel lateral muestra preview, fragmentos justificativos y alternativas. Acciones de lote indican
exactamente cuántos elementos afectarán y permiten excluir filas. Tras aceptar aparece `Deshacer`.

## 5. Programa

Árbol expandible bloque -> tema -> epígrafe. Columnas:

- fuentes: aceptadas/candidatas/obsoletas;
- preguntas: oficiales/verificadas/dudosas;
- dominio: sin datos/bajo/medio/alto con recuento;
- próxima revisión.

Al seleccionar nodo: descripción oficial, fuentes asignadas, preguntas, errores, notas y acciones.
No calcular una única barra que mezcle las tres dimensiones.

## 6. Biblioteca

### Lista

Filtros por oposición, tipo, autoridad, estado, versión, derechos, calidad y colección. Búsqueda con
opción literal/semántica cuando disponible.

### Documento

Cabecera: título lógico, versión activa, autoridad, vigencia, procedencia y derechos. Pestañas:

- lector;
- estructura;
- asignaciones;
- versiones/diff;
- preguntas relacionadas;
- metadatos/auditoría.

El lector sincroniza página original y texto extraído cuando sea posible. Un warning OCR permanece
visible. Copiar cita incluye título, versión, sección/página y URL.

## 7. Preguntas

Tabla y vista de detalle. Badges obligatorios: `OFICIAL`, `PRIVADA`, `GENERADA`; estado de clave y
evidencia. Conflictos arriba, no escondidos en filtros.

Editor estructurado:

- enunciado;
- opciones;
- clave por versión;
- explicación por opción;
- evidencias;
- asignación temática;
- original en panel lateral.

Modificar una transcripción oficial crea corrección local con motivo. El original permanece visible.

## 8. Estudiar

### Configuración

Elegir modo, alcance, origen, número y feedback. Para examen oficial, parámetros bloqueados y mostrados
desde la convocatoria. Para simulacro, dejar claro que no es oficial.

### Pregunta

- progreso y cronómetro;
- enunciado con formato legible;
- opciones y marcar/revisar;
- navegación accesible por teclado;
- nunca mostrar badges que revelen respuesta;
- guardado local inmediato.

### Corrección

Resultado -> explicación -> opciones -> evidencia -> causa -> siguiente acción. Cita abre drawer
manteniendo el contexto. Botón `Reportar ambigua/conflicto`.

### Resultado

Puntuación total y por parte, umbrales, blancos/fallos/anuladas/reservas, tiempo y temas débiles. Para
recalculo, comparación antes/después y fuente de la clave.

## 9. Errores y repaso

Vista `Hoy` con cola ordenada y explicación. Vista `Conceptos` agrupa fallos relacionados. Cada error
permite causa, nota propia, evidencia y historial. No gamificar con rachas punitivas.

## 10. Cambios

Lista de cambios con fuente anterior/nueva, fecha, estado y número de derivados afectados. Vista diff
por sección. Acciones:

- confirmar relación de versión;
- revisar derivado;
- mantener como histórico;
- descartar propuesta de cambio.

Nunca botón global «actualizar todo con IA» sin previsualización.

## 11. Ajustes

- ruta de datos y uso de disco;
- capacidades instaladas: OCR, embeddings, vectorial, LLM;
- proveedor con prueba real y privacidad explicada;
- modelos descargados y tamaño;
- copia/restauración;
- exportación;
- diagnóstico y logs sanitizados.

Las claves se introducen en backend/almacén seguro; la UI solo muestra estado y últimos cuatro
caracteres si procede.

## 12. Estados y mensajes

Cada carga tiene `loading`, `empty`, `error`, `partial`, `success`. Los errores incluyen acción:
reintentar, abrir incidencia o volver. No mostrar stack traces.

Vocabulario fijo:

- **Fuente**: documento utilizado como evidencia.
- **Material**: cualquier contenido importado.
- **Oficial**: procedencia oficial confirmada.
- **Aceptado**: aprobado para el corpus; no equivale a oficial.
- **Generado**: producido por modelo.
- **Pendiente de revisión**: no debe usarse como verdad.
- **Sustituido**: conservado históricamente, no vigente por defecto.

## 13. Accesibilidad y responsive

- flujo completo de bandeja y pregunta con teclado;
- foco tras diálogo y navegación;
- labels y mensajes asociados a controles;
- `aria-live` para progreso moderado, sin anunciar cada porcentaje;
- tablas con alternativa/lista en ancho pequeño;
- objetivos táctiles mínimos razonables;
- contraste AA;
- gráficos acompañados de datos/texto.

## 14. Aceptación visual

Capturas/Playwright a 1440x900, 1024x768 y 390x844 para Inicio, Bandeja, Programa, Pregunta y
Corrección. Sin scroll horizontal global, elementos cortados o acciones inaccesibles. Revisar con datos
vacíos, largos, OCR dudoso, conflicto y 1.000 filas.


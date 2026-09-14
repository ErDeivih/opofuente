# Fixtures sintéticos

Material **creado para pruebas**, nunca material comercial ni contenido privado del usuario
(10_TEST-PLAN §2, `AGENTS.md`: «Fixtures sintéticos; nada privado/comercial en git»).

En S00 esta carpeta está vacía a propósito: todavía no existe ingestión que probar. Cada fixture
se añade en el slice que lo necesita:

| Fixture | Slice | Uso |
|---|---|---|
| PDF nativo multipágina, PDF escaneado pequeño, DOCX con títulos y tablas | S03 | extractores |
| CSV de preguntas válido y con filas defectuosas | S06 | importador |
| HTML con scripts y texto que intenta inyectar instrucciones | S03 | seguridad |
| ZIP seguro, ZIP con traversal y ZIP con ratio de expansión abusivo | S03 | seguridad |
| Dos archivos idénticos con nombres distintos; dos revisiones casi iguales | S02/S04 | duplicados |
| Cuestionarios sintéticos modelo A/B y claves v1/v2 | S08 | claves versionadas |

## Material de S02 (inventario y copia)

La bandeja de S02 **sí** necesita una carpeta con material. No se versiona como ficheros binarios:
las pruebas la crean en un directorio temporal con contenido propio y la borran al terminar. Así no
entra en git nada que parezca material de estudio real, y el caso cubierto es exactamente el que
describe el plan de pruebas:

| Elemento | Dónde se crea | Qué prueba |
|---|---|---|
| `tema-01.pdf` y `tema-01-copia.pdf` (byte a byte iguales) | `tests/integration/test_import.py`, `tests/e2e/tray.spec.ts` | un solo artefacto con dos orígenes |
| `notas.txt` | ídem | copia normal |
| `.oculto.txt`, `~$temporal.docx`, `programa.exe` | ídem | omisión declarada (oculto, temporal, ejecutable) |
| `node_modules/` | ídem | directorio ignorado |
| `enlace-fuera` (junction a una carpeta de fuera) | ídem | no se sigue un enlace que sale de la raíz |
| `secreto.txt` fuera de la carpeta | ídem | el material de fuera no se copia ni se inventaría |

Nada de esto apunta jamás a una carpeta real del usuario: la raíz la elige el propio test.

Reglas:

- nada de material con derechos de terceros;
- ningún fichero con datos personales reales;
- los documentos sintéticos se generan a partir de texto propio y se versionan aquí;
- si un test necesita una fuente oficial, se guarda URL, fecha, derechos y hash, o se prueba con
  metadatos en lugar de descargar.

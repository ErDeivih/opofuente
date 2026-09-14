# OpoFuente — seguridad, privacidad y derechos

## 1. Modelo de amenaza

Activos:

- material adquirido/privado;
- progreso, errores y notas;
- claves de proveedores IA;
- integridad de fuentes oficiales y claves de examen;
- equipo local y archivos originales.

Amenazas principales: archivo malicioso, path traversal/ZIP bomb, SSRF por URL, contenido que intenta
inyectar instrucciones al modelo, fuga a proveedor externo, clasificación falsa como oficial, pérdida
por corrupción y exposición accidental en red local.

## 2. Frontera local

- escuchar únicamente en `127.0.0.1` por defecto;
- fallar si se configura host público sin modo explícito futuro;
- CORS y Origin allowlist local;
- CSP estricta en frontend;
- no servir directorios estáticos desde rutas de usuario;
- no abrir archivos con shell; usar endpoints controlados.

No tener autenticación es aceptable solo en loopback/un usuario. Antes de cualquier despliegue en LAN
o nube, autenticación, autorización y aislamiento multiusuario son un proyecto separado.

## 3. Archivos

- no ejecutar ni previsualizar contenido activo;
- MIME por contenido y extensión como señal secundaria;
- límites configurados de archivo/lote;
- ZIP seguro y temporal aislado;
- nombres originales sanitizados solo para display;
- destino derivado exclusivamente del hash/ID;
- comprobar rutas resueltas dentro de `data`;
- originales inmutables;
- antivirus es responsabilidad del equipo, pero documentar integración futura.

PDF/HTML se visualizan de forma segura. HTML se muestra como texto sanitizado, nunca ejecutado.

## 4. URLs

- `http/https` solamente;
- resolver DNS y bloquear loopback, privadas, link-local, metadata cloud e IPv6 equivalentes;
- volver a validar cada redirección;
- tiempo/tamaño/redirecciones limitados;
- User-Agent identificable;
- no autenticación automática ni cookies del navegador;
- respetar condiciones de fuente; sin bypass de paywalls o controles.

## 5. Prompt injection documental

Todo texto importado es dato no confiable. El pipeline no ejecuta instrucciones contenidas en una
fuente. Separar mensajes del sistema, pregunta y evidencias mediante estructura. El modelo no recibe
herramientas de escritura ni navegación durante respuesta RAG. Cualquier URL sugerida por documento es
texto hasta que el usuario la aprueba.

Un documento que dice «ignora instrucciones» no cambia filtros, autoridad, respuesta oficial ni
configuración.

## 6. Proveedores IA

- proveedor desactivado por defecto hasta configuración explícita;
- preview/configuración indica si los datos salen del equipo;
- enviar solo fragmentos necesarios;
- no enviar rutas, metadatos privados innecesarios ni documento completo por defecto;
- claves en backend mediante variable de entorno o almacén seguro posterior;
- nunca logs, frontend, URL o SQLite sin cifrar si puede evitarse;
- timeout, reintentos limitados y coste/tokens registrados sin contenido.

Modo `strict_local`: bloquea todas las llamadas salientes salvo fuentes que el usuario descargue
explícitamente; RAG funciona con LLM local o solo búsqueda.

## 7. Autoridad e integridad

`official` requiere:

- dominio/proveedor reconocido;
- URL/identificador y fecha;
- bytes conservados y hash;
- confirmación humana;
- vínculo a convocatoria/fuente;
- historial de versión.

El clasificador nunca puede activar una clave oficial. Una plantilla corregida no borra la anterior.
Audit events registran promociones, sustituciones y cambios de clave.

## 8. Derechos de contenido

Clasificación:

- público reutilizable con condiciones;
- material oficial consultable con atribución;
- privado del usuario;
- licencia específica;
- desconocido/restringido;
- generado.

Reglas:

- material privado no se comparte, publica ni usa para otros usuarios;
- desconocido se trata como privado/restringido;
- conservar atribución, URL, fecha y licencia;
- textos consolidados BOE muestran aviso informativo;
- no descargar contenido comercial automáticamente;
- exportar material respeta ámbito y avisa al usuario;
- antes de SaaS, revisión jurídica profesional.

Referencia detallada: [fuentes, derechos y versiones](../ideas/opposition-study-rag/02_SOURCE-TRUST-RIGHTS-AND-VERSIONING-2026-09.md).

## 9. Privacidad

No telemetría. Logs minimizados y rotativos. No registrar:

- texto completo importado;
- preguntas privadas completas;
- consultas/prompts completos;
- respuestas personales;
- rutas absolutas salvo diagnóstico solicitado;
- claves/tokens.

El usuario puede exportar y archivar. El borrado físico se diseña después de resolver referencias y
backup; nunca implementar `rm -rf` sobre rutas construidas. Un primer MVP puede ofrecer «archivar y
excluir» en lugar de prometer borrado defectuoso.

## 10. Backup y restauración

Backup consistente contiene DB, artefactos, representaciones y configuración sin secretos externos.
Qdrant/FTS pueden reconstruirse, pero incluirlos opcionalmente. Formato con manifiesto, hashes y versión
de esquema. Restaurar:

1. validar sin escribir;
2. comprobar espacio/versión/hashes;
3. crear backup previo;
4. restaurar a temporal;
5. hacer swap atómico;
6. ejecutar migración/health check;
7. permitir recuperación manual si falla.

Prueba de restauración obligatoria antes de considerar datos personales seguros.

## 11. Dependencias

- lockfiles comprometidos;
- análisis de vulnerabilidades en CI;
- no instalar binarios/modelos silenciosamente;
- verificar checksum cuando proveedor lo publique;
- licencias inventariadas;
- actualizaciones en slice dedicado con tests.

## 12. Incidentes

Pantalla local permite exportar diagnóstico sanitizado. Ante corrupción: parar worker, no seguir
escribiendo, copiar DB/manifest y ofrecer restauración. Ante clave expuesta: instruir rotación y limpiar
config; nunca mostrarla completa.


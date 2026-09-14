"""Worker local de trabajos persistidos (S02).

`job_worker.py` es el bucle que reclama trabajos de la cola de SQLite, los ejecuta sin bloquear
el bucle de eventos y los cierra con lease, reintento y cancelación cooperativa. El estado de
«está corriendo de verdad» que publica el informe de capacidades vive en
`opofuente.infrastructure.worker_liveness`.
"""

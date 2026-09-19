/**
 * GENERADO AUTOMÁTICAMENTE — no editar a mano.
 * Fuente: packages/contracts/openapi.json (esquema OpenAPI de FastAPI).
 * Regenerar: uv run python -m opofuente.tools.export_openapi && npm run contracts:generate
 */

export interface paths {
    "/api/v1/answer-keys/{key_id}/mark-supersedes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirma que una plantilla sustituye a otra */
        post: operations["mark_answer_key_supersedes_api_v1_answer_keys__key_id__mark_supersedes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/attempts/{attempt_id}/error-classification": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Declara por qué se ha fallado (causa, concepto y nota)
         * @description Sin causa no hay error: lo que se declara aquí es lo que la persona dice de su fallo.
         */
        post: operations["classify_error_api_v1_attempts__attempt_id__error_classification_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/backups": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Copia de seguridad: listado, alta e identidad de cada copia */
        get: operations["list_backups_api_v1_backups_get"];
        put?: never;
        /**
         * Hace una copia de seguridad del árbol de datos
         * @description Copia consistente de DB, artefactos, representaciones y fixtures, con manifiesto y hashes.
         */
        post: operations["create_backup_api_v1_backups_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/backups/{backup_id}/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verifica una copia entrada por entrada, sin escribir nada */
        post: operations["verify_backup_api_v1_backups__backup_id__verify_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/capabilities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Capacidades reales y degradaciones */
        get: operations["capabilities_api_v1_capabilities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/change-sets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Los cambios de versión propuestos, confirmados o descartados */
        get: operations["list_change_sets_api_v1_change_sets_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/change-sets/{change_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Un cambio con su diff por sección y sus derivados afectados */
        get: operations["get_change_set_api_v1_change_sets__change_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/change-sets/{change_id}/affected": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * La simulación del cambio: qué se invalidaría, sin aplicar nada
         * @description Nada de lo que se ve aquí ha ocurrido todavía: el cambio se aplica al confirmarlo.
         */
        get: operations["get_change_set_affected_api_v1_change_sets__change_id__affected_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/change-sets/{change_id}/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Confirma el cambio: acepta la versión, sustituye la anterior y marca derivados
         * @description La relación de versión la confirma una persona; la anterior no se borra.
         */
        post: operations["confirm_change_set_api_v1_change_sets__change_id__confirm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/change-sets/{change_id}/discard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Descarta la propuesta sin invalidar nada (ruta añadida a §11) */
        post: operations["discard_change_set_api_v1_change_sets__change_id__discard_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification-decisions/{decision_id}/undo": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Deshace una decisión y devuelve la propuesta a la cola
         * @description Deshace la última decisión de una propuesta.
         *
         *     `{decision_id}` es el identificador de la decisión que devuelve la propia respuesta de decidir
         *     (`audit_event_id`). También se admite el identificador de la propuesta: la interfaz trabaja con
         *     propuestas y la API no le obliga a recordar la traza de auditoría para deshacer.
         */
        post: operations["undo_decision_api_v1_classification_decisions__decision_id__undo_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification-proposals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Propuestas de clasificación, con su banda y su evidencia */
        get: operations["list_proposals_api_v1_classification_proposals_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification-proposals/bulk-decision": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Decide en lote, con excepciones: nunca es todo-o-nada */
        post: operations["bulk_decision_api_v1_classification_proposals_bulk_decision_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification-proposals/{proposal_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Una propuesta concreta */
        get: operations["get_proposal_api_v1_classification_proposals__proposal_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification-proposals/{proposal_id}/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Acepta una propuesta (y crea el mapeo si es de tema) */
        post: operations["accept_proposal_api_v1_classification_proposals__proposal_id__accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification-proposals/{proposal_id}/reject": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Rechaza una propuesta (y retira el mapeo que hubiera salido de ella) */
        post: operations["reject_proposal_api_v1_classification_proposals__proposal_id__reject_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification-runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Ejecuta una pasada de clasificación ahora (idempotente) */
        post: operations["run_classification_api_v1_classification_runs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/classification/{subject_type}/{subject_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Clasificación vigente de un material (lo aceptado y lo provisional)
         * @description Lo que consta de un material: hace que aceptar una propuesta **se note** en el producto.
         *
         *     Devuelve solo lo decidido —lo aceptado por el usuario y lo aplicado provisionalmente por banda
         *     alta— con su etiqueta legible y separado, porque «provisional» significa «revisable».
         */
        get: operations["accepted_classification_api_v1_classification__subject_type___subject_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/collections": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Colecciones (ruta añadida: la spec pide colecciones sin fijar la ruta) */
        get: operations["list_collections_api_v1_collections_get"];
        put?: never;
        /** Crea una colección */
        post: operations["create_collection_api_v1_collections_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/collections/{collection_id}/items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Añade un sujeto a una colección (sin duplicarlo) */
        post: operations["add_collection_item_api_v1_collections__collection_id__items_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/convocations/{convocation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Convocatoria con sus partes y sus reglas de examen */
        get: operations["get_convocation_api_v1_convocations__convocation_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/convocations/{convocation_id}/curriculum": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Árbol del programa oficial */
        get: operations["get_curriculum_api_v1_convocations__convocation_id__curriculum_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/curriculum-mappings/{mapping_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Retira un mapeo (queda auditado) */
        delete: operations["delete_mapping_api_v1_curriculum_mappings__mapping_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/curriculum-nodes/{node_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Nodo del programa con su procedencia */
        get: operations["get_curriculum_node_api_v1_curriculum_nodes__node_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/curriculum-nodes/{node_id}/coverage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Cobertura de un nodo y de su subárbol (provisional y aceptada, separadas) */
        get: operations["node_coverage_api_v1_curriculum_nodes__node_id__coverage_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/derived-artifacts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Los derivados del material y lo que está pendiente de revisar (añadida a §11) */
        get: operations["list_derived_artifacts_api_v1_derived_artifacts_get"];
        put?: never;
        /**
         * Crea un resumen extractivo de unas secciones (ruta añadida a §11)
         * @description Sin modelo: junta los fragmentos de las secciones elegidas con su cita.
         */
        post: operations["create_derived_artifact_api_v1_derived_artifacts_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/derived-artifacts/{artifact_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Un derivado con sus secciones de origen (ruta añadida a §11) */
        get: operations["get_derived_artifact_api_v1_derived_artifacts__artifact_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/derived-artifacts/{artifact_id}/resolution": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cierra la revisión de un derivado (ruta añadida a §11) */
        post: operations["resolve_derived_artifact_api_v1_derived_artifacts__artifact_id__resolution_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/document-versions/{version_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Una versión con su documento
         * @description Contrato §7: una versión sola, sin pedir la ficha entera del documento.
         */
        get: operations["get_version_api_v1_document_versions__version_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/document-versions/{version_id}/content": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Texto extraído de la versión, por trozos
         * @description Contrato §7. Si la extracción no dejó texto, se dice con su calidad: no se inventa nada.
         */
        get: operations["get_version_content_api_v1_document_versions__version_id__content_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/document-versions/{version_id}/evidence": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Evidencia citable de la versión (ruta añadida: la spec pide citas abribles) */
        get: operations["list_evidence_api_v1_document_versions__version_id__evidence_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/document-versions/{version_id}/mappings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Asignaciones de programa de una versión
         * @description Contrato §7. Mismo formato de mapeo que sirve la clasificación: un mapeo es un mapeo.
         */
        get: operations["list_version_mappings_api_v1_document_versions__version_id__mappings_get"];
        put?: never;
        /**
         * Asigna una versión de documento a un nodo del programa
         * @description Contrato §7: una fuente compartida se guarda una vez y se asigna a varias oposiciones.
         *
         *     El mapeo apunta a la **versión**, no al artefacto: así una versión retirada deja de contar como
         *     cobertura sin tocar el material que ya se había asignado con ella. Se devuelve el mapeo tal y
         *     como queda (con su nodo), no solo su identificador: quien lo pide quiere verlo.
         */
        post: operations["add_mapping_api_v1_document_versions__version_id__mappings_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/document-versions/{version_id}/original": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El fichero original de una versión
         * @description Contrato §7: el original tal y como entró.
         *
         *     `inline` solo para los tipos que se pueden ver con seguridad; el resto se descarga. El fichero
         *     se sirve desde el almacén (nunca desde una ruta de fuera) y un material en cuarentena **no se
         *     sirve**: está retenido a propósito y eso se dice con un 409, no con un 404 que parecería un
         *     fallo.
         */
        get: operations["get_version_original_api_v1_document_versions__version_id__original_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/document-versions/{version_id}/sections": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Estructura de la versión (de aquí sale la cita) */
        get: operations["list_sections_api_v1_document_versions__version_id__sections_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Biblioteca: documentos con su versión activa */
        get: operations["list_documents_api_v1_documents_get"];
        put?: never;
        /** Promociona un artefacto a documento (o le añade una versión) */
        post: operations["promote_document_api_v1_documents_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/documents/{document_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Un documento con sus versiones */
        get: operations["get_document_api_v1_documents__document_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Edita los metadatos de un documento
         * @description Contrato §7. Lo que no se puede aplicar responde **409 con el motivo**, nunca a medias.
         *
         *     Marcar un documento como público es una decisión con consecuencias: exige que los derechos de su
         *     versión activa consten revisados y permitan reutilizar el material.
         */
        patch: operations["patch_document_api_v1_documents__document_id__patch"];
        trace?: never;
    };
    "/api/v1/documents/{document_id}/diff": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Compara dos versiones del mismo documento
         * @description **Ruta no listada en el contrato §7**: se declara aquí en lugar de esconderse.
         *
         *     El diff existe desde el primer día en el dominio y la spec lo pide («confirmar diff»), pero el
         *     contrato no fija su ruta. Compara el texto real de las secciones del mismo documento y **no
         *     fusiona nada**: informa y deja decidir.
         */
        get: operations["get_document_diff_api_v1_documents__document_id__diff_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/documents/{document_id}/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Versiones del documento (la antigua no desaparece) */
        get: operations["list_versions_api_v1_documents__document_id__versions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/documents/{document_id}/versions/{version_id}/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Acepta una versión (promoción crítica, confirmada y auditada) */
        post: operations["accept_version_api_v1_documents__document_id__versions__version_id__accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/documents/{document_id}/versions/{version_id}/mark-supersedes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirma que una versión sustituye a otra (la antigua se conserva) */
        post: operations["mark_supersedes_api_v1_documents__document_id__versions__version_id__mark_supersedes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/duplicate-clusters": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Grupos de material repetido o muy parecido */
        get: operations["list_duplicate_clusters_api_v1_duplicate_clusters_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/duplicate-clusters/{cluster_id}/resolve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resuelve un grupo de duplicados (nunca borra nada por sí solo) */
        post: operations["resolve_duplicate_cluster_api_v1_duplicate_clusters__cluster_id__resolve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/evidence-spans/{span_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Un fragmento de evidencia con lo necesario para abrirlo */
        get: operations["get_evidence_span_api_v1_evidence_spans__span_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/evidence/{evidence_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Una evidencia concreta, con su sección y su página */
        get: operations["get_evidence_api_v1_evidence__evidence_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/exports/anki-csv": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Exporta el banco a CSV de Anki, con su procedencia */
        post: operations["export_anki_csv_api_v1_exports_anki_csv_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/exports/markdown": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Exporta el banco a Markdown para Obsidian, con sus citas */
        post: operations["export_markdown_api_v1_exports_markdown_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/health/live": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Proceso vivo
         * @description No comprueba dependencias: solo que el proceso responde.
         */
        get: operations["live_api_v1_health_live_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/health/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listo para servir (comprueba la base de datos) */
        get: operations["ready_api_v1_health_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Lotes de inventario e importación */
        get: operations["list_batches_api_v1_ingestion_batches_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/files": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Copia los ficheros que el usuario selecciona o suelta (S03)
         * @description Subida de ficheros: cada uno se copia al almacén y sigue el pipeline.
         *
         *     Un ZIP se copia aquí y se expande en la extracción, con los límites de seguridad del módulo de
         *     ZIP (traversal, bombas y enlaces se rechazan).
         */
        post: operations["ingest_files_api_v1_ingestion_batches_files_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/paste": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Guarda el texto pegado como material propio (S03) */
        post: operations["ingest_paste_api_v1_ingestion_batches_paste_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/url": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Descarga una URL con la guarda de red y la guarda como material (S03) */
        post: operations["ingest_url_api_v1_ingestion_batches_url_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/{batch_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Lote con sus entradas, incidencias e informe */
        get: operations["get_batch_api_v1_ingestion_batches__batch_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/{batch_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Pide cancelar el lote (el worker se detiene entre ficheros) */
        post: operations["cancel_batch_api_v1_ingestion_batches__batch_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/{batch_id}/issues": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Incidencias del lote */
        get: operations["list_issues_api_v1_ingestion_batches__batch_id__issues_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/{batch_id}/items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Entradas del lote */
        get: operations["list_items_api_v1_ingestion_batches__batch_id__items_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/{batch_id}/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Informe del lote */
        get: operations["get_report_api_v1_ingestion_batches__batch_id__report_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/{batch_id}/representations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Texto extraído de las entradas del lote, con su calidad y sus avisos */
        get: operations["list_representations_api_v1_ingestion_batches__batch_id__representations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ingestion-batches/{batch_id}/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reintenta un lote fallido o cancelado (409 si está en otro estado) */
        post: operations["retry_batch_api_v1_ingestion_batches__batch_id__retry_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inventories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Inventaría una carpeta en modo lectura (no copia nada) */
        post: operations["create_inventory_api_v1_inventories_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inventories/{inventory_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Inventario ya realizado */
        get: operations["get_inventory_api_v1_inventories__inventory_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/inventories/{inventory_id}/confirm-import": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Confirma la importación de una copia del inventario */
        post: operations["confirm_import_api_v1_inventories__inventory_id__confirm_import_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/jobs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Trabajos (polling con backoff desde la interfaz) */
        get: operations["list_jobs_api_v1_jobs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/jobs/{job_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Estado de un trabajo */
        get: operations["get_job_api_v1_jobs__job_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/jobs/{job_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Pide cancelar un trabajo */
        post: operations["cancel_job_api_v1_jobs__job_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/learning-errors": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Los fallos agrupados por concepto (ruta añadida a §10) */
        get: operations["list_learning_errors_api_v1_learning_errors_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/learning-errors/{error_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Un fallo con su intento, su repaso y su historial (ruta añadida a §10) */
        get: operations["get_learning_error_api_v1_learning_errors__error_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/learning-errors/{error_id}/resolution": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Resuelve un error o lo vuelve a abrir (ruta añadida a §10)
         * @description Resolver un error es una decisión de quien estudia, y **no** detiene su repaso.
         */
        post: operations["resolve_learning_error_api_v1_learning_errors__error_id__resolution_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/mappings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Mapeos de programa de un sujeto */
        get: operations["list_mappings_api_v1_mappings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/oppositions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Oposiciones disponibles y su convocatoria activa */
        get: operations["list_oppositions_api_v1_oppositions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/oppositions/{opposition_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detalle de una oposición con sus convocatorias */
        get: operations["get_opposition_api_v1_oppositions__opposition_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/oppositions/{opposition_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activa una oposición (desactiva el resto) */
        post: operations["activate_opposition_api_v1_oppositions__opposition_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/oppositions/{opposition_id}/convocations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Convocatorias de una oposición */
        get: operations["list_convocations_api_v1_oppositions__opposition_id__convocations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Conjuntos de preguntas con sus recuentos */
        get: operations["list_question_sets_api_v1_question_sets_get"];
        put?: never;
        /** Crea un conjunto de preguntas */
        post: operations["create_question_set_api_v1_question_sets_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets/{set_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Un conjunto con sus recuentos */
        get: operations["get_question_set_api_v1_question_sets__set_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets/{set_id}/answer-keys": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Plantillas de un conjunto, con sus desenlaces */
        get: operations["list_answer_keys_api_v1_question_sets__set_id__answer_keys_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets/{set_id}/answer-keys/{key_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Activa una plantilla (activar es aprobar)
         * @description Activar una plantilla **es** aprobarla: lo decide una persona y queda en la auditoría.
         *
         *     Si el conjunto es oficial y la plantilla no tiene enlazada la plantilla oficial, responde 409
         *     con el motivo: una aprobación no convierte en oficial un documento que no lo es.
         */
        post: operations["activate_answer_key_api_v1_question_sets__set_id__answer_keys__key_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets/{set_id}/parse": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Importa preguntas, un CSV, un JSON o una plantilla a un conjunto
         * @description Las cuatro formas de llenar un conjunto: texto, CSV con mapeo, JSON y plantilla suelta.
         *
         *     Lo que no se entiende se informa (fila a fila, con su causa) y el resto entra: una fila mala no
         *     aborta el lote.
         */
        post: operations["parse_into_set_api_v1_question_sets__set_id__parse_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets/{set_id}/questions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Preguntas de un conjunto (banco: con su clave) */
        get: operations["list_set_questions_api_v1_question_sets__set_id__questions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/questions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Preguntas del banco, con filtros
         * @description El banco enseña la clave: aquí se revisa, no se examina a nadie.
         */
        get: operations["list_questions_api_v1_questions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/questions/{question_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Una pregunta con sus opciones y su clave */
        get: operations["get_question_api_v1_questions__question_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Cambia la composición de una pregunta
         * @description Tipo, posición y reserva. El **texto** de una oficial se corrige con corrección local.
         */
        patch: operations["patch_question_api_v1_questions__question_id__patch"];
        trace?: never;
    };
    "/api/v1/questions/{question_id}/evidence": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Evidencia que sostiene una pregunta */
        get: operations["list_question_evidence_api_v1_questions__question_id__evidence_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/questions/{question_id}/local-corrections": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Corrige una transcripción con su motivo, sin tocar el original */
        post: operations["correct_question_api_v1_questions__question_id__local_corrections_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/questions/{question_id}/report-issue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reporta que una pregunta es ambigua, está mal keyada o tiene una errata */
        post: operations["report_question_issue_api_v1_questions__question_id__report_issue_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rag/queries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pregunta al corpus y devuelve una respuesta con citas
         * @description La respuesta puede ser `insufficient`: es un resultado, no un error.
         */
        post: operations["ask_api_v1_rag_queries_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rag/queries/{query_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Una consulta guardada con su respuesta */
        get: operations["get_rag_query_api_v1_rag_queries__query_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rag/queries/{query_id}/retrieval": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Todo lo que se recuperó en una consulta, se usara o no */
        get: operations["get_rag_retrieval_api_v1_rag_queries__query_id__retrieval_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/representations/{representation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Una representación: extractor, calidad, páginas y avisos */
        get: operations["get_representation_api_v1_representations__representation_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/representations/{representation_id}/text": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Texto extraído, por trozos, con sus avisos a la vista */
        get: operations["get_representation_text_api_v1_representations__representation_id__text_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/restore/execute": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restaura una copia validada, con copia previa automática y deshacer si falla */
        post: operations["execute_restore_api_v1_restore_execute_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/restore/validate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Previsualiza una restauración: valida, comprueba espacio y versión, y no escribe */
        post: operations["validate_restore_api_v1_restore_validate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/review-groups": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Grupos de revisión: propuestas pendientes agrupadas por eje y valor */
        get: operations["review_groups_api_v1_review_groups_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reviews/due": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Lo que toca repasar hoy, con su motivo */
        get: operations["due_reviews_api_v1_reviews_due_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reviews/mastery": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El dominio estimado de cada nodo del programa (ruta añadida a §10)
         * @description Lo que la aplicación puede decir del dominio de cada tema, sin inventar un porcentaje.
         *
         *     Los nodos sin intentos se declaran «sin datos» y los que tienen pocos, «evidencia insuficiente»:
         *     07_UI-UX §5 pide enseñar esa columna, y aquí se calcula con la misma regla para todos.
         */
        get: operations["program_mastery_api_v1_reviews_mastery_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reviews/{review_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** El estado de un repaso (ruta añadida a §10) */
        get: operations["get_review_api_v1_reviews__review_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reviews/{review_id}/complete": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Declara el resultado de un repaso hecho y lo reprograma */
        post: operations["complete_review_api_v1_reviews__review_id__complete_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reviews/{review_id}/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El historial de un repaso, del cambio más reciente al más antiguo (añadida a §10)
         * @description Lo que ha movido la fecha de un repaso: sin esto, una fecha no se puede explicar.
         */
        get: operations["get_review_history_api_v1_reviews__review_id__history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reviews/{review_id}/snooze": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Aplaza un repaso sin contarlo como repasado */
        post: operations["snooze_review_api_v1_reviews__review_id__snooze_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Busca en el corpus publicado (sin generar respuesta) */
        post: operations["search_api_v1_search_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Configuración efectiva sanitizada (sin secretos)
         * @description Configuración efectiva, **con el destino real de cada proveedor** (DEBT-001).
         *
         *     Cada proveedor se clasifica por separado sobre su endpoint efectivo: antes el proveedor de
         *     embeddings se informaba dentro del bloque de LLM, y un endpoint local contaba como que salía del
         *     equipo. Un destino `unknown` viaja como tal y cuenta como que sí sale.
         */
        get: operations["read_settings_api_v1_settings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Sesiones de estudio de una oposición (ruta añadida a §10)
         * @description Ruta **añadida** al contrato §10: Inicio necesita saber qué hay para continuar.
         *
         *     Sin ella, «Continuar estudiando» no tendría de dónde leer, y el producto promete esa tarjeta.
         */
        get: operations["list_study_sessions_api_v1_study_sessions_get"];
        put?: never;
        /**
         * Crea una sesión de estudio con su composición congelada
         * @description Monta la sesión. Si falta material, clave activa o la parte no se corrige aquí, lo dice.
         */
        post: operations["create_study_session_api_v1_study_sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Una sesión con su configuración y su progreso */
        get: operations["get_study_session_api_v1_study_sessions__session_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/answers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Registra una respuesta y la corrige con la clave congelada
         * @description Registra el intento **una sola vez**: reenviar lo mismo no crea otro y cambiarlo es 409.
         */
        post: operations["answer_api_v1_study_sessions__session_id__answers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/current-question": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** La pregunta que toca ahora, sin solución */
        get: operations["current_question_api_v1_study_sessions__session_id__current_question_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/finish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Termina la sesión y calcula el resultado */
        post: operations["finish_study_session_api_v1_study_sessions__session_id__finish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/navigate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mueve el puntero: a una posición o al siguiente/anterior */
        post: operations["navigate_api_v1_study_sessions__session_id__navigate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/recalculate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Recalcula la sesión con la clave activa ahora (ruta añadida a §10)
         * @description Ruta **añadida** al contrato §10 para S08.
         *
         *     Una clave corregida no cambia sola lo que ya se corrigió: recalcular es una acción explícita que
         *     crea evaluaciones nuevas, conserva el resultado anterior y explica de dónde a dónde cambió.
         */
        post: operations["recalculate_study_session_api_v1_study_sessions__session_id__recalculate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/result": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** El resultado de una sesión terminada */
        get: operations["study_result_api_v1_study_sessions__session_id__result_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** La revisión: cada pregunta con lo que se marcó y su corrección */
        get: operations["study_review_api_v1_study_sessions__session_id__review_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/study-sessions/{session_id}/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Inicia la sesión (congela el reloj) */
        post: operations["start_study_session_api_v1_study_sessions__session_id__start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /**
         * AcceptedClassificationSchema
         * @description Lo que consta de un material: lo aceptado y lo que quedó provisional (revisable).
         */
        AcceptedClassificationSchema: {
            /** Pending Review */
            pending_review: boolean;
            /** Subject Id */
            subject_id: string;
            /** Subject Label */
            subject_label?: string | null;
            /** Subject Type */
            subject_type: string;
            /** Values */
            values?: components["schemas"]["AcceptedValueSchema"][];
        };
        /**
         * AcceptedValueSchema
         * @description Un eje de la clasificación vigente de un material, con su etiqueta legible.
         */
        AcceptedValueSchema: {
            /** Axis */
            axis: string;
            /** Confidence */
            confidence: number;
            /** Decided At */
            decided_at?: string | null;
            /** Is Critical */
            is_critical: boolean;
            /**
             * Status
             * @enum {string}
             */
            status: "accepted" | "auto_applied_provisional";
            /** Value */
            value: string;
            /** Value Label */
            value_label?: string | null;
        };
        /**
         * ActiveConvocationSchema
         * @description Convocatoria activa de una oposición, en la forma mínima que necesita el selector.
         */
        ActiveConvocationSchema: {
            /** Code */
            code: string;
            /** Id */
            id: string;
            /**
             * Published At
             * Format: date
             */
            published_at: string;
            status: components["schemas"]["ConvocationStatus"];
        };
        /**
         * AffectedSchema
         * @description Un dependiente afectado por el cambio, con su motivo.
         */
        AffectedSchema: {
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "derived_artifact" | "question_version" | "rag_answer";
            /** Reason */
            reason: string;
            /** Reviewable */
            reviewable: boolean;
            /** Sections */
            sections: string[];
            /** Title */
            title: string;
        };
        /** AlternativeSchema */
        AlternativeSchema: {
            /** Confidence */
            confidence: number;
            /** Value */
            value: string;
        };
        /** AnswerKeySchema */
        AnswerKeySchema: {
            /** Approved At */
            approved_at?: string | null;
            /** Created At */
            created_at?: string | null;
            /** Entries */
            entries: components["schemas"]["KeyEntrySchema"][];
            /** Id */
            id: string;
            /** Published At */
            published_at?: string | null;
            /** Question Set Id */
            question_set_id: string;
            /** Source Document Version Id */
            source_document_version_id?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "active" | "superseded" | "rejected";
            /** Supersedes Id */
            supersedes_id?: string | null;
            /** Version No */
            version_no: number;
        };
        /**
         * AnswerOutcomeSchema
         * @description Qué ha pasado al registrar una respuesta, con la corrección si se puede enseñar.
         *
         *     Lleva la **pregunta respondida**: la pantalla enseña el resultado de lo que se acaba de
         *     contestar antes de pasar a la siguiente, y esa pregunta es la que trae su corrección.
         */
        AnswerOutcomeSchema: {
            /** Already Answered */
            already_answered: boolean;
            attempt: components["schemas"]["AttemptSchema"];
            correction?: components["schemas"]["CorrectionSchema"] | null;
            question: components["schemas"]["SessionQuestionSchema"];
            /** Saved */
            saved: boolean;
            session: components["schemas"]["SessionSchema"];
        };
        /**
         * AnswerRequestSchema
         * @description La respuesta a una pregunta: qué se marcó, cuánto se tardó y con qué confianza.
         */
        AnswerRequestSchema: {
            /** Chosen Option Keys */
            chosen_option_keys?: string[];
            /** Client Sequence */
            client_sequence?: number | null;
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            /**
             * Elapsed Ms
             * @default 0
             */
            elapsed_ms: number;
            /** Question Version Id */
            question_version_id: string;
        };
        /**
         * AnswerSchema
         * @description La respuesta con sus afirmaciones citadas y sus incertidumbres.
         */
        AnswerSchema: {
            /** Claims */
            claims: components["schemas"]["ClaimSchema"][];
            /** Created At */
            created_at?: string | null;
            /** Explanation */
            explanation: string;
            /** Id */
            id: string;
            /** Model */
            model?: string | null;
            /** Prompt Template Version */
            prompt_template_version?: string | null;
            /** Provider */
            provider: string;
            /** Query Id */
            query_id: string;
            /** Short Answer */
            short_answer: string;
            /**
             * Status
             * @enum {string}
             */
            status: "supported" | "partial" | "insufficient";
            /** Suggested Followups */
            suggested_followups: string[];
            /** Uncertainties */
            uncertainties: string[];
        };
        /**
         * AskRequestSchema
         * @description La consulta de RAG añade el estilo y si se admite material privado.
         */
        AskRequestSchema: {
            /**
             * Allow Private Sources
             * @default true
             */
            allow_private_sources: boolean;
            /** Authority Tier */
            authority_tier?: string | null;
            /** Convocation Id */
            convocation_id?: string | null;
            /** Curriculum Node Ids */
            curriculum_node_ids?: string[];
            /** Document Ids */
            document_ids?: string[];
            /** Languages */
            languages?: string[];
            /**
             * Limit
             * @default 10
             */
            limit: number;
            /** Opposition Id */
            opposition_id?: string | null;
            /** Query */
            query: string;
            /** Reference Date */
            reference_date?: string | null;
            /**
             * Strategy
             * @default lexical
             * @enum {string}
             */
            strategy: "lexical" | "hybrid";
            /**
             * Style
             * @default brief
             * @enum {string}
             */
            style: "brief" | "teach" | "compare";
            /**
             * Version Mode
             * @default current
             * @enum {string}
             */
            version_mode: "current" | "explicit_historical";
        };
        /**
         * AttemptSchema
         * @description Un intento: lo que se marcó y, si ya se corrigió, su desenlace.
         */
        AttemptSchema: {
            /**
             * Answered At
             * Format: date-time
             */
            answered_at: string;
            /** Chosen Option Keys */
            chosen_option_keys: string[];
            /** Client Sequence */
            client_sequence?: number | null;
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            /** Elapsed Ms */
            elapsed_ms: number;
            /** Id */
            id: string;
            /** Outcome */
            outcome?: ("correct" | "wrong" | "blank" | "annulled" | "excluded" | "conflicting" | "unused_reserve") | null;
            /** Question Version Id */
            question_version_id: string;
            /** Reason */
            reason?: string | null;
            score?: components["schemas"]["ScoreSchema"] | null;
            /** Session Question Id */
            session_question_id: string;
        };
        /** BackupListSchema */
        BackupListSchema: {
            /** Backups */
            backups: components["schemas"]["BackupSchema"][];
        };
        /**
         * BackupSchema
         * @description Una copia tal como se enseña: identidad, tamaño y si se puede restaurar aquí y ahora.
         */
        BackupSchema: {
            /** App Version */
            app_version: string;
            /** Created At */
            created_at: string;
            /** File Count */
            file_count: number;
            /** Id */
            id: string;
            /** Note */
            note?: string | null;
            /** Restorable */
            restorable: boolean;
            /** Restorable Reason */
            restorable_reason: string;
            /** Schema Revision */
            schema_revision: string;
            /** Scope */
            scope: string[];
            /** Size Bytes */
            size_bytes: number;
        };
        /** BatchDetailSchema */
        BatchDetailSchema: {
            batch: components["schemas"]["BatchSchema"];
            /** Entries */
            entries: components["schemas"]["EntrySchema"][];
            /** Issues */
            issues: components["schemas"]["IssueSchema"][];
            report: components["schemas"]["ImportReportSchema"];
        };
        /** BatchSchema */
        BatchSchema: {
            /** Counters */
            counters: {
                [key: string]: number;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Error Summary */
            error_summary?: string | null;
            /** Finished At */
            finished_at?: string | null;
            /** Formats */
            formats?: {
                [key: string]: number;
            };
            /** Id */
            id: string;
            /** Inventory Batch Id */
            inventory_batch_id?: string | null;
            /** Issue Counts */
            issue_counts?: {
                [key: string]: number;
            };
            /** Job Id */
            job_id?: string | null;
            /**
             * Kind
             * @enum {string}
             */
            kind: "inventory" | "import";
            /** Manifest Hash */
            manifest_hash?: string | null;
            /**
             * Mode
             * @enum {string}
             */
            mode: "read_only" | "copy";
            /** Source Path Display */
            source_path_display: string;
            /** Started At */
            started_at?: string | null;
            status: components["schemas"]["BatchStatus"];
            /**
             * Total Items
             * @default 0
             */
            total_items: number;
        };
        /**
         * BatchStatus
         * @enum {string}
         */
        BatchStatus: "queued" | "running" | "succeeded" | "failed" | "cancel_requested" | "cancelled";
        /** Body_ingest_files_api_v1_ingestion_batches_files_post */
        Body_ingest_files_api_v1_ingestion_batches_files_post: {
            /**
             * Files
             * @description Uno o más ficheros
             */
            files: string[];
        };
        /**
         * BulkDecisionRequestSchema
         * @description Decisión en lote con excepciones explícitas (11_IMPLEMENTATION-SLICES S04).
         */
        BulkDecisionRequestSchema: {
            /**
             * Decision
             * @enum {string}
             */
            decision: "accepted" | "rejected";
            /** Excluded */
            excluded?: string[];
            /** Note */
            note?: string | null;
            /** Overrides */
            overrides?: {
                [key: string]: string;
            };
            /** Proposal Ids */
            proposal_ids: string[];
        };
        /** BulkDecisionResponseSchema */
        BulkDecisionResponseSchema: {
            /** Applied */
            applied: number;
            /** Conflicts */
            conflicts: number;
            /** Excluded */
            excluded?: string[];
            /** Outcomes */
            outcomes: components["schemas"]["DecisionOutcomeSchema"][];
            /** Requested */
            requested: number;
        };
        /** CapabilitiesSchema */
        CapabilitiesSchema: {
            /** Capabilities */
            capabilities: components["schemas"]["CapabilitySchema"][];
            /** Degradations */
            degradations: components["schemas"]["DegradationSchema"][];
            /** Version */
            version: string;
        };
        /** CapabilitySchema */
        CapabilitySchema: {
            /** Detail */
            detail: string;
            /** Id */
            id: string;
            /** Label */
            label: string;
            /** Planned Slice */
            planned_slice?: string | null;
            status: components["schemas"]["CapabilityStatus"];
        };
        /**
         * CapabilityStatus
         * @description Estado real de una capacidad. Nada se declara operativo sin comprobarlo.
         * @enum {string}
         */
        CapabilityStatus: "enabled" | "disabled" | "unavailable" | "configured_unverified" | "planned";
        /**
         * ChangeOutcomeSchema
         * @description El resultado de confirmar o descartar: qué se ha hecho exactamente.
         */
        ChangeOutcomeSchema: {
            /** Applied */
            applied: boolean;
            change: components["schemas"]["ChangeSetSchema"];
            /** Marked */
            marked: string[];
            /** Reason */
            reason?: string | null;
            /** Superseded Version Id */
            superseded_version_id?: string | null;
        };
        /**
         * ChangeSetSchema
         * @description Una propuesta de cambio, con lo que se invalidaría al confirmarla.
         */
        ChangeSetSchema: {
            /** Affected */
            affected: components["schemas"]["AffectedSchema"][];
            /** Confirmed At */
            confirmed_at?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Discarded At */
            discarded_at?: string | null;
            /** Document Id */
            document_id: string;
            /** Document Title */
            document_title: string;
            /** Effect Note */
            effect_note: string;
            /** Id */
            id: string;
            /** New Version Id */
            new_version_id: string;
            /** New Version Label */
            new_version_label?: string | null;
            /** Notes */
            notes: string[];
            /** Previous Version Id */
            previous_version_id: string;
            /** Previous Version Label */
            previous_version_label?: string | null;
            /** Reviewed By */
            reviewed_by?: string | null;
            /** Sections */
            sections: components["schemas"]["SectionChangeSchema"][];
            /** Sections Added */
            sections_added: number;
            /** Sections Changed */
            sections_changed: number;
            /** Sections Removed */
            sections_removed: number;
            /** Sections Unchanged */
            sections_unchanged: number;
            /**
             * Status
             * @enum {string}
             */
            status: "proposed" | "confirmed" | "discarded";
        };
        /** CheckSchema */
        CheckSchema: {
            /** Detail */
            detail: string;
            /** Name */
            name: string;
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "failed";
        };
        /**
         * ClaimSchema
         * @description Una afirmación con las citas que la sostienen.
         */
        ClaimSchema: {
            /** Evidence */
            evidence: components["schemas"]["EvidenceSpanSchema"][];
            /**
             * Support
             * @enum {string}
             */
            support: "direct" | "inferred";
            /** Text */
            text: string;
        };
        /**
         * ClassificationReportSchema
         * @description Qué dejó la última pasada de clasificación: se sirve tal cual, sin redondear nada.
         */
        ClassificationReportSchema: {
            /** Auto Applied */
            auto_applied: number;
            /** Duplicates Found */
            duplicates_found: number;
            /** Proposals Created */
            proposals_created: number;
            /** Proposals Unchanged */
            proposals_unchanged: number;
            /** Subjects */
            subjects: number;
            /** Subjects Without Signals */
            subjects_without_signals: number;
            /** Summary */
            summary: string;
        };
        /** CollectionItemRequestSchema */
        CollectionItemRequestSchema: {
            /** Subject Id */
            subject_id: string;
            /**
             * Subject Type
             * @enum {string}
             */
            subject_type: "artifact" | "representation" | "document_version" | "section" | "evidence";
        };
        /** CollectionSchema */
        CollectionSchema: {
            /** Created At */
            created_at?: string | null;
            /** Description */
            description?: string | null;
            /** Id */
            id: string;
            /**
             * Item Count
             * @default 0
             */
            item_count: number;
            /** Items */
            items?: string[];
            /** Name */
            name: string;
        };
        /**
         * CompleteReviewSchema
         * @description El resultado **declarado** de un repaso hecho fuera de una sesión.
         */
        CompleteReviewSchema: {
            /** Cause */
            cause?: ("knowledge" | "confusion" | "reading" | "time" | "calculation" | "ambiguous" | "other") | null;
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            /** Note */
            note?: string | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "correct" | "wrong";
        };
        /**
         * ConceptGroupSchema
         * @description La vista `Conceptos`: los grupos y sus totales.
         */
        ConceptGroupSchema: {
            /** Groups */
            groups: components["schemas"]["ConceptSchema"][];
            /** Open Errors */
            open_errors: number;
            /** Total Errors */
            total_errors: number;
        };
        /**
         * ConceptSchema
         * @description Un concepto con los fallos que agrupa.
         */
        ConceptSchema: {
            /** Errors */
            errors: components["schemas"]["ErrorSchema"][];
            /** Key */
            key: string;
            /** Label */
            label: string;
            /**
             * Last Seen At
             * Format: date-time
             */
            last_seen_at: string;
            /** Node Id */
            node_id?: string | null;
            /** Occurrences */
            occurrences: number;
            /** Open Count */
            open_count: number;
            /** Resolved Count */
            resolved_count: number;
        };
        /** ConvocationDetailSchema */
        ConvocationDetailSchema: {
            /** Code */
            code: string;
            /** Exam Date */
            exam_date?: string | null;
            /** Id */
            id: string;
            /** Official Url */
            official_url: string;
            /** Opposition Code */
            opposition_code: string;
            /** Opposition Id */
            opposition_id: string;
            /** Opposition Name */
            opposition_name: string;
            /** Parts */
            parts: components["schemas"]["ExamPartSchema"][];
            /**
             * Published At
             * Format: date
             */
            published_at: string;
            /** Rules */
            rules: components["schemas"]["ExamRuleSchema"][];
            /** Source Reference */
            source_reference?: string | null;
            status: components["schemas"]["ConvocationStatus"];
            /** Title */
            title: string;
        };
        /** ConvocationReferenceSchema */
        ConvocationReferenceSchema: {
            /** Code */
            code: string;
            /** Exam Date */
            exam_date?: string | null;
            /** Id */
            id: string;
            /** Official Url */
            official_url: string;
            /**
             * Published At
             * Format: date
             */
            published_at: string;
            status: components["schemas"]["ConvocationStatus"];
            /** Title */
            title: string;
        };
        /**
         * ConvocationStatus
         * @enum {string}
         */
        ConvocationStatus: "draft" | "active" | "superseded" | "archived";
        /**
         * CorrectionOutcomeSchema
         * @description La versión corregida y, si la tenía, la plantilla nueva que apunta a ella.
         */
        CorrectionOutcomeSchema: {
            /** Key Id */
            key_id?: string | null;
            question: components["schemas"]["QuestionSchema"];
        };
        /**
         * CorrectionSchema
         * @description La corrección de una pregunta. **Aquí y solo aquí** viaja la solución.
         */
        CorrectionSchema: {
            /** Correct Option Keys */
            correct_option_keys: string[];
            /** Evidence */
            evidence: components["schemas"]["QuestionEvidenceSchema"][];
            /** Explanation */
            explanation?: string | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "correct" | "wrong" | "blank" | "annulled" | "excluded" | "conflicting" | "unused_reserve";
            /** Reason */
            reason?: string | null;
            score: components["schemas"]["ScoreSchema"];
        };
        /** CoverageNodeSchema */
        CoverageNodeSchema: {
            /** Accepted */
            accepted: number;
            /** Depth */
            depth: number;
            /** Materials */
            materials?: string[];
            /** Node Id */
            node_id: string;
            /** Path */
            path: string;
            /** Provisional */
            provisional: number;
            /** Title */
            title: string;
        };
        /**
         * CoverageSchema
         * @description Cobertura de un nodo y de su subárbol: provisional y aceptada, nunca mezcladas.
         */
        CoverageSchema: {
            /** Accepted */
            accepted: number;
            /** Materials Total */
            materials_total: number;
            /** Node Id */
            node_id: string;
            /** Path */
            path: string;
            /** Provisional */
            provisional: number;
            /** Subtree */
            subtree?: components["schemas"]["CoverageNodeSchema"][];
            /** Title */
            title: string;
            /** Unclassified Subjects */
            unclassified_subjects: number;
        };
        /** CreateBackupSchema */
        CreateBackupSchema: {
            /** Note */
            note?: string | null;
        };
        /** CreateCollectionRequestSchema */
        CreateCollectionRequestSchema: {
            /** Description */
            description?: string | null;
            /** Name */
            name: string;
        };
        /** CreateInventoryRequest */
        CreateInventoryRequest: {
            /** Source Path */
            source_path: string;
        };
        /** CreateQuestionSetSchema */
        CreateQuestionSetSchema: {
            /** Convocation Version Id */
            convocation_version_id?: string | null;
            /** Held At */
            held_at?: string | null;
            /** Model Code */
            model_code?: string | null;
            /** Opposition Id */
            opposition_id: string;
            /**
             * Set Type
             * @enum {string}
             */
            set_type: "official_exam" | "private_bank" | "practice" | "generated_batch";
            /** Source Document Version Id */
            source_document_version_id?: string | null;
            /** Title */
            title: string;
        };
        /**
         * CreateSessionSchema
         * @description Lo que se manda para montar una sesión.
         */
        CreateSessionSchema: {
            /** Convocation Version Id */
            convocation_version_id?: string | null;
            /** Feedback */
            feedback?: ("immediate" | "at_end") | null;
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam";
            /** Opposition Id */
            opposition_id: string;
            /**
             * Review Limit
             * @description Solo en `error_review`: cuántas preguntas vencidas entran como mucho.
             */
            review_limit?: number | null;
            /**
             * Shuffle
             * @default false
             */
            shuffle: boolean;
            /** Sources */
            sources?: components["schemas"]["SessionSourceSchema"][];
            /** Time Limit Minutes */
            time_limit_minutes?: number | null;
        };
        /**
         * CreateSummarySchema
         * @description Lo que se manda para resumir unas secciones de una versión.
         */
        CreateSummarySchema: {
            /** Document Version Id */
            document_version_id: string;
            /** Section Ids */
            section_ids: string[];
            /** Title */
            title?: string | null;
        };
        /** CsvMappingSchema */
        CsvMappingSchema: {
            /**
             * Correct
             * @default correct
             */
            correct: string | null;
            /**
             * Explanation
             * @default explanation
             */
            explanation: string | null;
            /** Options */
            options?: string[];
            /** Position */
            position?: string | null;
            /** Reserve */
            reserve?: string | null;
            /**
             * Source
             * @default source
             */
            source: string | null;
            /**
             * Stem
             * @default stem
             */
            stem: string;
            /**
             * Tags
             * @default tags
             */
            tags: string | null;
            /**
             * Topic
             * @default topic
             */
            topic: string | null;
        };
        /**
         * CurrentQuestionSchema
         * @description Qué pregunta toca y cómo va la sesión.
         */
        CurrentQuestionSchema: {
            /** Answered */
            answered: number;
            /** Finished */
            finished: boolean;
            /** Pending */
            pending: number;
            question?: components["schemas"]["SessionQuestionSchema"] | null;
            session: components["schemas"]["SessionSchema"];
            /** Total */
            total: number;
        };
        /** CurriculumNodeDetailSchema */
        CurriculumNodeDetailSchema: {
            /** Ancestors */
            ancestors: components["schemas"]["CurriculumNodeSchema"][];
            /** Convocation Code */
            convocation_code: string;
            /** Convocation Id */
            convocation_id: string;
            /** Convocation Title */
            convocation_title: string;
            /** Coverage */
            coverage?: null;
            node: components["schemas"]["CurriculumNodeSchema"];
            /** Official Url */
            official_url: string;
            /** Opposition Code */
            opposition_code: string;
            /** Opposition Name */
            opposition_name: string;
            /**
             * Published At
             * Format: date
             */
            published_at: string;
            /** Source Reference */
            source_reference?: string | null;
        };
        /** CurriculumNodeSchema */
        CurriculumNodeSchema: {
            /** Children */
            children: components["schemas"]["CurriculumNodeSchema"][];
            /** Depth */
            depth: number;
            /** Description */
            description?: string | null;
            /** Id */
            id: string;
            node_type: components["schemas"]["NodeType"];
            /** Official Code */
            official_code: string;
            /** Path */
            path: string;
            /** Position */
            position: number;
            /** Title */
            title: string;
        };
        /** CurriculumSchema */
        CurriculumSchema: {
            /** Convocation Code */
            convocation_code: string;
            /** Convocation Id */
            convocation_id: string;
            /** Counts */
            counts: {
                [key: string]: number;
            };
            /** Nodes */
            nodes: components["schemas"]["CurriculumNodeSchema"][];
            /** Opposition Code */
            opposition_code: string;
        };
        /** DecisionOutcomeSchema */
        DecisionOutcomeSchema: {
            /** Applied */
            applied: boolean;
            /** Audit Event Id */
            audit_event_id?: string | null;
            /** Mapping Id */
            mapping_id?: string | null;
            /** Proposal Id */
            proposal_id: string;
            /** Reason */
            reason?: string | null;
            /** Status */
            status: string;
        };
        /**
         * DecisionRequestSchema
         * @description Decisión explícita sobre una propuesta. `override_value` corrige el valor propuesto.
         */
        DecisionRequestSchema: {
            /**
             * Coverage Type
             * @default partial
             * @enum {string}
             */
            coverage_type: "mention" | "partial" | "complete";
            /** Note */
            note?: string | null;
            /** Override Value */
            override_value?: string | null;
        };
        /** DegradationSchema */
        DegradationSchema: {
            /** Code */
            code: string;
            /** Message */
            message: string;
        };
        /**
         * DerivedArtifactSchema
         * @description Un derivado del material (hoy, un resumen extractivo), con su procedencia y su estado.
         */
        DerivedArtifactSchema: {
            /** Content */
            content: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Document Id */
            document_id: string;
            /** Document Title */
            document_title: string;
            /** Document Version Id */
            document_version_id: string;
            /** Generator */
            generator: string;
            /** Id */
            id: string;
            /**
             * Kind
             * @constant
             */
            kind: "summary";
            /** Model */
            model?: string | null;
            /** Needs Review */
            needs_review: boolean;
            /** Needs Review At */
            needs_review_at?: string | null;
            /** Needs Review Reason */
            needs_review_reason?: string | null;
            /** Prompt Template Version */
            prompt_template_version?: string | null;
            /**
             * Review Status
             * @enum {string}
             */
            review_status: "pending" | "reviewed" | "discarded";
            /** Reviewed At */
            reviewed_at?: string | null;
            /** Sections */
            sections: string[];
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** DocumentDetailSchema */
        DocumentDetailSchema: {
            document: components["schemas"]["DocumentSchema"];
            /** Versions */
            versions?: components["schemas"]["VersionSchema"][];
        };
        /** DocumentPageSchema */
        DocumentPageSchema: {
            /** Documents */
            documents: components["schemas"]["DocumentSchema"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
        };
        /** DocumentSchema */
        DocumentSchema: {
            active_version?: components["schemas"]["VersionSchema"] | null;
            /** Authority Tier */
            authority_tier?: string | null;
            /** Canonical Identifier */
            canonical_identifier?: string | null;
            /** Canonical Title */
            canonical_title: string;
            /** Created At */
            created_at?: string | null;
            /** Document Type */
            document_type: string;
            /** Id */
            id: string;
            /** Is Public */
            is_public: boolean;
            /**
             * Mapping Count
             * @default 0
             */
            mapping_count: number;
            /**
             * Owner Scope
             * @enum {string}
             */
            owner_scope: "public" | "private_user" | "generated";
            /**
             * Version Count
             * @default 0
             */
            version_count: number;
        };
        /**
         * DueItemSchema
         * @description Una pregunta vencida, con su motivo y sus opciones para poder repasarla.
         */
        DueItemSchema: {
            /** Explanation */
            explanation: string;
            /** Is Reserve */
            is_reserve: boolean;
            /** Options */
            options: components["schemas"]["DueOptionSchema"][];
            /** Origin Type */
            origin_type: string;
            /** Overdue Days */
            overdue_days: number;
            /** Part Code */
            part_code?: string | null;
            /** Question Set Id */
            question_set_id: string;
            /** Question Version Id */
            question_version_id: string;
            review: components["schemas"]["ReviewItemSchema"];
            /** Session Id */
            session_id: string;
            /** Stable Key */
            stable_key: string;
            /** Stem */
            stem: string;
        };
        /**
         * DueOptionSchema
         * @description Una opción de la pregunta que toca repasar (sin decir cuál es la correcta).
         */
        DueOptionSchema: {
            /** Stable Key */
            stable_key: string;
            /** Text */
            text: string;
        };
        /** DuplicateClusterSchema */
        DuplicateClusterSchema: {
            /** Created At */
            created_at?: string | null;
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "same_text" | "near_duplicate";
            /** Members */
            members?: components["schemas"]["DuplicateMemberSchema"][];
            /**
             * Relation
             * @enum {string}
             */
            relation: "revision_candidate" | "subset" | "superset" | "similar";
            /** Resolution Note */
            resolution_note?: string | null;
            /** Resolved At */
            resolved_at?: string | null;
            /** Signature */
            signature: string;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "resolved" | "dismissed";
        };
        /** DuplicateGroupSchema */
        DuplicateGroupSchema: {
            /**
             * Can Merge
             * @default false
             */
            can_merge: boolean;
            /**
             * Conflicting Keys
             * @default false
             */
            conflicting_keys: boolean;
            /** Keys Seen */
            keys_seen: string[];
            /**
             * Kind
             * @enum {string}
             */
            kind: "same_question" | "reordered_options" | "similar";
            /** Members */
            members: string[];
        };
        /** DuplicateMemberSchema */
        DuplicateMemberSchema: {
            /** Is Representative */
            is_representative: boolean;
            /** Similarity */
            similarity: number;
            /** Subject Id */
            subject_id: string;
            /** Subject Label */
            subject_label?: string | null;
            /** Subject Type */
            subject_type: string;
        };
        /** EmbeddingSettingsSchema */
        EmbeddingSettingsSchema: {
            /**
             * Base Url Configured
             * @default false
             */
            base_url_configured: boolean;
            /**
             * Destination
             * @default disabled
             * @enum {string}
             */
            destination: "disabled" | "local" | "remote" | "unknown";
            /**
             * Destination Reason
             * @default sin proveedor de embeddings configurado
             */
            destination_reason: string;
            /** Model */
            model?: string | null;
            /** Provider */
            provider: string;
        };
        /** EntryPageSchema */
        EntryPageSchema: {
            /** Entries */
            entries: components["schemas"]["EntrySchema"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
        };
        /** EntrySchema */
        EntrySchema: {
            /** Artifact Sha256 */
            artifact_sha256?: string | null;
            /** Detail */
            detail?: string | null;
            /** Id */
            id: string;
            /** Media Type */
            media_type?: string | null;
            /** Original Name */
            original_name: string;
            /** Relative Path */
            relative_path: string;
            /** Size Bytes */
            size_bytes: number;
            status: components["schemas"]["ItemStatus"];
        };
        /**
         * ErrorClassificationSchema
         * @description Lo que se declara de un fallo: por qué, sobre qué concepto y con qué nota.
         */
        ErrorClassificationSchema: {
            /**
             * Cause
             * @enum {string}
             */
            cause: "knowledge" | "confusion" | "reading" | "time" | "calculation" | "ambiguous" | "other";
            /** Concept Label */
            concept_label?: string | null;
            /** Curriculum Node Id */
            curriculum_node_id?: string | null;
            /** Note */
            note?: string | null;
        };
        /**
         * ErrorDetailSchema
         * @description Un error con su intento, su repaso y el historial de ese repaso.
         */
        ErrorDetailSchema: {
            /** Answered At */
            answered_at?: string | null;
            /** Chosen Option Keys */
            chosen_option_keys: string[];
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            error: components["schemas"]["ErrorSchema"];
            /** Events */
            events: components["schemas"]["ReviewEventSchema"][];
            review?: components["schemas"]["ReviewItemSchema"] | null;
        };
        /**
         * ErrorSchema
         * @description Un fallo con la causa declarada y su procedencia (pregunta, sesión y parte).
         */
        ErrorSchema: {
            /** Attempt Id */
            attempt_id: string;
            /**
             * Cause
             * @enum {string}
             */
            cause: "knowledge" | "confusion" | "reading" | "time" | "calculation" | "ambiguous" | "other";
            /** Concept Label */
            concept_label?: string | null;
            /** Curriculum Node Id */
            curriculum_node_id?: string | null;
            /**
             * First Seen At
             * Format: date-time
             */
            first_seen_at: string;
            /** Id */
            id: string;
            /**
             * Last Seen At
             * Format: date-time
             */
            last_seen_at: string;
            /** Node Title */
            node_title?: string | null;
            /** Occurrences */
            occurrences: number;
            /** Part Code */
            part_code?: string | null;
            /** Question Version Id */
            question_version_id?: string | null;
            /** Resolved At */
            resolved_at?: string | null;
            /** Session Id */
            session_id?: string | null;
            /** Stable Key */
            stable_key?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "resolved";
            /** Stem */
            stem?: string | null;
            /** User Note */
            user_note?: string | null;
        };
        /**
         * EvidenceSchema
         * @description Unidad citable: es lo que permite abrir el documento en el sitio exacto.
         */
        EvidenceSchema: {
            /**
             * Char End
             * @default 0
             */
            char_end: number;
            /**
             * Char Start
             * @default 0
             */
            char_start: number;
            /** Citation Label */
            citation_label?: string | null;
            /** Document Version Id */
            document_version_id: string;
            /** Id */
            id: string;
            /**
             * Index Status
             * @default pending
             * @enum {string}
             */
            index_status: "pending" | "indexed" | "failed" | "stale";
            /** Normalized Text */
            normalized_text: string;
            /** Ordinal */
            ordinal: number;
            /** Page */
            page?: number | null;
            /** Quality */
            quality?: string | null;
            /** Section Id */
            section_id?: string | null;
            /** Text */
            text: string;
        };
        /**
         * EvidenceSpanSchema
         * @description Un fragmento de evidencia con lo necesario para abrirlo.
         */
        EvidenceSpanSchema: {
            /** Authority Tier */
            authority_tier?: string | null;
            /** Citation Label */
            citation_label?: string | null;
            /** Document Id */
            document_id: string;
            /** Document Title */
            document_title: string;
            /** Document Type */
            document_type: string;
            /** Document Version Id */
            document_version_id: string;
            /** Id */
            id: string;
            /** Ordinal */
            ordinal: number;
            /** Page */
            page?: number | null;
            /** Page End */
            page_end?: number | null;
            /** Page Start */
            page_start?: number | null;
            /** Section Id */
            section_id?: string | null;
            /** Section Title */
            section_title?: string | null;
            /** Text */
            text: string;
            /** Version Status */
            version_status: string;
        };
        /** ExamPartSchema */
        ExamPartSchema: {
            /** Code */
            code: string;
            /** Evidence Quote */
            evidence_quote: string;
            /** Fail If Errors Gte */
            fail_if_errors_gte?: number | null;
            format?: components["schemas"]["PartFormat"] | null;
            kind: components["schemas"]["PartKind"];
            /** Name */
            name: string;
            /** Notes */
            notes?: string | null;
            /** Options Per Question */
            options_per_question?: number | null;
            /** Ordinary Items */
            ordinary_items?: number | null;
            /** Parent Code */
            parent_code?: string | null;
            /** Pass Score */
            pass_score?: number | null;
            /** Position */
            position: number;
            /** Reserve Items */
            reserve_items?: number | null;
            /** Score Max */
            score_max?: number | null;
            /** Score Min */
            score_min?: number | null;
            /** Structure Note */
            structure_note?: string | null;
            /** Time Minutes */
            time_minutes?: number | null;
            /** Wrong Penalty Fraction */
            wrong_penalty_fraction?: number | null;
        };
        /** ExamRuleSchema */
        ExamRuleSchema: {
            /** Code */
            code: string;
            /** Description */
            description: string;
            /** Evidence Quote */
            evidence_quote: string;
            kind: components["schemas"]["RuleKind"];
            /** Value Text */
            value_text: string;
        };
        /**
         * ExportRequestSchema
         * @description Qué se exporta: un conjunto concreto, un tema, o todo lo de una oposición.
         */
        ExportRequestSchema: {
            /**
             * Include Restricted
             * @description Si se incluye el material con derechos restringidos o sin determinar. Por defecto sí, con aviso: el material es del usuario y quien exporta decide.
             * @default true
             */
            include_restricted: boolean;
            /**
             * Node Id
             * @description Nodo del programa: solo las preguntas asignadas a ese tema.
             */
            node_id?: string | null;
            /** Opposition Id */
            opposition_id?: string | null;
            /** Question Set Id */
            question_set_id?: string | null;
            /** Title */
            title?: string | null;
        };
        /**
         * ExportSchema
         * @description El fichero exportado, con lo que hay que saber de él.
         */
        ExportSchema: {
            /** Bytes */
            bytes: number;
            /** Content */
            content: string;
            /** Documents */
            documents: string[];
            /** Filename */
            filename: string;
            /**
             * Format
             * @enum {string}
             */
            format: "anki_csv" | "markdown";
            /** Item Count */
            item_count: number;
            /** Path */
            path: string;
            /** Provenance */
            provenance: {
                [key: string]: string;
            };
            /** Warnings */
            warnings: string[];
        };
        /** FieldError */
        FieldError: {
            /** Field */
            field: string;
            /** Message */
            message: string;
        };
        /**
         * ImportReportSchema
         * @description Informe del lote. Los contadores deben cuadrar (total = copiadas + fallidas + omitidas).
         */
        ImportReportSchema: {
            /** Artifacts Total */
            artifacts_total: number;
            /** Balanced */
            balanced: boolean;
            /** Batch Id */
            batch_id: string;
            /** Counters */
            counters: {
                [key: string]: number;
            };
            /**
             * Generated At
             * Format: date-time
             */
            generated_at: string;
            /** Issue Counts */
            issue_counts: {
                [key: string]: number;
            };
            /**
             * Kind
             * @enum {string}
             */
            kind: "inventory" | "import";
            status: components["schemas"]["BatchStatus"];
        };
        /**
         * InventorySchema
         * @description Respuesta de un inventario: qué hay y qué se omite, sin haber copiado nada.
         */
        InventorySchema: {
            batch: components["schemas"]["BatchSchema"];
            /**
             * Copied Anything
             * @default false
             * @constant
             */
            copied_anything: false;
            /** Issues */
            issues: components["schemas"]["IssueSchema"][];
            /**
             * Note
             * @default OpoFuente ha leído la carpeta sin modificarla. No se ha copiado ni movido nada todavía.
             */
            note: string;
            /** Sample */
            sample: components["schemas"]["EntrySchema"][];
        };
        /** IssuePageSchema */
        IssuePageSchema: {
            /** Issues */
            issues: components["schemas"]["IssueSchema"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
        };
        /** IssueReportRequestSchema */
        IssueReportRequestSchema: {
            /** Detail */
            detail: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "ambiguous" | "wrong_key" | "typo" | "outdated" | "other";
        };
        /** IssueReportSchema */
        IssueReportSchema: {
            /** Created At */
            created_at?: string | null;
            /** Detail */
            detail: string;
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "ambiguous" | "wrong_key" | "typo" | "outdated" | "other";
            /** Question Version Id */
            question_version_id: string;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "reviewed" | "dismissed";
        };
        /** IssueSchema */
        IssueSchema: {
            /** Code */
            code: string;
            /** Details */
            details?: {
                [key: string]: unknown;
            };
            /** Relative Path */
            relative_path?: string | null;
            /** Safe Message */
            safe_message: string;
            /**
             * Severity
             * @enum {string}
             */
            severity: "info" | "warning" | "error";
        };
        /**
         * ItemStatus
         * @enum {string}
         */
        ItemStatus: "discovered" | "inventoried" | "omitted" | "copied" | "hashed" | "extracted" | "unsupported_preserved" | "ocr_pending" | "expanded" | "failed" | "cancelled";
        /** JobSchema */
        JobSchema: {
            /** Attempts */
            attempts: number;
            /**
             * Cancel Requested
             * @default false
             */
            cancel_requested: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Error Code */
            error_code?: string | null;
            /** Error Message */
            error_message?: string | null;
            /** Finished At */
            finished_at?: string | null;
            /** Id */
            id: string;
            /** Job Type */
            job_type: string;
            /** Max Attempts */
            max_attempts: number;
            /** Progress */
            progress: number;
            /** Started At */
            started_at?: string | null;
            /** Status */
            status: string;
            /** Step */
            step?: string | null;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /**
         * JobStatus
         * @enum {string}
         */
        JobStatus: "queued" | "leased" | "running" | "succeeded" | "failed" | "cancel_requested" | "cancelled";
        /** KeyEntrySchema */
        KeyEntrySchema: {
            /** Correct Option Keys */
            correct_option_keys?: string[];
            /** Notes */
            notes?: string | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "keyed" | "annulled" | "unanswered" | "conflicting";
            /** Question Version Id */
            question_version_id: string;
        };
        /**
         * LimitsSchema
         * @description Límites efectivos de la configuración (07_UI-UX §11: «límites» en Ajustes).
         *
         *     Se publican para que la pantalla pueda decir con qué topes trabaja el programa sin que nadie
         *     tenga que leer el código, y para que un fallo por tamaño tenga una cifra que enseñar.
         */
        LimitsSchema: {
            /** Job Lease Seconds */
            job_lease_seconds: number;
            /** Max Batch Entries */
            max_batch_entries: number;
            /** Max File Bytes */
            max_file_bytes: number;
            /** Max Paste Bytes */
            max_paste_bytes: number;
            /** Max Pdf Pages */
            max_pdf_pages: number;
            /** Max Representation Chars */
            max_representation_chars: number;
            /** Max Url Bytes */
            max_url_bytes: number;
            /** Max Url Redirects */
            max_url_redirects: number;
            /** Max Zip Depth */
            max_zip_depth: number;
            /** Max Zip Entries */
            max_zip_entries: number;
            /** Max Zip Ratio */
            max_zip_ratio: number;
            /** Max Zip Uncompressed Bytes */
            max_zip_uncompressed_bytes: number;
            /** Worker Poll Seconds */
            worker_poll_seconds: number;
        };
        /** LiveSchema */
        LiveSchema: {
            /**
             * Status
             * @default alive
             * @constant
             */
            status: "alive";
            /** Version */
            version: string;
        };
        /** LlmSettingsSchema */
        LlmSettingsSchema: {
            /** Api Key Configured */
            api_key_configured: boolean;
            /** Base Url Configured */
            base_url_configured: boolean;
            /**
             * Destination
             * @enum {string}
             */
            destination: "disabled" | "local" | "remote" | "unknown";
            /** Destination Reason */
            destination_reason: string;
            /** Model */
            model?: string | null;
            /** Provider */
            provider: string;
            /** Sends Data Off Device */
            sends_data_off_device: boolean;
        };
        /**
         * LocalCorrectionSchema
         * @description Corrección local de una transcripción: **con motivo** y sin tocar el original importado.
         */
        LocalCorrectionSchema: {
            /** Note */
            note: string;
            /** Options */
            options?: string[] | null;
            /** Stem */
            stem?: string | null;
        };
        /**
         * MappingRequestSchema
         * @description Alta de un mapeo: qué nodo del programa cubre esta versión de documento (contrato §7).
         *
         *     No se acepta `confidence` desde fuera: un mapeo que pide una persona es una afirmación, no una
         *     estimación, y fingir una probabilidad inventada sería peor que no tenerla.
         */
        MappingRequestSchema: {
            /**
             * Coverage Type
             * @default partial
             * @enum {string}
             */
            coverage_type: "mention" | "partial" | "complete";
            /** Curriculum Node Id */
            curriculum_node_id: string;
        };
        /** MappingSchema */
        MappingSchema: {
            /** Approved At */
            approved_at?: string | null;
            /** Confidence */
            confidence: number;
            /**
             * Coverage Type
             * @enum {string}
             */
            coverage_type: "mention" | "partial" | "complete";
            /** Depth */
            depth: number;
            /** Id */
            id: string;
            /** Node Depth */
            node_depth: number;
            /** Node Id */
            node_id: string;
            /** Node Path */
            node_path: string;
            /** Node Title */
            node_title: string;
            /** Source Proposal Id */
            source_proposal_id?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "provisional" | "accepted" | "rejected";
            /** Subject Id */
            subject_id: string;
            /** Subject Label */
            subject_label?: string | null;
            /** Subject Type */
            subject_type: string;
        };
        /** MarkKeySupersedesRequestSchema */
        MarkKeySupersedesRequestSchema: {
            /** Superseded Id */
            superseded_id: string;
        };
        /** MarkSupersedesRequestSchema */
        MarkSupersedesRequestSchema: {
            /** Superseded Id */
            superseded_id: string;
        };
        /**
         * MasteryProgramSchema
         * @description El dominio de todos los nodos del programa, con el resumen de lo que se puede decir.
         */
        MasteryProgramSchema: {
            /** Convocation Id */
            convocation_id: string;
            /** Nodes */
            nodes: components["schemas"]["NodeMasterySchema"][];
            /** Nodes Insufficient */
            nodes_insufficient: number;
            /** Nodes Total */
            nodes_total: number;
            /** Nodes With Estimate */
            nodes_with_estimate: number;
            /** Nodes Without Data */
            nodes_without_data: number;
            /** Note */
            note: string;
            /** Opposition Id */
            opposition_id: string;
        };
        /**
         * NavigateRequestSchema
         * @description A dónde se navega: a una posición o al siguiente/anterior.
         */
        NavigateRequestSchema: {
            /** Direction */
            direction?: ("next" | "previous") | null;
            /** Position */
            position?: number | null;
        };
        /**
         * NodeMasterySchema
         * @description El dominio de un nodo concreto del programa.
         */
        NodeMasterySchema: {
            /** Accuracy */
            accuracy?: number | null;
            /** Attempts */
            attempts: number;
            /** Correct */
            correct: number;
            /** Curriculum Node Id */
            curriculum_node_id: string;
            /** Explanation */
            explanation: string;
            /** Has Estimate */
            has_estimate: boolean;
            /**
             * Level
             * @enum {string}
             */
            level: "no_data" | "insufficient_evidence" | "low" | "medium" | "high";
            /** Recent Attempts */
            recent_attempts: number;
        };
        /**
         * NodeType
         * @description Nivel estructural del programa dentro de una convocatoria.
         *
         *     Los perfiles oficiales no tienen la misma forma: TAI publica cuatro bloques con temas, y
         *     Guardia Civil publica veinticinco temas con bloques internos y epígrafes. El tipo describe el
         *     nivel, y cada convocatoria define su jerarquía (ver ADR-005).
         * @enum {string}
         */
        NodeType: "block" | "topic" | "epigraph";
        /** OcrSettingsSchema */
        OcrSettingsSchema: {
            /** Tesseract Available */
            tesseract_available: boolean;
            /** Tesseract Configured */
            tesseract_configured: boolean;
        };
        /** OppositionDetailSchema */
        OppositionDetailSchema: {
            /** Convocations */
            convocations: components["schemas"]["ConvocationReferenceSchema"][];
            opposition: components["schemas"]["OppositionSchema"];
        };
        /** OppositionSchema */
        OppositionSchema: {
            /** Active */
            active: boolean;
            active_convocation?: components["schemas"]["ActiveConvocationSchema"] | null;
            /** Code */
            code: string;
            /** Description */
            description?: string | null;
            /** Id */
            id: string;
            /** Name */
            name: string;
        };
        /** OptionSchema */
        OptionSchema: {
            /** Id */
            id: string;
            /** Label */
            label?: string | null;
            /** Position */
            position: number;
            /** Stable Key */
            stable_key: string;
            /** Text */
            text: string;
        };
        /** ParseIssueSchema */
        ParseIssueSchema: {
            /** Code */
            code: string;
            /** Detail */
            detail: string;
            /** Line */
            line: number;
        };
        /**
         * ParseQuestionSetSchema
         * @description Lo que se pide al importar: preguntas de un texto, un CSV, un JSON o una plantilla suelta.
         */
        ParseQuestionSetSchema: {
            /**
             * Kind
             * @default questions
             * @enum {string}
             */
            kind: "questions" | "answer_key" | "csv" | "json";
            mapping?: components["schemas"]["CsvMappingSchema"] | null;
            /** Source Document Version Id */
            source_document_version_id?: string | null;
            /** Text */
            text: string;
        };
        /**
         * PartFormat
         * @enum {string}
         */
        PartFormat: "single_choice" | "multi_mark_error" | "psychotechnical";
        /**
         * PartKind
         * @enum {string}
         */
        PartKind: "group" | "test";
        /**
         * PartScoreSchema
         * @description Puntuación de una parte, con su forma de cálculo y los umbrales como datos declarados.
         */
        PartScoreSchema: {
            /** Annulled */
            annulled: number;
            /** Blank */
            blank: number;
            /** Conflicting */
            conflicting: number;
            /** Correct */
            correct: number;
            /** Excluded */
            excluded: number;
            /**
             * Kind
             * @enum {string}
             */
            kind: "direct" | "scaled" | "pass_fail";
            /** Official Available */
            official_available: boolean;
            /** Ordinary Items */
            ordinary_items?: number | null;
            /** Part Code */
            part_code?: string | null;
            /** Part Name */
            part_name?: string | null;
            /** Pass Score */
            pass_score?: number | null;
            /** Passed */
            passed?: boolean | null;
            penalty?: components["schemas"]["ScoreSchema"] | null;
            /** Reserves Used */
            reserves_used: number;
            score: components["schemas"]["ScoreSchema"];
            /** Score Max */
            score_max?: number | null;
            /** Score Min */
            score_min?: number | null;
            /** Unused Reserves */
            unused_reserves: number;
            /** Verdict Note */
            verdict_note?: string | null;
            /** Wrong */
            wrong: number;
        };
        /**
         * PasteRequest
         * @description Texto pegado por el usuario (04_INGESTION §2).
         */
        PasteRequest: {
            /** Text */
            text: string;
            /** Title */
            title?: string | null;
        };
        /**
         * PatchDocumentRequestSchema
         * @description Edición de los metadatos de la obra (contrato §7: `PATCH /documents/{id}`).
         *
         *     Un campo ausente no se toca; un campo presente con `null` se **vacía** (autoridad e
         *     identificador). `owner_scope` solo admite lo que puede pedir una persona: `generated` es para
         *     material derivado y no se concede desde aquí.
         */
        PatchDocumentRequestSchema: {
            /** Authority Tier */
            authority_tier?: string | null;
            /** Canonical Identifier */
            canonical_identifier?: string | null;
            /** Canonical Title */
            canonical_title?: string | null;
            /** Document Type */
            document_type?: string | null;
            /** Owner Scope */
            owner_scope?: ("public" | "private_user") | null;
        };
        /**
         * PatchQuestionSchema
         * @description Cambia lo que se puede cambiar sin tocar el texto importado: una corrección es otra cosa.
         */
        PatchQuestionSchema: {
            /** Is Reserve */
            is_reserve?: boolean | null;
            /** Position */
            position?: number | null;
            /** Question Type */
            question_type?: ("single_choice" | "multi_mark_error" | "true_false" | "free_text_reference") | null;
            /** Reserve Order */
            reserve_order?: number | null;
            /** Stem */
            stem?: string | null;
        };
        /**
         * ProblemDetail
         * @description Cuerpo de error del contrato.
         */
        ProblemDetail: {
            /** Code */
            code: string;
            /** Correlation Id */
            correlation_id: string;
            /** Detail */
            detail: string;
            /** Field Errors */
            field_errors?: components["schemas"]["FieldError"][] | null;
            /** Instance */
            instance: string;
            /** Status */
            status: number;
            /** Title */
            title: string;
            /**
             * Type
             * @default about:blank
             */
            type: string;
        };
        /**
         * PromoteRequestSchema
         * @description Promociona un artefacto. `document_id` añade una versión a un documento que ya existe.
         */
        PromoteRequestSchema: {
            /** Artifact Id */
            artifact_id: string;
            /** Authority Tier */
            authority_tier?: string | null;
            /** Document Id */
            document_id?: string | null;
            /**
             * Document Type
             * @default unknown
             */
            document_type: string;
            /** Official Url */
            official_url?: string | null;
            /** Rights Code */
            rights_code?: string | null;
            /** Title */
            title?: string | null;
            /** Version Label */
            version_label?: string | null;
        };
        /** PromotionOutcomeSchema */
        PromotionOutcomeSchema: {
            /** Applied */
            applied: boolean;
            /** Created Document */
            created_document: boolean;
            /** Created Version */
            created_version: boolean;
            /** Document Id */
            document_id?: string | null;
            /** Reason */
            reason?: string | null;
            /** Version Id */
            version_id?: string | null;
        };
        /** ProposalPageSchema */
        ProposalPageSchema: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Proposals */
            proposals: components["schemas"]["ProposalSchema"][];
            /** Total */
            total: number;
        };
        /** ProposalSchema */
        ProposalSchema: {
            /** Alternatives */
            alternatives?: components["schemas"]["AlternativeSchema"][];
            /**
             * Axis
             * @enum {string}
             */
            axis: "document_type" | "opposition" | "topic" | "authority" | "rights";
            /**
             * Band
             * @enum {string}
             */
            band: "high" | "medium" | "low";
            /** Confidence */
            confidence: number;
            /** Created At */
            created_at?: string | null;
            /** Decided At */
            decided_at?: string | null;
            /** Decision Note */
            decision_note?: string | null;
            /** Engine Name */
            engine_name: string;
            /** Engine Version */
            engine_version: string;
            /** Evidence */
            evidence?: string[];
            /** Id */
            id: string;
            /** Is Critical */
            is_critical: boolean;
            /** Proposed Value */
            proposed_value: string;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "accepted" | "rejected" | "superseded" | "auto_applied_provisional";
            /** Subject Id */
            subject_id: string;
            /** Subject Label */
            subject_label?: string | null;
            /**
             * Subject Type
             * @enum {string}
             */
            subject_type: "artifact" | "representation";
            /** Value Label */
            value_label?: string | null;
        };
        /** QuestionEvidenceSchema */
        QuestionEvidenceSchema: {
            /** Citation Label */
            citation_label?: string | null;
            /** Claim */
            claim?: string | null;
            /** Document Version Id */
            document_version_id: string;
            /** Page */
            page?: number | null;
            /**
             * Role
             * @enum {string}
             */
            role: "stem" | "correct" | "distractor" | "explanation";
            /** Section Id */
            section_id?: string | null;
            /** Span Id */
            span_id: string;
            /**
             * Status
             * @enum {string}
             */
            status: "proposed" | "accepted" | "rejected";
            /** Text */
            text: string;
        };
        /**
         * QuestionImportReportSchema
         * @description Lo que ha pasado al importar: ni una fila se pierde, ni un conflicto se esconde.
         *
         *     Se llama `QuestionImportReport` y no `ImportReport` porque la ingestión ya tiene su propio
         *     `ImportReportSchema` (el cuadre del lote): dos modelos con el mismo nombre obligan a FastAPI a
         *     inventar nombres cualificados en el OpenAPI y rompen los tipos derivados del contrato.
         */
        QuestionImportReportSchema: {
            /**
             * Created
             * @default 0
             */
            created: number;
            /** Duplicates */
            duplicates: components["schemas"]["DuplicateGroupSchema"][];
            /**
             * Existing
             * @default 0
             */
            existing: number;
            /** Ignored Columns */
            ignored_columns: string[];
            /**
             * Incomplete
             * @default 0
             */
            incomplete: number;
            /** Issues */
            issues: components["schemas"]["ParseIssueSchema"][];
            /**
             * Key Entries
             * @default 0
             */
            key_entries: number;
            /** Key Id */
            key_id?: string | null;
            /**
             * Keys In Conflict
             * @default 0
             */
            keys_in_conflict: number;
            /** Missing Columns */
            missing_columns: string[];
            /** Model Code Detected */
            model_code_detected?: string | null;
            /** Rejected */
            rejected: components["schemas"]["RejectedRowSchema"][];
            /** Set Id */
            set_id: string;
            /** Unmatched Positions */
            unmatched_positions: number[];
            /**
             * With Key
             * @default 0
             */
            with_key: number;
        };
        /** QuestionPageSchema */
        QuestionPageSchema: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Questions */
            questions: components["schemas"]["QuestionSchema"][];
            /** Total */
            total: number;
        };
        /** QuestionSchema */
        QuestionSchema: {
            /** Correct Option Keys */
            correct_option_keys: string[];
            /** Created At */
            created_at?: string | null;
            /**
             * Explanation Count
             * @default 0
             */
            explanation_count: number;
            /** Id */
            id: string;
            /**
             * Is Reserve
             * @default false
             */
            is_reserve: boolean;
            /** Key Outcome */
            key_outcome?: ("keyed" | "annulled" | "unanswered" | "conflicting") | null;
            /** Note */
            note?: string | null;
            /** Options */
            options: components["schemas"]["OptionSchema"][];
            /**
             * Origin Type
             * @enum {string}
             */
            origin_type: "official" | "private" | "generated";
            /** Position */
            position: number;
            /** Question Set Id */
            question_set_id: string;
            /**
             * Question Type
             * @enum {string}
             */
            question_type: "single_choice" | "multi_mark_error" | "true_false" | "free_text_reference";
            /** Reserve Order */
            reserve_order?: number | null;
            /** Source Section Id */
            source_section_id?: string | null;
            /** Stable Key */
            stable_key: string;
            /**
             * Status
             * @enum {string}
             */
            status: "incomplete" | "complete" | "verified" | "conflicting" | "annulled" | "superseded";
            /** Stem */
            stem: string;
            /** Supersedes Id */
            supersedes_id?: string | null;
            /** Version No */
            version_no: number;
        };
        /** QuestionSetPageSchema */
        QuestionSetPageSchema: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Sets */
            sets: components["schemas"]["QuestionSetSchema"][];
            /** Total */
            total: number;
        };
        /** QuestionSetSchema */
        QuestionSetSchema: {
            /** Active Key Id */
            active_key_id?: string | null;
            /** Convocation Version Id */
            convocation_version_id?: string | null;
            /** Created At */
            created_at?: string | null;
            /** Held At */
            held_at?: string | null;
            /** Id */
            id: string;
            /**
             * Incomplete Count
             * @default 0
             */
            incomplete_count: number;
            /**
             * Is Official
             * @default false
             */
            is_official: boolean;
            /**
             * Key Count
             * @default 0
             */
            key_count: number;
            /** Model Code */
            model_code?: string | null;
            /** Opposition Id */
            opposition_id: string;
            /**
             * Question Count
             * @default 0
             */
            question_count: number;
            /**
             * Reserve Count
             * @default 0
             */
            reserve_count: number;
            /**
             * Set Type
             * @enum {string}
             */
            set_type: "official_exam" | "private_bank" | "practice" | "generated_batch";
            /** Source Document Version Id */
            source_document_version_id?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "confirmed" | "archived";
            /** Title */
            title: string;
        };
        /**
         * RagQuerySchema
         * @description Una consulta de RAG guardada, con su respuesta y la revisión del corpus que usó.
         */
        RagQuerySchema: {
            answer?: components["schemas"]["AnswerSchema"] | null;
            /** Corpus Revision */
            corpus_revision: string;
            /** Created At */
            created_at?: string | null;
            /** Id */
            id: string;
            /** Model */
            model?: string | null;
            /** Prompt Template Version */
            prompt_template_version?: string | null;
            /** Provider */
            provider: string;
            /** Question */
            question: string;
            /**
             * Strategy
             * @enum {string}
             */
            strategy: "lexical" | "hybrid";
            /**
             * Version Mode
             * @enum {string}
             */
            version_mode: "current" | "explicit_historical";
        };
        /**
         * ReadinessProblem
         * @description Cuerpo del 503 de `/health/ready`.
         *
         *     Es un problema RFC 9457 al que se añade el detalle de cada comprobación, de modo que la
         *     interfaz pueda explicar **por qué** la aplicación no está lista sin abrir otra petición.
         *     Se declara como esquema propio para que `application/problem+json` esté descrito de verdad
         *     en OpenAPI y el frontend use el tipo generado (no una conversión escrita a mano).
         */
        ReadinessProblem: {
            /** Checks */
            checks: components["schemas"]["CheckSchema"][];
            /** Code */
            code: string;
            /** Correlation Id */
            correlation_id: string;
            /** Detail */
            detail: string;
            /** Field Errors */
            field_errors?: components["schemas"]["FieldError"][] | null;
            /** Instance */
            instance: string;
            /** Status */
            status: number;
            /** Title */
            title: string;
            /**
             * Type
             * @default about:blank
             */
            type: string;
        };
        /** ReadinessSchema */
        ReadinessSchema: {
            /** Checks */
            checks: components["schemas"]["CheckSchema"][];
            /**
             * Status
             * @enum {string}
             */
            status: "ready" | "degraded";
        };
        /**
         * RecalculationSchema
         * @description Qué se dijo antes de recalcular con una clave nueva, y qué cambió (S08).
         *
         *     Recalcular no borra el resultado anterior: la interfaz puede explicar «tu puntuación cambió de X
         *     a Y por la plantilla oficial v2» en lugar de que la cifra cambie sola.
         */
        RecalculationSchema: {
            /** Changed */
            changed: boolean;
            /** Note */
            note: string;
            /** Previous Key Label */
            previous_key_label?: string | null;
            /** Previous Parts */
            previous_parts: components["schemas"]["PartScoreSchema"][];
            previous_total: components["schemas"]["ScoreSchema"];
            /** Recalculated At */
            recalculated_at?: string | null;
        };
        /** RejectedRowSchema */
        RejectedRowSchema: {
            /** Cause */
            cause: string;
            /** Detail */
            detail: string;
            /** Row Number */
            row_number: number;
        };
        /**
         * RepresentationSchema
         * @description Texto extraído de un artefacto, con quién lo extrajo, su calidad y sus avisos.
         *
         *     El texto **no** viaja aquí: se lee por trozos en `/representations/{id}/text`, para que un
         *     documento largo no bloquee la interfaz.
         */
        RepresentationSchema: {
            /** Artifact Id */
            artifact_id: string;
            /** Char Count */
            char_count: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Extractor */
            extractor: string;
            /**
             * Has Text
             * @default false
             */
            has_text: boolean;
            /** Id */
            id: string;
            /** Kind */
            kind: string;
            /** Language */
            language?: string | null;
            /**
             * Ocr Candidate
             * @default false
             */
            ocr_candidate: boolean;
            /** Page Count */
            page_count?: number | null;
            /** Quality */
            quality: string;
            /** Sources */
            sources?: components["schemas"]["RepresentationSourceSchema"][];
            /** Status */
            status: string;
            /** Warnings */
            warnings?: string[];
        };
        /**
         * RepresentationSourceSchema
         * @description De qué entrada sale el texto, con **su** origen y su profundidad de contenedor.
         *
         *     El origen se toma de la entrada, no del artefacto: unos mismos bytes pueden haber entrado como
         *     fichero, como texto pegado y como URL, y unirlos por artefacto atribuía a una entrada el origen
         *     de otra.
         */
        RepresentationSourceSchema: {
            /**
             * Depth
             * @default 0
             */
            depth: number;
            /** Location */
            location: string;
            /** Origin Type */
            origin_type?: string | null;
        };
        /**
         * RepresentationTextSchema
         * @description Trozo de texto pedido, con lo necesario para seguir leyendo y los avisos a la vista.
         */
        RepresentationTextSchema: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Quality */
            quality: string;
            /** Representation Id */
            representation_id: string;
            /** Text */
            text: string;
            /** Total Chars */
            total_chars: number;
            /** Truncated */
            truncated: boolean;
            /** Warnings */
            warnings?: string[];
        };
        /** ResolveDuplicateRequestSchema */
        ResolveDuplicateRequestSchema: {
            /** Note */
            note?: string | null;
            /**
             * Relation
             * @enum {string}
             */
            relation: "revision_candidate" | "subset" | "superset" | "similar";
        };
        /**
         * ResolveErrorSchema
         * @description Resolver un error: `resolved` o volver a abrirlo, con la nota de por qué.
         */
        ResolveErrorSchema: {
            /** Note */
            note?: string | null;
            /**
             * Resolved
             * @default true
             */
            resolved: boolean;
        };
        /**
         * RestorePreviewSchema
         * @description Lo que una restauración haría **antes** de hacerlo: es el paso 1 y 2 del contrato.
         */
        RestorePreviewSchema: {
            backup: components["schemas"]["BackupSchema"];
            /** Blockers */
            blockers: string[];
            /** Can Restore */
            can_restore: boolean;
            /** Free Bytes */
            free_bytes: number;
            /** Missing Scope */
            missing_scope: string[];
            /** Needed Bytes */
            needed_bytes: number;
            /** Previous Backup Note */
            previous_backup_note: string;
            /** Targets */
            targets: string[];
        };
        /** RestoreRequestSchema */
        RestoreRequestSchema: {
            /** Backup Id */
            backup_id: string;
            /**
             * Keep Rollback
             * @default false
             */
            keep_rollback: boolean;
        };
        /** RestoreResultSchema */
        RestoreResultSchema: {
            /** Backup Id */
            backup_id: string;
            /** Health Detail */
            health_detail: string;
            /** Health Ok */
            health_ok: boolean;
            /** Previous Backup Id */
            previous_backup_id: string;
            /** Restored */
            restored: string[];
            /** Rollback Paths */
            rollback_paths: string[];
            /** Schema Revision */
            schema_revision: string;
        };
        /** RetrievalHitSchema */
        RetrievalHitSchema: {
            /** Rank */
            rank: number;
            /** Score */
            score: number;
            span: components["schemas"]["EvidenceSpanSchema"];
            /**
             * Strategy
             * @enum {string}
             */
            strategy: "lexical" | "hybrid";
            /** Used */
            used: boolean;
        };
        /**
         * RetrievalSchema
         * @description La recuperación completa: todo lo que se encontró, se usara o no (§5, paso 9).
         */
        RetrievalSchema: {
            /** Corpus Revision */
            corpus_revision: string;
            /** Hits */
            hits: components["schemas"]["RetrievalHitSchema"][];
            /** Query Id */
            query_id: string;
            /** Used Ids */
            used_ids: string[];
        };
        /**
         * ReviewArtifactSchema
         * @description Cerrar la revisión de un derivado: sigue valiendo o se aparta.
         */
        ReviewArtifactSchema: {
            /**
             * Resolution
             * @enum {string}
             */
            resolution: "reviewed" | "discarded";
        };
        /**
         * ReviewEventSchema
         * @description Un paso del historial: de qué fecha a qué fecha, con qué resultado y por qué.
         */
        ReviewEventSchema: {
            /** Cause */
            cause?: ("knowledge" | "confusion" | "reading" | "time" | "calculation" | "ambiguous" | "other") | null;
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            /**
             * Due At
             * Format: date-time
             */
            due_at: string;
            /** Id */
            id: string;
            /** Interval Days */
            interval_days: number;
            /**
             * Kind
             * @enum {string}
             */
            kind: "created" | "attempt" | "reviewed" | "snoozed";
            /** Note */
            note?: string | null;
            /**
             * Occurred At
             * Format: date-time
             */
            occurred_at: string;
            /** Outcome */
            outcome?: ("correct" | "wrong") | null;
            /** Previous Due At */
            previous_due_at?: string | null;
            /** Previous Interval Days */
            previous_interval_days?: number | null;
            /** Reason */
            reason: string;
            /** Repetitions */
            repetitions: number;
        };
        /** ReviewGroupSchema */
        ReviewGroupSchema: {
            /** Axis */
            axis: string;
            /** Is Critical */
            is_critical: boolean;
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Max Confidence */
            max_confidence: number;
            /** Min Confidence */
            min_confidence: number;
            /** Proposal Ids */
            proposal_ids: string[];
            /** Proposed Value */
            proposed_value: string;
            /** Size */
            size: number;
            /** Subject Type */
            subject_type: string;
        };
        /**
         * ReviewItemSchema
         * @description El estado de repaso de una pregunta.
         */
        ReviewItemSchema: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Due At
             * Format: date-time
             */
            due_at: string;
            /** Id */
            id: string;
            /** Interval Days */
            interval_days: number;
            /** Lapses */
            lapses: number;
            /** Last Reason */
            last_reason?: string | null;
            /** Last Reviewed At */
            last_reviewed_at?: string | null;
            /** Learning Error Id */
            learning_error_id?: string | null;
            /** Opposition Id */
            opposition_id: string;
            /** Question Version Id */
            question_version_id: string;
            /** Repetitions */
            repetitions: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /**
         * ReviewQueueSchema
         * @description La vista `Hoy`: la cola ordenada, sus cifras, los conceptos y lo que no se puede decir.
         */
        ReviewQueueSchema: {
            /** Concepts */
            concepts: components["schemas"]["ConceptSchema"][];
            /** Items */
            items: components["schemas"]["DueItemSchema"][];
            /** Notes */
            notes: string[];
            stats: components["schemas"]["ReviewStatsSchema"];
        };
        /**
         * ReviewSchema
         * @description La revisión: cada pregunta con lo que se marcó y su corrección cuando se puede ver.
         */
        ReviewSchema: {
            /** Entries */
            entries: components["schemas"]["SessionQuestionSchema"][];
            /** Note */
            note?: string | null;
            /** Partial */
            partial: boolean;
            /** Pending */
            pending: number;
            session: components["schemas"]["SessionSchema"];
            /** Unanswered */
            unanswered: number;
        };
        /**
         * ReviewStatsSchema
         * @description Cuánto queda por repasar.
         */
        ReviewStatsSchema: {
            /** Active */
            active: number;
            /** Due */
            due: number;
            /** Lapses */
            lapses: number;
            /** Next Due At */
            next_due_at?: string | null;
        };
        /** RightsSchema */
        RightsSchema: {
            /** Attribution */
            attribution?: string | null;
            /** Code */
            code: string;
            /**
             * Commercial Reuse
             * @default false
             */
            commercial_reuse: boolean;
            /** Is Restricted */
            is_restricted: boolean;
            /** License Name */
            license_name?: string | null;
            /** License Url */
            license_url?: string | null;
            /** Notes */
            notes?: string | null;
            /**
             * Review Status
             * @enum {string}
             */
            review_status: "unknown" | "reviewed" | "restricted";
            /**
             * Sharing
             * @default false
             */
            sharing: boolean;
        };
        /**
         * RuleKind
         * @enum {string}
         */
        RuleKind: "boolean" | "integer" | "fraction" | "text";
        /**
         * ScoreSchema
         * @description Una puntuación: la fracción exacta y su decimal, que es solo para leerla.
         */
        ScoreSchema: {
            /** Decimal */
            decimal: string;
            /** Denominator */
            denominator: number;
            /** Fraction */
            fraction: string;
            /** Numerator */
            numerator: number;
        };
        /** SearchHitSchema */
        SearchHitSchema: {
            /** Matched Terms */
            matched_terms: string[];
            /** Rank */
            rank: number;
            /** Score */
            score: number;
            span: components["schemas"]["EvidenceSpanSchema"];
            /**
             * Strategy
             * @enum {string}
             */
            strategy: "lexical" | "hybrid";
        };
        /**
         * SearchRequestSchema
         * @description Lo que se manda para buscar (o para preguntar).
         */
        SearchRequestSchema: {
            /** Authority Tier */
            authority_tier?: string | null;
            /** Convocation Id */
            convocation_id?: string | null;
            /** Curriculum Node Ids */
            curriculum_node_ids?: string[];
            /** Document Ids */
            document_ids?: string[];
            /** Languages */
            languages?: string[];
            /**
             * Limit
             * @default 10
             */
            limit: number;
            /** Opposition Id */
            opposition_id?: string | null;
            /** Query */
            query: string;
            /** Reference Date */
            reference_date?: string | null;
            /**
             * Strategy
             * @default lexical
             * @enum {string}
             */
            strategy: "lexical" | "hybrid";
            /**
             * Version Mode
             * @default current
             * @enum {string}
             */
            version_mode: "current" | "explicit_historical";
        };
        /**
         * SearchResultSchema
         * @description Lo que devuelve una búsqueda: resultados, estrategia y lo que no se pudo hacer.
         */
        SearchResultSchema: {
            /** Corpus Revision */
            corpus_revision: string;
            /** Degradations */
            degradations: string[];
            /** Excluded */
            excluded: string[];
            /** Hits */
            hits: components["schemas"]["SearchHitSchema"][];
            /** Strategies */
            strategies: ("lexical" | "hybrid")[];
            /**
             * Strategy
             * @enum {string}
             */
            strategy: "lexical" | "hybrid";
            /** Total */
            total: number;
            /**
             * Version Mode
             * @enum {string}
             */
            version_mode: "current" | "explicit_historical";
        };
        /**
         * SectionChangeSchema
         * @description Una sección del diff: qué le pasó y, si se puede, sus dos textos.
         */
        SectionChangeSchema: {
            /**
             * Kind
             * @enum {string}
             */
            kind: "added" | "removed" | "changed" | "unchanged";
            /** Label */
            label: string;
            /** Left */
            left?: string | null;
            /** Right */
            right?: string | null;
        };
        /**
         * SectionDiffSchema
         * @description Cambio de una sección. El texto se recorta a un tope y **se dice** cuándo se recortó.
         */
        SectionDiffSchema: {
            /**
             * Kind
             * @enum {string}
             */
            kind: "added" | "removed" | "changed" | "unchanged";
            /** Label */
            label: string;
            /** Left */
            left?: string | null;
            /**
             * Left Truncated
             * @default false
             */
            left_truncated: boolean;
            /** Right */
            right?: string | null;
            /**
             * Right Truncated
             * @default false
             */
            right_truncated: boolean;
        };
        /** SectionSchema */
        SectionSchema: {
            /**
             * Char End
             * @default 0
             */
            char_end: number;
            /**
             * Char Start
             * @default 0
             */
            char_start: number;
            /** Document Version Id */
            document_version_id: string;
            /** Id */
            id: string;
            /** Label */
            label?: string | null;
            /** Ordinal */
            ordinal: number;
            /** Page End */
            page_end?: number | null;
            /** Page Start */
            page_start?: number | null;
            /** Parent Id */
            parent_id?: string | null;
            /** Position */
            position: number;
            /** Section Type */
            section_type: string;
            /** Title */
            title?: string | null;
        };
        /**
         * SessionConfigurationSchema
         * @description La configuración congelada al crear la sesión.
         */
        SessionConfigurationSchema: {
            /**
             * Feedback
             * @enum {string}
             */
            feedback: "immediate" | "at_end";
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam";
            /** Shuffle */
            shuffle: boolean;
            /** Sources */
            sources: components["schemas"]["SessionSourceSchema"][];
            /** Time Limit Minutes */
            time_limit_minutes?: number | null;
        };
        /** SessionPageSchema */
        SessionPageSchema: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Sessions */
            sessions: components["schemas"]["SessionSchema"][];
            /** Total */
            total: number;
        };
        /**
         * SessionQuestionSchema
         * @description Una pregunta de la sesión, sin solución: enunciado, opciones y lo que se marcó.
         */
        SessionQuestionSchema: {
            /** Answered */
            answered: boolean;
            /** Chosen Option Keys */
            chosen_option_keys: string[];
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            correction?: components["schemas"]["CorrectionSchema"] | null;
            /** Elapsed Ms */
            elapsed_ms?: number | null;
            /** Is Reserve */
            is_reserve: boolean;
            /** Options */
            options: components["schemas"]["OptionSchema"][];
            /** Origin Type */
            origin_type: string;
            /** Part Code */
            part_code?: string | null;
            /** Position */
            position: number;
            /** Question Type */
            question_type: string;
            /** Question Version Id */
            question_version_id: string;
            /** Reserve Order */
            reserve_order?: number | null;
            /** Session Question Id */
            session_question_id: string;
            /** Stable Key */
            stable_key: string;
            /** Stem */
            stem: string;
        };
        /**
         * SessionResultSchema
         * @description El resultado de una sesión, tal como se calculó y se guardó.
         */
        SessionResultSchema: {
            /** Answer Key Version Id */
            answer_key_version_id?: string | null;
            /** Calculated At */
            calculated_at?: string | null;
            /** Key Label */
            key_label?: string | null;
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam";
            /** Official Available */
            official_available: boolean;
            /** Official Note */
            official_note?: string | null;
            /** Parts */
            parts: components["schemas"]["PartScoreSchema"][];
            recalculation?: components["schemas"]["RecalculationSchema"] | null;
            /** Session Id */
            session_id: string;
            /** Substitutions */
            substitutions: components["schemas"]["SubstitutionSchema"][];
            total: components["schemas"]["PartScoreSchema"];
            /** Unfinished */
            unfinished: number;
        };
        /**
         * SessionSchema
         * @description Una sesión con su configuración congelada y su progreso.
         */
        SessionSchema: {
            /** Answer Key Version Id */
            answer_key_version_id?: string | null;
            /** Answered Questions */
            answered_questions: number;
            configuration: components["schemas"]["SessionConfigurationSchema"];
            /** Convocation Version Id */
            convocation_version_id?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Feedback
             * @enum {string}
             */
            feedback: "immediate" | "at_end";
            /** Finished At */
            finished_at?: string | null;
            /** Id */
            id: string;
            /** Key Label */
            key_label?: string | null;
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam";
            /** Opposition Id */
            opposition_id: string;
            /** Question Set Id */
            question_set_id?: string | null;
            result?: components["schemas"]["SessionResultSchema"] | null;
            /** Started At */
            started_at?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "running" | "finished" | "abandoned";
            /** Time Limit Minutes */
            time_limit_minutes?: number | null;
            /** Total Questions */
            total_questions: number;
        };
        /**
         * SessionSourceSchema
         * @description De dónde salen las preguntas y qué parte del examen representan.
         */
        SessionSourceSchema: {
            /**
             * Count
             * @description Cuántas preguntas ordinarias se quieren (solo en práctica).
             */
            count?: number | null;
            /**
             * Include Reserves
             * @default true
             */
            include_reserves: boolean;
            /**
             * Part Code
             * @description Parte de la convocatoria con la que se corrige. Es obligatoria: la penalización y los umbrales los publica la convocatoria, no el cliente.
             */
            part_code: string;
            /** Question Set Id */
            question_set_id: string;
        };
        /**
         * SettingsSchema
         * @description Configuración efectiva sanitizada. Nunca incluye secretos.
         */
        SettingsSchema: {
            /** Cors Origins */
            cors_origins: string[];
            /** Data Dir */
            data_dir: string;
            /** Database File */
            database_file: string;
            /** Disk Free Bytes */
            disk_free_bytes: number;
            /** Disk Total Bytes */
            disk_total_bytes: number;
            /** Editable */
            editable: boolean;
            embeddings: components["schemas"]["EmbeddingSettingsSchema"];
            /** Host */
            host: string;
            limits: components["schemas"]["LimitsSchema"];
            llm: components["schemas"]["LlmSettingsSchema"];
            /** Log Level */
            log_level: string;
            ocr: components["schemas"]["OcrSettingsSchema"];
            /** Port */
            port: number;
            /** Version */
            version: string;
        };
        /**
         * SnoozeReviewSchema
         * @description Aplazar un repaso sin contarlo como repasado.
         */
        SnoozeReviewSchema: {
            /** Days */
            days: number;
        };
        /**
         * SubstitutionSchema
         * @description Una pregunta anulada y la reserva que la sustituyó.
         */
        SubstitutionSchema: {
            /** Annulled Question Version Id */
            annulled_question_version_id: string;
            /** Reserve Question Version Id */
            reserve_question_version_id?: string | null;
        };
        /**
         * UrlRequest
         * @description URL que se descargará con la guarda de red (09_SECURITY §4).
         */
        UrlRequest: {
            /** Url */
            url: string;
        };
        /** VerificationSchema */
        VerificationSchema: {
            backup: components["schemas"]["BackupSchema"];
            /** Problems */
            problems: string[];
            /** Verified */
            verified: boolean;
        };
        /**
         * VersionContentSchema
         * @description Texto extraído de una versión, por trozos, con la calidad de la extracción a la vista.
         */
        VersionContentSchema: {
            /** Document Version Id */
            document_version_id: string;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Quality */
            quality?: string | null;
            /** Representation Id */
            representation_id?: string | null;
            /** Text */
            text: string;
            /** Total Chars */
            total_chars: number;
            /** Truncated */
            truncated: boolean;
            /** Warnings */
            warnings?: string[];
        };
        /**
         * VersionDetailSchema
         * @description Una versión con su documento (contrato §7: `GET /document-versions/{id}`).
         */
        VersionDetailSchema: {
            /** Document Id */
            document_id: string;
            /** Document Title */
            document_title: string;
            /** Document Type */
            document_type: string;
            /**
             * Mapping Count
             * @default 0
             */
            mapping_count: number;
            /**
             * Owner Scope
             * @enum {string}
             */
            owner_scope: "public" | "private_user" | "generated";
            version: components["schemas"]["VersionSchema"];
        };
        /**
         * VersionDiffSchema
         * @description Comparación de dos versiones: informa de los cambios y no fusiona nada.
         *
         *     Todos los campos son obligatorios a propósito: quien lea el contrato no tiene que suponer que
         *     «sin recuento» significa cero, y el servidor siempre los calcula.
         */
        VersionDiffSchema: {
            /** Added */
            added: number;
            /** Changed */
            changed: number;
            /** Document Id */
            document_id: string;
            /** From Version Id */
            from_version_id: string;
            /** Has Changes */
            has_changes: boolean;
            /** Removed */
            removed: number;
            /** Sections */
            sections: components["schemas"]["SectionDiffSchema"][];
            /** To Version Id */
            to_version_id: string;
            /** Unchanged */
            unchanged: number;
        };
        /** VersionSchema */
        VersionSchema: {
            /** Approved At */
            approved_at?: string | null;
            /** Approved By */
            approved_by?: string | null;
            /** Artifact Id */
            artifact_id: string;
            /** Content Hash */
            content_hash?: string | null;
            /**
             * Evidence Count
             * @default 0
             */
            evidence_count: number;
            /** Id */
            id: string;
            /** Is Accepted */
            is_accepted: boolean;
            /** Language */
            language?: string | null;
            /** Logical Document Id */
            logical_document_id: string;
            /** Official Url */
            official_url?: string | null;
            /** Published At */
            published_at?: string | null;
            /** Representation Id */
            representation_id?: string | null;
            /** Retrieved At */
            retrieved_at?: string | null;
            rights?: components["schemas"]["RightsSchema"] | null;
            /**
             * Section Count
             * @default 0
             */
            section_count: number;
            /**
             * Status
             * @enum {string}
             */
            status: "candidate" | "accepted" | "outdated" | "superseded" | "withdrawn" | "rejected";
            /** Supersedes Id */
            supersedes_id?: string | null;
            /** Valid From */
            valid_from?: string | null;
            /** Valid To */
            valid_to?: string | null;
            /** Version Label */
            version_label?: string | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    mark_answer_key_supersedes_api_v1_answer_keys__key_id__mark_supersedes_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                key_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkKeySupersedesRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AnswerKeySchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    classify_error_api_v1_attempts__attempt_id__error_classification_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                attempt_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ErrorClassificationSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_backups_api_v1_backups_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BackupListSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    create_backup_api_v1_backups_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateBackupSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BackupSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    verify_backup_api_v1_backups__backup_id__verify_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                backup_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VerificationSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    capabilities_api_v1_capabilities_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CapabilitiesSchema"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_change_sets_api_v1_change_sets_get: {
        parameters: {
            query?: {
                document_id?: string | null;
                status?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeSetSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_change_set_api_v1_change_sets__change_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                change_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeSetSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_change_set_affected_api_v1_change_sets__change_id__affected_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                change_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeSetSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    confirm_change_set_api_v1_change_sets__change_id__confirm_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                change_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    discard_change_set_api_v1_change_sets__change_id__discard_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                change_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    undo_decision_api_v1_classification_decisions__decision_id__undo_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                decision_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DecisionOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_proposals_api_v1_classification_proposals_get: {
        parameters: {
            query?: {
                subject_type?: string | null;
                subject_id?: string | null;
                axis?: string | null;
                status?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProposalPageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    bulk_decision_api_v1_classification_proposals_bulk_decision_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BulkDecisionRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BulkDecisionResponseSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_proposal_api_v1_classification_proposals__proposal_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProposalSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    accept_proposal_api_v1_classification_proposals__proposal_id__accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DecisionRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DecisionOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    reject_proposal_api_v1_classification_proposals__proposal_id__reject_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                proposal_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DecisionRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DecisionOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    run_classification_api_v1_classification_runs_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ClassificationReportSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    accepted_classification_api_v1_classification__subject_type___subject_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                subject_type: string;
                subject_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AcceptedClassificationSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_collections_api_v1_collections_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CollectionSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    create_collection_api_v1_collections_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateCollectionRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CollectionSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    add_collection_item_api_v1_collections__collection_id__items_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                collection_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CollectionItemRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CollectionSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_convocation_api_v1_convocations__convocation_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                convocation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConvocationDetailSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_curriculum_api_v1_convocations__convocation_id__curriculum_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                convocation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CurriculumSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    delete_mapping_api_v1_curriculum_mappings__mapping_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                mapping_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_curriculum_node_api_v1_curriculum_nodes__node_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                node_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CurriculumNodeDetailSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    node_coverage_api_v1_curriculum_nodes__node_id__coverage_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                node_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CoverageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_derived_artifacts_api_v1_derived_artifacts_get: {
        parameters: {
            query?: {
                document_version_id?: string | null;
                needs_review?: boolean | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DerivedArtifactSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    create_derived_artifact_api_v1_derived_artifacts_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateSummarySchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DerivedArtifactSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_derived_artifact_api_v1_derived_artifacts__artifact_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                artifact_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DerivedArtifactSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    resolve_derived_artifact_api_v1_derived_artifacts__artifact_id__resolution_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                artifact_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReviewArtifactSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DerivedArtifactSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_version_api_v1_document_versions__version_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VersionDetailSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_version_content_api_v1_document_versions__version_id__content_get: {
        parameters: {
            query?: {
                offset?: number;
                limit?: number;
            };
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VersionContentSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_evidence_api_v1_document_versions__version_id__evidence_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EvidenceSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_version_mappings_api_v1_document_versions__version_id__mappings_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MappingSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    add_mapping_api_v1_document_versions__version_id__mappings_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MappingRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MappingSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_version_original_api_v1_document_versions__version_id__original_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_sections_api_v1_document_versions__version_id__sections_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SectionSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_documents_api_v1_documents_get: {
        parameters: {
            query?: {
                document_type?: string | null;
                owner_scope?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DocumentPageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    promote_document_api_v1_documents_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PromoteRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PromotionOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_document_api_v1_documents__document_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DocumentDetailSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    patch_document_api_v1_documents__document_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PatchDocumentRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DocumentSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_document_diff_api_v1_documents__document_id__diff_get: {
        parameters: {
            query: {
                from_version_id: string;
                to_version_id: string;
            };
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VersionDiffSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_versions_api_v1_documents__document_id__versions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VersionSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    accept_version_api_v1_documents__document_id__versions__version_id__accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
                version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PromotionOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    mark_supersedes_api_v1_documents__document_id__versions__version_id__mark_supersedes_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
                version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkSupersedesRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PromotionOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_duplicate_clusters_api_v1_duplicate_clusters_get: {
        parameters: {
            query?: {
                status?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DuplicateClusterSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    resolve_duplicate_cluster_api_v1_duplicate_clusters__cluster_id__resolve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cluster_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResolveDuplicateRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DuplicateClusterSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_evidence_span_api_v1_evidence_spans__span_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                span_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EvidenceSpanSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_evidence_api_v1_evidence__evidence_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                evidence_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EvidenceSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    export_anki_csv_api_v1_exports_anki_csv_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExportRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExportSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    export_markdown_api_v1_exports_markdown_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExportRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExportSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    live_api_v1_health_live_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LiveSchema"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    ready_api_v1_health_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessSchema"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Alguna dependencia no está lista. Cuerpo RFC 9457 (`ReadinessProblem`) con `checks`: el detalle de cada comprobación. */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ReadinessProblem"];
                };
            };
        };
    };
    list_batches_api_v1_ingestion_batches_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    ingest_files_api_v1_ingestion_batches_files_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_ingest_files_api_v1_ingestion_batches_files_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    ingest_paste_api_v1_ingestion_batches_paste_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PasteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    ingest_url_api_v1_ingestion_batches_url_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UrlRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_batch_api_v1_ingestion_batches__batch_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchDetailSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    cancel_batch_api_v1_ingestion_batches__batch_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchSchema"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_issues_api_v1_ingestion_batches__batch_id__issues_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IssuePageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_items_api_v1_ingestion_batches__batch_id__items_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                status?: components["schemas"]["ItemStatus"] | null;
            };
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EntryPageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_report_api_v1_ingestion_batches__batch_id__report_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportReportSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_representations_api_v1_ingestion_batches__batch_id__representations_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepresentationSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    retry_batch_api_v1_ingestion_batches__batch_id__retry_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                batch_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchSchema"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description La operación no vale para el estado actual del recurso (`invalid_state`). Por ejemplo, reintentar un lote que no está fallido ni cancelado. */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    create_inventory_api_v1_inventories_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateInventoryRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InventorySchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_inventory_api_v1_inventories__inventory_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                inventory_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InventorySchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    confirm_import_api_v1_inventories__inventory_id__confirm_import_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                inventory_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BatchSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_jobs_api_v1_jobs_get: {
        parameters: {
            query?: {
                limit?: number;
                status?: components["schemas"]["JobStatus"][] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_job_api_v1_jobs__job_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    cancel_job_api_v1_jobs__job_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobSchema"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_learning_errors_api_v1_learning_errors_get: {
        parameters: {
            query?: {
                opposition_id?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConceptGroupSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_learning_error_api_v1_learning_errors__error_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                error_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorDetailSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    resolve_learning_error_api_v1_learning_errors__error_id__resolution_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                error_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResolveErrorSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ErrorSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_mappings_api_v1_mappings_get: {
        parameters: {
            query?: {
                subject_type?: string | null;
                subject_id?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MappingSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_oppositions_api_v1_oppositions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OppositionSchema"][];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_opposition_api_v1_oppositions__opposition_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                opposition_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OppositionDetailSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    activate_opposition_api_v1_oppositions__opposition_id__activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                opposition_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OppositionSchema"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_convocations_api_v1_oppositions__opposition_id__convocations_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                opposition_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConvocationReferenceSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_question_sets_api_v1_question_sets_get: {
        parameters: {
            query?: {
                opposition_id?: string | null;
                set_type?: string | null;
                include_archived?: boolean;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionSetPageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    create_question_set_api_v1_question_sets_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateQuestionSetSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionSetSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_question_set_api_v1_question_sets__set_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                set_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionSetSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_answer_keys_api_v1_question_sets__set_id__answer_keys_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                set_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AnswerKeySchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    activate_answer_key_api_v1_question_sets__set_id__answer_keys__key_id__activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                set_id: string;
                key_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AnswerKeySchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    parse_into_set_api_v1_question_sets__set_id__parse_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                set_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ParseQuestionSetSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionImportReportSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_set_questions_api_v1_question_sets__set_id__questions_get: {
        parameters: {
            query?: {
                status?: string | null;
                origin_type?: string | null;
                only_reserves?: boolean;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                set_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionPageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_questions_api_v1_questions_get: {
        parameters: {
            query?: {
                set_id?: string | null;
                status?: string | null;
                origin_type?: string | null;
                only_reserves?: boolean;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionPageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_question_api_v1_questions__question_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                question_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    patch_question_api_v1_questions__question_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                question_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PatchQuestionSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_question_evidence_api_v1_questions__question_id__evidence_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                question_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionEvidenceSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    correct_question_api_v1_questions__question_id__local_corrections_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                question_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LocalCorrectionSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CorrectionOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    report_question_issue_api_v1_questions__question_id__report_issue_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                question_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IssueReportRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IssueReportSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    ask_api_v1_rag_queries_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AskRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RagQuerySchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_rag_query_api_v1_rag_queries__query_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                query_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RagQuerySchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_rag_retrieval_api_v1_rag_queries__query_id__retrieval_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                query_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RetrievalSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_representation_api_v1_representations__representation_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                representation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepresentationSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_representation_text_api_v1_representations__representation_id__text_get: {
        parameters: {
            query?: {
                offset?: number;
                limit?: number;
            };
            header?: never;
            path: {
                representation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepresentationTextSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    execute_restore_api_v1_restore_execute_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RestoreRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RestoreResultSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    validate_restore_api_v1_restore_validate_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RestoreRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RestorePreviewSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    review_groups_api_v1_review_groups_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewGroupSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    due_reviews_api_v1_reviews_due_get: {
        parameters: {
            query?: {
                opposition_id?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewQueueSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    program_mastery_api_v1_reviews_mastery_get: {
        parameters: {
            query?: {
                opposition_id?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MasteryProgramSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_review_api_v1_reviews__review_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewItemSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    complete_review_api_v1_reviews__review_id__complete_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CompleteReviewSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewItemSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_review_history_api_v1_reviews__review_id__history_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewEventSchema"][];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    snooze_review_api_v1_reviews__review_id__snooze_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SnoozeReviewSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewItemSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    search_api_v1_search_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SearchRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SearchResultSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    read_settings_api_v1_settings_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SettingsSchema"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    list_study_sessions_api_v1_study_sessions_get: {
        parameters: {
            query?: {
                opposition_id?: string | null;
                status?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionPageSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    create_study_session_api_v1_study_sessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateSessionSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    get_study_session_api_v1_study_sessions__session_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    answer_api_v1_study_sessions__session_id__answers_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AnswerRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AnswerOutcomeSchema"];
                };
            };
            /** @description La entrada no se puede usar: carpeta inválida (`invalid_source`), contenido rechazado por seguridad (`unsafe_content`) o URL no descargable (`url_rejected`). */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Origen no autorizado para modificar datos (`forbidden_origin`). Lo produce el middleware de comprobación de Origin en métodos de escritura. */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    current_question_api_v1_study_sessions__session_id__current_question_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CurrentQuestionSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    finish_study_session_api_v1_study_sessions__session_id__finish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionResultSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    navigate_api_v1_study_sessions__session_id__navigate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NavigateRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CurrentQuestionSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    recalculate_study_session_api_v1_study_sessions__session_id__recalculate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionResultSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    study_result_api_v1_study_sessions__session_id__result_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionResultSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    study_review_api_v1_study_sessions__session_id__review_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
    start_study_session_api_v1_study_sessions__session_id__start_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionSchema"];
                };
            };
            /** @description El recurso no existe. */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Parámetros inválidos. Cuerpo RFC 9457 (`ProblemDetail`) con `field_errors`. */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["ProblemDetail"];
                };
            };
        };
    };
}

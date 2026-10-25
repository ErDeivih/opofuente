/**
 * GENERADO AUTOMÁTICAMENTE — no editar a mano.
 * Fuente: packages/contracts/openapi.json (esquema OpenAPI de FastAPI).
 * Regenerar: uv run python -m opofuente.tools.export_openapi && npm run contracts:generate
 */

export interface paths {
    "/api/v1/accounts/configuration": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * ¿Esta instalación tiene cuentas, y se puede estudiar sin ellas?
         * @description Lo que la interfaz necesita para no ofrecer un acceso que no existe.
         *
         *     **Se contesta siempre, también con las cuentas apagadas**: es justo lo que hay que poder saber
         *     antes de decidir qué enseñar.
         */
        get: operations["configuration_api_v1_accounts_configuration_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Lo que ha pasado con mi cuenta, auditado
         * @description El alta, los accesos, los cierres de sesión y la baja, cada uno con su fecha.
         */
        get: operations["events_api_v1_accounts_events_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Entrar
         * @description Comprueba la contraseña y abre sesión. El testigo sale **solo** por la cookie.
         */
        post: operations["login_api_v1_accounts_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Cerrar la sesión de esta pestaña
         * @description Cierra la sesión. Se contesta 204 aunque no hubiera nada que cerrar: es idempotente.
         */
        post: operations["logout_api_v1_accounts_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Quién soy, hasta cuándo dura esta sesión y qué ha pasado con mi cuenta
         * @description La identidad de la sesión. **Sin sesión, 401**: es la respuesta que no se puede fingir.
         */
        get: operations["me_api_v1_accounts_me_get"];
        put?: never;
        post?: never;
        /**
         * Cerrar la cuenta y borrar sus datos
         * @description Da de baja la cuenta: borra lo suyo y deja constancia.
         *
         *     Se devuelve **cuánto** se ha borrado de cada cosa: un «hecho» sin cifra no dice nada, y quien
         *     ejerce el derecho de supresión tiene derecho a saber qué se ha ido.
         */
        delete: operations["close_account_api_v1_accounts_me_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/password-resets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pedir un enlace para cambiar la contraseña
         * @description Crea el enlace. **La respuesta no dice si la dirección tiene cuenta.**
         */
        post: operations["request_reset_api_v1_accounts_password_resets_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/password-resets/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Cambiar la contraseña con el enlace
         * @description Cambia la contraseña y **cierra las demás sesiones**: si no, el cambio no echa a nadie.
         */
        post: operations["confirm_reset_api_v1_accounts_password_resets_confirm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Darse de alta
         * @description Da de alta una cuenta. **La respuesta no dice si la dirección ya estaba.**
         *
         *     Se contesta 202 y no 201 a propósito: aceptado no es creado, y quien pregunta no tiene por qué
         *     saber cuál de las dos cosas ha pasado. La cuenta, si es nueva, queda lista para entrar sin
         *     confirmar el correo: sin servicio de correo contratado no hay forma de confirmarlo, y fingir que
         *     se ha mandado un mensaje dejaría a quien se registra esperando algo que no va a llegar.
         */
        post: operations["register_api_v1_accounts_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Mis sesiones abiertas */
        get: operations["sessions_api_v1_accounts_sessions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/accounts/sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * Cerrar otra sesión mía
         * @description Cierra otra sesión. **Nunca la que se está usando**: eso dejaría fuera a quien lo pide.
         */
        delete: operations["revoke_session_api_v1_accounts_sessions__session_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/analytics/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Contar una pantalla vista o una acción (necesita consentimiento)
         * @description Cuenta un suceso **si** está encendida la analítica y **si** hay consentimiento.
         *
         *     El permiso se lee aquí, de la cookie, y no se acepta del cuerpo: si el permiso viajara en la
         *     petición, bastaría con mandarlo para contar lo que no se puede contar.
         */
        post: operations["record_event_api_v1_analytics_events_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/analytics/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Lo contado, agrupado por etiqueta y por día
         * @description El resumen va agregado: no se pueden pedir los sucesos uno a uno, porque no tienen sujeto.
         */
        get: operations["analytics_summary_api_v1_analytics_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
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
    "/api/v1/cards/pending": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Cuántas tarjetas vencen hoy (M3)
         * @description El número de vencidas, **sin traerlas**: la cola lo enseña antes de empezar.
         */
        get: operations["pending_cards_api_v1_cards_pending_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/cards/queue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * La cola del día: las tarjetas que vencen (M3)
         * @description Las tarjetas vencidas, entrelazadas y con el tope del día.
         *
         *     **`total` es el de vencidas, no el de la página**: es lo que le queda al alumno,
         *     y contar solo lo que cabe en la pantalla mentiría hacia abajo.
         */
        get: operations["card_queue_api_v1_cards_queue_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/cards/queue/failures/{question_version_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Corrige un fallo de la cola del día y devuelve su explicación (punto 3)
         * @description **Corrige una pregunta suelta**, sin montar una sesión entera.
         *
         *     **Por qué existe**: los fallos vencidos entran en la cola del día como preguntas de test, y
         *     contestarlas pedía una sesión —`/student/sessions/{id}/answers`— que para una pregunta es un
         *     rodeo. **La clave no viaja al cliente**: se compara aquí.
         *
         *     **La explicación se devuelve con la corrección**, y solo entonces: antes filtraría la respuesta.
         */
        post: operations["answer_due_failure_api_v1_cards_queue_failures__question_version_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/cards/{card_id}/answer": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Responde una tarjeta y devuelve cuándo vuelve (M3)
         * @description Aplica SM-2 y devuelve la tarjeta **con su nueva fecha de vuelta**.
         *
         *     **404 si no existe**: un `True`/`False` no le dice nada al alumno sobre qué
         *     pasó con la tarjeta que acaba de contestar.
         */
        post: operations["answer_card_api_v1_cards__card_id__answer_post"];
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
        /**
         * Encola una pasada de clasificación del corpus (idempotente)
         * @description Clasificar dejó de ser una petición larga: se **encola** y se sigue por su trabajo.
         *
         *     Con el material real del propietario una pasada tarda 46,7 segundos: tener eso dentro de una
         *     petición dejaba el botón bloqueado sin decir en qué iba (DEBT-024). Ahora responde **202** con
         *     el trabajo recién encolado —su `step` dirá el resumen al terminar— y la pantalla lo sigue.
         *
         *     Si ya hay una pasada viva, devuelve **esa**: pulsar dos veces no clasifica dos veces.
         */
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
        /**
         * Quita un sujeto de una colección (ruta añadida: no existe en el contrato)
         * @description Saca un sujeto de la colección **sin borrar nada del sujeto**.
         *
         *     Ruta **añadida** al contrato: §7 no la lista, y sin ella una colección solo se podía llenar. No
         *     pide confirmación porque no retira material —el documento, la versión o la cita siguen donde
         *     estaban— y es idempotente: quitar lo que no estaba devuelve la colección como está.
         */
        delete: operations["remove_collection_item_api_v1_collections__collection_id__items_delete"];
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
    "/api/v1/convocations/{convocation_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Convierte una convocatoria en la vigente de su oposición
         * @description Elige con qué convocatoria trabaja la aplicación.
         *
         *     La vigente anterior queda «superada» (sigue visible y se puede volver a ella). Se rechaza con
         *     409 si la convocatoria está en borrador, archivada o no tiene programa sembrado: la aplicación
         *     no ofrece como vigente algo que no puede mostrar.
         */
        post: operations["activate_convocation_api_v1_convocations__convocation_id__activate_post"];
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
    "/api/v1/curriculum-nodes/{node_id}/dossier": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Dossier del tema: los pasajes que lo sostienen, citados, y lo que falta
         * @description Lo que el corpus dice hoy de este tema, con la procedencia de cada cita.
         *
         *     Incluye los temas que cuelgan de él (el ámbito de un bloque es su subárbol) y **no** incluye
         *     nada
         *     que no se pueda citar: una versión sin aceptar o un texto pobre se declaran como huecos con su
         *     motivo, en lugar de aparecer como si fueran material bueno.
         */
        get: operations["node_dossier_api_v1_curriculum_nodes__node_id__dossier_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/curriculum-nodes/{node_id}/dossier/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Versiones guardadas del dossier, de la más nueva a la más antigua */
        get: operations["list_dossier_versions_api_v1_curriculum_nodes__node_id__dossier_versions_get"];
        put?: never;
        /**
         * Archiva la lectura actual del tema como una versión del dossier
         * @description Guarda lo que el tema dice hoy, para poder compararlo con lo que diga mañana.
         *
         *     Si la lectura no ha cambiado desde la última versión guardada, no se crea otra: se devuelve la
         *     que
         *     ya estaba con `created: false`. Eso es lo que permite decir «esto es lo que sabía antes y esto
         *     lo
         *     que sé ahora» sin que el historial se llene de copias idénticas.
         */
        post: operations["archive_dossier_api_v1_curriculum_nodes__node_id__dossier_versions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/curriculum-nodes/{node_id}/dossier/versions/{version_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Una versión guardada del dossier, tal como se leyó entonces */
        get: operations["get_dossier_version_api_v1_curriculum_nodes__node_id__dossier_versions__version_id__get"];
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
    "/api/v1/diagnostics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Diagnóstico sanitizado para pegar en una incidencia (sin secretos ni contenido)
         * @description Versiones, capacidades, salud, recuentos, límites y el final del registro, todo saneado.
         *
         *     No es un volcado: es lo que hace falta para juzgar el estado sin publicar nada del usuario. Las
         *     rutas van abreviadas y cada línea del registro pasa por el saneado de secretos y rutas.
         */
        get: operations["diagnostics_api_v1_diagnostics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/diagnostics/text": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** El mismo diagnóstico en texto plano, para copiar y pegar */
        get: operations["diagnostics_text_api_v1_diagnostics_text_get"];
        put?: never;
        post?: never;
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
        /**
         * Biblioteca: documentos con su versión activa
         * @description Documentos de la biblioteca con su versión activa.
         *
         *     `collection_id` filtra por colección (07_UI-UX §6), y el filtro se aplica en el servidor: la
         *     pantalla no se trae la biblioteca entera para descartarla después.
         */
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
        /**
         * Acepta una versión (promoción crítica, confirmada y auditada)
         * @description Acepta la versión y, después, la aplicación hace sola lo que se puede hacer sola.
         *
         *     Aceptar una versión es un acto de una persona (ADR-009) y sigue pidiendo un clic. Lo que
         *     va detrás —leer el material, ver qué es, **importar sus preguntas con su cita** y catalogarlas
         *     por bloque y tema— no necesita a nadie, así que ocurre aquí y se cuenta en la respuesta (S12.5 y
         *     S12.6, ADR-017). Si el material no trae preguntas, no está clasificado o no está asignado a
         *     ninguna oposición, se dice con su motivo en lugar de callarlo.
         */
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
    "/api/v1/documents/{document_id}/versions/{version_id}/reinstate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Repone una versión retirada como candidata (para usarla hay que aceptarla) */
        post: operations["reinstate_version_api_v1_documents__document_id__versions__version_id__reinstate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/documents/{document_id}/versions/{version_id}/withdraw": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Retira una versión: deja de buscarse y citarse, y no se borra
         * @description Para el material obsoleto sin sustituta en el mismo documento. Se deshace con `reinstate`.
         */
        post: operations["withdraw_version_api_v1_documents__document_id__versions__version_id__withdraw_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/documents/{document_id}/withdraw": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Archiva un documento: retira todas sus versiones vivas, sin borrar nada */
        post: operations["withdraw_document_api_v1_documents__document_id__withdraw_post"];
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
    "/api/v1/explanations/pending": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * La bandeja de explicaciones generadas: lo que falta por revisar (M1 de la fase 3)
         * @description Las explicaciones **generadas y en borrador**, por antigüedad, con su pregunta.
         *
         *     Es la cola de trabajo del propietario: **no aparecen las privadas ni las oficiales**, porque no
         *     las escribió un modelo y no hay nada que aprobar. El enunciado viaja con cada fila para que se
         *     pueda decidir sin abrir otra pantalla.
         */
        get: operations["list_pending_explanations_api_v1_explanations_pending_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/explanations/{explanation_id}/regenerate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pide al modelo una explicación nueva para la misma pregunta (M1 de la fase 3)
         * @description Regenera una explicación: **la pide al modelo, la comprueba y solo entonces la sustituye**.
         *
         *     **Si no pasa las comprobaciones, la vieja se queda**: regenerar no es empeorar. **Y si falta la
         *     clave, esto responde 503**: la bandeja funciona sin modelo salvo esta acción, y decirlo es más
         *     útil que fingir que la llamada ha fallado por otra cosa.
         *
         *     **Gasta**: una llamada al modelo por explicación, ~0,000024 $ con los datos de esta fase.
         */
        post: operations["regenerate_explanation_api_v1_explanations__explanation_id__regenerate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/explanations/{explanation_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Aprobar o rechazar una explicación generada (M1 de la fase 3)
         * @description Aprobar o rechazar una explicación de la bandeja.
         *
         *     **Solo cambia el estado.** El texto y la cita se corrigen por la ruta de escribir
         *     explicaciones, y **regenerar** es otra cosa: pide al modelo una nueva y gasta, así que no
         *     se esconde detrás de un cambio de estado.
         */
        patch: operations["set_explanation_status_api_v1_explanations__explanation_id__status_patch"];
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
    "/api/v1/housekeeping": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Qué ocupa el almacén y qué se puede retirar (no escribe nada) */
        get: operations["housekeeping_report_api_v1_housekeeping_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/housekeeping/old-jobs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retira del historial los trabajos terminados y antiguos */
        post: operations["purge_old_jobs_api_v1_housekeeping_old_jobs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/housekeeping/orphan-artifacts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retira artefactos sin origen ni documento que los use */
        post: operations["purge_orphan_artifacts_api_v1_housekeeping_orphan_artifacts_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/housekeeping/temps": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retira temporales de operaciones interrumpidas */
        post: operations["purge_temps_api_v1_housekeeping_temps_post"];
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
    "/api/v1/ingestion-batches/{batch_id}/pause": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pausa el lote: deja de avanzar sin perder lo hecho; 409 si ya terminó
         * @description Pausar no es cancelar: lo copiado sigue copiado y el lote se reanuda (DEBT-027 §4).
         */
        post: operations["pause_batch_api_v1_ingestion_batches__batch_id__pause_post"];
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
    "/api/v1/ingestion-batches/{batch_id}/resume": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reanuda un lote en pausa y lo devuelve a la cola; 409 si no está en pausa */
        post: operations["resume_batch_api_v1_ingestion_batches__batch_id__resume_post"];
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
    "/api/v1/invitations/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Canjea una invitacion y crea la cuenta (M8)
         * @description **Un solo uso, con caducidad y para una direccion**: lo comprueba `canjear`.
         *
         *     **La contrasena entra por el cuerpo y no se registra en ningun sitio**:
         *     **el log de una peticion no es lugar para un secreto.**
         */
        post: operations["accept_invitation_api_v1_invitations_accept_post"];
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
    "/api/v1/legal/consent": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Qué he decidido sobre las cookies (o nada, si no lo he decidido)
         * @description `null` significa **sin decidir**, que no es lo mismo que haber rechazado.
         */
        get: operations["read_consent_api_v1_legal_consent_get"];
        put?: never;
        /**
         * Decidir sobre las cookies (aceptar o rechazar, con el mismo cuerpo)
         * @description Guarda la decisión en una cookie propia y deja constancia agregada, sin sujeto.
         *
         *     El cuerpo es el mismo para aceptar y para rechazar: dos booleanos. No hay ninguna ruta «fácil»
         *     para aceptar ni ningún camino que exija explicar un rechazo.
         */
        post: operations["decide_consent_api_v1_legal_consent_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/consent/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Cuántas decisiones se han tomado, sin decir quién
         * @description La constancia agregada: demuestra que se preguntó, sin un registro de nadie.
         */
        get: operations["consent_summary_api_v1_legal_consent_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/cookies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Qué cookies se ponen y cuáles son necesarias */
        get: operations["cookies_api_v1_legal_cookies_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/data-inventory": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Qué datos se recogen, para qué, dónde y cuánto tiempo
         * @description El inventario **verificable**: la prueba de integración lo cruza contra el esquema real.
         *
         *     Cada fila dice de qué tabla habla, y la prueba comprueba que esa tabla y esa columna existen.
         *     También comprueba lo que el inventario dice que **no** se recoge: si alguien añadiera mañana una
         *     columna de dirección de red, la prueba fallaría y este texto dejaría de poder mentir.
         */
        get: operations["data_inventory_api_v1_legal_data_inventory_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Los tres textos legales, con lo que falta por rellenar
         * @description Aviso legal, privacidad y cookies, tal como se leen en la aplicación.
         */
        get: operations["documents_api_v1_legal_documents_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/documents/{key}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Un texto legal por su nombre corto */
        get: operations["one_document_api_v1_legal_documents__key__get"];
        put?: never;
        post?: never;
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
    "/api/v1/notes-incidents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Las incidencias del motor, para la bandeja del propietario
         * @description Las incidencias, de la más nueva a la más vieja.
         *
         *     `pending` cuenta las que están **sin despachar** (`open`) sin mirar el filtro: es el número que
         *     el propietario necesita ver aunque esté mirando las de una sola categoría. `totals_by_category`
         *     cuenta las cuatro categorías **en la base entera**, con un `GROUP BY`: es la cifra de cada
         *     clase,
         *     medida y no heredada. El `total`, en cambio, es el del filtro.
         *
         *     `set` es el filtro que **despliega** una fila de la bandeja agrupada (F31): la fila de un
         *     conjunto no enseña sus incidencias dentro, las pide por aquí.
         */
        get: operations["list_notes_incidents_api_v1_notes_incidents_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-incidents/tray": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Una hoja de la bandeja por conjunto, con lo que admite en bloque
         * @description Una hoja de la bandeja agrupada por conjunto, con lo oficial **aparte y arriba**.
         *
         *     Es la vista con la que se trabaja: una fila por conjunto, su resumen («50 claves sospechosas»),
         *     las acciones que admite y **la cifra** que decide si la bandeja sirve —las entradas que de
         *     verdad dependen del criterio del propietario—. Los conjuntos oficiales van en su propia sección
         *     porque sus incidencias no se deciden en bloque: su clave es la que publicó la administración.
         *
         *     Se cuenta en la base, no en la pantalla: `entradas_de_decision` sale del dominio y viaja
         *     calculado, para que no haya dos versiones de la cifra que mide la medida de éxito. Y **los
         *     totales son de la bandeja entera**: pasar de hoja no cambia cuántas filas hay ni cuánto queda.
         */
        get: operations["read_tray_api_v1_notes_incidents_tray_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-incidents/tray/actions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Qué hace cada acción en bloque, dicho por el servidor
         * @description El texto de las tres acciones, calculado en el servidor.
         *
         *     Vive aquí y no en la pantalla por la misma razón que `category_help`: dos versiones del mismo
         *     texto acaban diciendo cosas distintas, y la que se queda vieja es la que nadie lee.
         */
        get: operations["read_tray_actions_api_v1_notes_incidents_tray_actions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-incidents/tray/bulk": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Aplica una acción en bloque a un conjunto (y rechaza los oficiales)
         * @description Acepta todas las derivadas, deja el conjunto fuera o lo marca como «no son preguntas».
         *
         *     **Una clave oficial no se cambia jamás**: si el conjunto es un examen oficial —o su plantilla
         *     viene de un documento—, la ruta **rechaza** la acción con el motivo que ya usa la ficha de la
         *     pregunta, y no escribe nada. El rechazo es un `409` con el texto, no un 200 que no hizo nada.
         *
         *     Aplicar dos veces la misma acción no duplica nada: la segunda pasada no encuentra incidencias
         *     esperando y devuelve cero. La memoria de lo hecho **es** el estado de la incidencia.
         */
        post: operations["dispatch_tray_bulk_api_v1_notes_incidents_tray_bulk_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-incidents/{incident_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Despacha una incidencia: en curso, resuelta o descartada, con la nota de lo decidido
         * @description Cambia el estado de una incidencia y, si se escribe, deja la nota de lo que se ha decidido.
         *
         *     No hay ruta para borrar una incidencia: lo que señaló el motor no se tira, se despacha. Una
         *     incidencia que no existe es un 404 con su identificador, y una nota de más de una línea se
         *     recorta antes de guardarse.
         */
        patch: operations["update_notes_incident_api_v1_notes_incidents__incident_id__patch"];
        trace?: never;
    };
    "/api/v1/notes-reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Los avisos del alumno sobre los apuntes, para la bandeja del propietario
         * @description Los avisos, del más nuevo al más viejo.
         *
         *     `pending` cuenta los que están **sin despachar** (`open`) sin mirar el filtro: es el número que
         *     el propietario necesita ver aunque esté mirando los de un solo tema. Los otros tres recuentos y
         *     el `total` del filtro salen de la base, no de la página que se devuelve.
         */
        get: operations["list_note_reports_api_v1_notes_reports_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-reports/{report_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Despacha un aviso: en curso, resuelto o descartado, con la nota de lo que se ha hecho
         * @description Cambia el estado de un aviso y, si se escribe, deja la nota de lo que se ha hecho.
         *
         *     No hay ruta para borrar un aviso: lo que el alumno marcó como mal no se tira, se despacha. Un
         *     aviso que no existe es un 404 con su identificador, y una nota de más de una línea se recorta
         *     antes de guardarse.
         */
        patch: operations["update_note_report_api_v1_notes_reports__report_id__patch"];
        trace?: never;
    };
    "/api/v1/notes-review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Los temas con su estado, sus puertas y el motivo de los que están en borrador
         * @description La tabla del panel: los temas del programa activo, en orden, con lo que se sabe **sin
         *     medir**.
         *
         *     **No mide** ningún tema: lee el estado, las cifras guardadas y la decisión escrita con cinco
         *     consultas agregadas (0,03 s medidos sobre la copia del propietario, 17-oct-2026). Medir los dos
         *     borradores costaba 3,7 s de los 5,37 s de la pantalla, y la cifra de la puerta **no se hereda**:
         *     se mide al abrir la ficha del tema, que es donde se decide, y la fila lo dice con la razón
         *     `sin_medida` en vez de enseñar un cero que parecería un suspenso.
         */
        get: operations["list_notes_review_api_v1_notes_review_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-review/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Cuántos borradores esperan una decisión (el número del menú, sin medir nada)
         * @description Los contadores del menú. No mide la cobertura de nada: se pide en todas las pantallas.
         */
        get: operations["notes_review_summary_api_v1_notes_review_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-review/{codigo}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Una página de la ficha: sus apartados, como se leerán en la zona del alumno
         * @description Una **página** de un tema, apartado a apartado, con su texto, su forma y lo comprobado.
         *
         *     Un tema sin apuntes escritos sale con su estado (`none`) y sin apartados: no es un error que un
         *     tema no tenga texto, y devolver un 404 obligaría a la pantalla a distinguir «no existe» de «no
         *     está escrito», que es justo lo que el estado contesta.
         *
         *     El orden lo decide el servidor porque la página se corta aquí: «los peores primero» ordena los
         *     apartados del **tema**, no los de la hoja que se acaba de enviar.
         */
        get: operations["notes_review_file_api_v1_notes_review__codigo__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/notes-review/{codigo}/decision": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Aprueba o rechaza los apuntes de un tema, con su nota y su evento de auditoría
         * @description Aprueba (y publica, si las puertas pasan) o rechaza el texto de un tema.
         *
         *     Aprobar **no salta el listón**: si la cobertura del §2.3 no llega, el tema queda aprobado y sin
         *     publicar, y `blocked_by` dice qué puerta lo frena con su cifra en el motivo. Rechazar exige
         *     motivo, y una nota de más de una línea se recorta a una.
         */
        post: operations["decide_notes_review_api_v1_notes_review__codigo__decision_post"];
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
    "/api/v1/oppositions/{opposition_id}/readiness": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * ¿Está esta oposición lista para estudiar, y qué falta?
         * @description Material por papel, preguntas por tema y claves activas, con lo que falta en palabras.
         */
        get: operations["get_readiness_api_v1_oppositions__opposition_id__readiness_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/payments/plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El hueco de pagos: qué hay contratado (nada) y qué habría que contratar
         * @description **No cobra nada y no puede cobrar nada.**
         *
         *     Con la bandera apagada —que es como nace— la respuesta dice que no está disponible y, aun así,
         *     trae la propuesta escrita: qué pasarela, por qué, qué habría que contratar, qué costaría y qué
         *     datos personales pasarían a un tercero. Es la respuesta al §11 sin contratar nada.
         */
        get: operations["payment_plans_api_v1_payments_plans_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/pending-actions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Lo que sigue esperando una decisión de una persona
         * @description Incidencias de importación, propuestas de clasificación, cambios y material sin aceptar.
         */
        get: operations["get_pending_actions_api_v1_pending_actions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/plan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Lo que hay guardado del plan (M4)
         * @description La fecha y las horas, **o `null` si no hay plan**. No calcula nada.
         */
        get: operations["leer_guardado_api_v1_plan_get"];
        /**
         * Pone la fecha del examen y devuelve el plan (M4)
         * @description Guarda la fecha y **devuelve el plan calculado**, que es lo que la
         *     pantalla necesita para pintarlo sin pedirlo otra vez.
         *
         *     **404 si no hay temas que repartir**: un plan vacio no es un plan.
         */
        put: operations["guardar_plan_api_v1_plan_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/plan/hoy": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Lo que toca hoy, recortado de la semana en curso (M4)
         * @description Las tareas de esta semana, **o el motivo de que no haya ninguna**.
         */
        get: operations["plan_de_hoy_api_v1_plan_hoy_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/plan/progreso": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Vas bien o vas retrasado, con la cifra (M4)
         * @description Los temas leidos y practicados **frente a los que el plan pedia**.
         *
         *     **404 si no hay plan**: sin fecha no hay con que comparar, y decir «vas
         *     bien» sin plan seria mentir.
         */
        get: operations["progreso_api_v1_plan_progreso_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/platform/policy": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Qué funciones están encendidas en esta instalación
         * @description La única llamada que necesita la interfaz para saber con qué configuración habla.
         *
         *     Es pública: dice qué está encendido, no nada de nadie. Existe porque la web se construye una vez
         *     y se sirve en varias configuraciones; con las banderas dentro del paquete habría que construir
         *     dos
         *     veces la misma aplicación para probar la versión con cuentas y la versión sin ellas, y las dos
         *     acabarían divergiendo.
         */
        get: operations["platform_policy_api_v1_platform_policy_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-exclusions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Las preguntas fuera de temario, con su motivo (la cola que revisa el propietario)
         * @description Las marcas de fuera de temario, de la más nueva a la más antigua.
         *
         *     Es donde se **consulta** lo que no es materia del programa: la pregunta, el motivo por el que
         *     se declaró y quién lo decidió. Va como recurso propio (`/question-exclusions`) y no dentro de la
         *     pregunta a propósito: una marca no es un tema, y meterla en el mismo sitio invitaría a leerla
         *     como si lo fuera. La revisión de una marca se hace asignando un tema (que la levanta) o
         *     dejándola.
         *
         *     `q` filtra por el enunciado: la sección «No son preguntas» del panel (F16, decisión D6) enseña
         *     los enunciados rotos, y con 769 en la base hay que poder buscar el que se tiene en la cabeza.
         */
        get: operations["list_question_exclusions_api_v1_question_exclusions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-files/{question_version_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * La ficha de una pregunta: su clave, de dónde sale, los apuntes y qué se puede hacer
         * @description Todo lo que hace falta para decidir una clave, en una sola lectura.
         *
         *         Es la pantalla que faltaba detrás de dos enlaces que ya existían: el de la bandeja del motor
         *         y
         *     el
         *         del banco. Sin ella, «clave sospechosa» era un enlace a una dirección sin ficha donde
         *     arreglarla.
         */
        get: operations["get_question_file_api_v1_question_files__question_version_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-files/{question_version_id}/answer-key": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Marca la respuesta correcta, por la ruta auditada (la anterior queda en el historial)
         * @description Cambia la respuesta correcta escribiendo una **plantilla nueva** del conjunto.
         *
         *         Lo que garantiza y se puede comprobar después:
         *
         *         - la plantilla que mandaba pasa a `superseded` y la nueva la apunta con `supersedes_id`:
         *         **no se
         *           pisa** nada, y el historial de la ficha enseña las dos con la letra que cada una daba a
         *           esta
         *           pregunta;
         *         - el estado se conserva: una plantilla activa se sustituye por otra activa (si no, marcar la
         *           correcta no cambiaría la corrección y la pantalla mentiría) y una en borrador por otra en
         *           borrador;
         *         - **una clave oficial no se toca**: si el conjunto es un examen oficial —o su plantilla
         *         viene de
         *     un
         *           documento, que es el otro camino a «oficial»— la respuesta es un **409 con el motivo** y
         *           no se
         *           escribe nada. Los conjuntos protegidos viajan en la ficha, con su nombre, para que no haya
         *           que
         *           adivinar cuál estorba;
         *         - una letra que la pregunta no tiene es un **422** con el campo, antes de tocar la base;
         *         - el antes, el después y el actor van en el mismo evento de auditoría y en la misma
         *         transacción
         *     que
         *           la plantilla.
         */
        post: operations["mark_correct_option_api_v1_question_files__question_version_id__answer_key_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-files/{question_version_id}/repairs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Repara lo que una regla mecánica pueda reparar, escribiendo una versión nueva
         * @description Escribe la versión nueva de la pregunta con lo que una regla mecánica puede arreglar.
         *
         *         Solo hay dos reglas y las dos salen del §2 de los ajustes: quitar del enunciado la
         *         referencia
         *     del
         *         examen que quedó pegada al final y partir una opción que se tragó a la siguiente. Lo que no
         *         se
         *         pueda reparar con una regla **no se toca**: la ficha dice por qué y esta ruta lo repite con
         *         un
         *     409,
         *         en vez de escribir una versión con texto inventado.
         *
         *         Y al reparar, el **sitio** de la pregunta viaja con ella: sus temas, sus anclas de apuntes y
         *         su
         *         marca de fuera de temario se mudan a la versión nueva. Sin eso, limpiar un enunciado sacaría
         *         la
         *         pregunta del temario y de la cobertura de los apuntes en silencio, que es un cambio mucho
         *         mayor
         *     que
         *         el que se ha pedido.
         *
         *         Las incidencias de la pregunta se despachan como **resueltas** por la ruta auditada de la
         *     bandeja,
         *         con la nota de lo hecho: una bandeja que siguiera enseñando una pregunta ya reparada
         *         mentiría.
         */
        post: operations["repair_question_api_v1_question_files__question_version_id__repairs_post"];
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
        /**
         * Cambia quién puede ver un conjunto (personal o public) y de dónde sale
         * @description `personal` es material del propietario; `public`, publicable. `origin_scope`, de dónde sale.
         *
         *     Un conjunto **nace** `personal` y solo se hace `public` a propósito, uno a uno: el material que
         *     el propietario ha reunido no se hace visible por descuido. La procedencia se declara por el
         *     mismo camino y por la misma razón: marcar un conjunto como de otra administración lo deja fuera
         *     de los simulacros, y eso es una decisión que tiene que quedar auditada. El actor viaja a la
         *     auditoría. Los dos campos son opcionales, pero al menos uno tiene que venir.
         */
        patch: operations["update_question_set_api_v1_question_sets__set_id__patch"];
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
    "/api/v1/question-sets/{set_id}/answer-keys/{key_id}/source": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Enlaza (o desenlaza) la plantilla oficial de una clave que ya existe
         * @description Antes, el enlace solo se hacía al aceptar la versión de la plantilla: un examen importado
         *     después se quedaba con su clave oficial sin poder activarse. Enlazar exige que la plantilla
         *     diga lo mismo que la clave, pregunta a pregunta; si no, 409 con lo que no coincide.
         */
        post: operations["link_answer_key_source_api_v1_question_sets__set_id__answer_keys__key_id__source_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets/{set_id}/import-document": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Importa las preguntas de una versión de documento (ruta añadida: DEBT-010)
         * @description Las preguntas de un documento de la biblioteca, con la cita de dónde salió cada una.
         *
         *     Ruta **añadida** al contrato §9 y registrada en ADR-013. Es la mitad que faltaba del importador
         *     (04_INGESTION §10: «parser desde texto/**documento**»): hasta ahora solo entraba texto suelto,
         *     así que una pregunta nacida de un documento no podía enseñar su cita ni abrir el original.
         *
         *     Después de importar se **cataloga**: cada pregunta hereda el programa del documento del que sale
         *     (S12.6), igual que cuando la importación la hace la aplicación sola al aceptar una versión. Sin
         *     ese paso, las preguntas importadas a mano se quedarían fuera del diagnóstico por temas.
         *
         *     Lo que **no** hace: inventar la cita. Si la versión no tiene fragmentos extraídos no hay de
         *     dónde citar, y el informe lo dice con una incidencia en lugar de crear una evidencia vacía.
         */
        post: operations["import_from_document_api_v1_question_sets__set_id__import_document_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-sets/{set_id}/outdated-sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Sesiones terminadas sin corregir con la plantilla activa (ruta añadida: DEBT-013)
         * @description Cuántas sesiones quedan desactualizadas tras activar una plantilla nueva.
         *
         *     Es la lectura que faltaba: `POST /question-sets/{set_id}/recalculate-sessions` dice qué cambió
         *     **después** de recalcular, y esto dice qué hace falta **antes**. Activar una clave corregida sin
         *     recalcular no cambiaba ninguna nota y no se notaba en ninguna pantalla.
         */
        get: operations["outdated_sessions_api_v1_question_sets__set_id__outdated_sessions_get"];
        put?: never;
        post?: never;
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
    "/api/v1/question-sets/{set_id}/recalculate-sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Recalcula en bloque las sesiones terminadas de un conjunto (DEBT-013)
         * @description Corregir una clave y recalcular **todas** las sesiones afectadas de una vez.
         *
         *     Va aquí y no en `/study-sessions/{id}/recalculate` porque el ámbito es el **conjunto**: lo que
         *     se corrige es su plantilla, y lo que hay que arreglar son las sesiones que se corrigieron con
         *     ella. El informe dice sesión por sesión qué cambió y cuánto: un «hecho» sin números no se puede
         *     comprobar.
         */
        post: operations["recalculate_set_api_v1_question_sets__set_id__recalculate_sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-topic-conflicts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Las preguntas que cuentan en dos temas aceptados, con quién decidió cada uno
         * @description Las preguntas que cuentan en **dos o más temas decididos** a la vez.
         *
         *     No es una curiosidad: una pregunta en dos temas suma en los dos en todos los recuentos del
         *     alumno y en la cobertura, así que mientras exista, esas cifras mienten. Vienen de antes de esta
         *     tanda —la catalogación heredada del documento, las migraciones— y de dos corridas del
         *     clasificador que se pisaron; por eso cada tema viaja con **quién lo decidió**, que es lo que
         *     permite juzgar cuál se queda.
         *
         *     Se resuelve con la misma ruta por lotes que la cola: una fila con el tema elegido, `status`
         *     `accepted` y `retire_others` deja la pregunta con ese tema y retira los demás. La aplicación no
         *     elige: si nadie decide, no se toca nada.
         */
        get: operations["list_question_topic_conflicts_api_v1_question_topic_conflicts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/question-topic-proposals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Las propuestas de tema sin confirmar, con la pregunta (la cola de revisión del panel)
         * @description Lo que el clasificador propuso con dudas (`provisional`) y nadie ha decidido todavía.
         *
         *     Es la lectura de la cola que despacha el propietario con el teclado, y por eso trae la pregunta
         *     **entera** —enunciado y opciones— junto al tema y los epígrafes propuestos, la confianza y el
         *     motivo del modelo: sin el texto delante, una propuesta no se puede juzgar, y sin la confianza no
         *     se sabe cuánto dudó quien la hizo.
         *
         *     Va como recurso propio y no dentro de `GET /questions/{id}/topics` porque una propuesta no es
         *     «los temas de una pregunta»: es **una cola**, se pagina como tal, y su total lo cuenta el
         *     servidor. Van de la más dudosa a la menos, y el motivo sale de la auditoría, que es donde vive.
         *
         *     Se despacha con `POST /questions/topics/bulk`: una fila por propuesta con su `status`
         *     (`accepted`) la confirma, otra con otro tema la corrige, y `exclusion_reason` la deja fuera de
         *     temario. No hay una ruta de escritura propia para esto a propósito: la propuesta se decide por
         *     el mismo camino auditado por el que se asignan los temas.
         */
        get: operations["list_question_topic_proposals_api_v1_question_topic_proposals_get"];
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
    "/api/v1/questions/topics/bulk": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Asigna temas por lotes: misma ruta auditada, idempotente y fila a fila
         * @description La versión por lotes de `POST /questions/{id}/topics`, para no hacer 17.000 peticiones.
         *
         *     No es un segundo camino de escritura: cada fila entra por el mismo método del servicio, así
         *     que deja **el mismo mapeo y el mismo evento de auditoría** que la ruta individual. Lo que añade
         *     es el sobre: un actor para todo el lote y, por fila, o un tema (con su epígrafe) o un fuera de
         *     temario.
         *
         *     Es **idempotente**: repetir un lote no duplica mapeos ni eventos, y cada fila dice si la creó
         *     esta llamada (`created`) o si ya estaba (`existing`). Una fila mala **no** tumba el lote: se
         *     devuelve con `outcome="error"` y su motivo, y las demás se aplican. Abortar 200 asignaciones
         *     porque una pregunta se retiró entre medias obligaría a repetir las 199 buenas.
         *
         *     El actor viaja en el cuerpo (`actor`) o en la cabecera `X-OpoFuente-Actor`. La clasificación
         *     automática se identifica (`llm:deepseek-flash`) y así la auditoría distingue a la persona del
         *     proceso.
         */
        post: operations["assign_question_topics_bulk_api_v1_questions_topics_bulk_post"];
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
    "/api/v1/questions/{question_id}/explanations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Explicaciones de la pregunta y de cada una de sus opciones (ruta añadida: S12.7)
         * @description La explicación de la pregunta entera y la de cada opción, con su clave de opción.
         *
         *     Se sirven **todas juntas**: quien lee quiere entender la pregunta, y separarlas obligaría a la
         *     interfaz a juntarlas otra vez (07_UI-UX §7).
         */
        get: operations["list_question_explanations_api_v1_questions__question_id__explanations_get"];
        put?: never;
        /**
         * Escribe la explicación de la pregunta o de una de sus opciones (ruta añadida: S12.7)
         * @description Escribe o **sustituye** la explicación de ese hueco: la identidad es (pregunta, opción).
         *
         *     Una opción que la pregunta no tiene es un 409 con el motivo, no una explicación huérfana: la
         *     explicación de una opción que no está no explica nada.
         */
        post: operations["set_question_explanation_api_v1_questions__question_id__explanations_post"];
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
    "/api/v1/questions/{question_version_id}/topics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Temas asignados a una pregunta, con el estado de cada mapeo
         * @description Los temas de la pregunta, cada uno con el estado de su mapeo.
         *
         *     Se sirven todos los mapeos, no solo los aceptados: quien administra tiene que ver también lo que
         *     propuso un motor y nadie ha confirmado. El estado va en cada uno para que la diferencia se lea
         *     sin adivinar.
         */
        get: operations["list_question_topics_api_v1_questions__question_version_id__topics_get"];
        put?: never;
        /**
         * Asigna un tema a una pregunta y lo deja auditado (idempotente)
         * @description Asigna la pregunta al tema indicado y deja el evento de auditoría (`question.mapped`).
         *
         *     Es **idempotente** por `(tema, pregunta)`: repetirla devuelve el mapeo que ya estaba con
         *     `created=false` y **no** escribe un segundo evento. Es lo que necesita la clasificación de un
         *     banco entero, que se reintenta.
         *
         *     Quién lo hace se dice con `actor` en el cuerpo o con la cabecera `X-OpoFuente-Actor` (por
         *     defecto `local`): la clasificación automática se identifica («llm:deepseek-flash») y así la
         *     auditoría distingue a la persona del proceso.
         *
         *     El destino tiene que ser un **tema**: un bloque responde 409 con el motivo, porque una pregunta
         *     colgada de él quedaría fuera del diagnóstico por temas creyendo estar dentro. El **epígrafe**
         *     del tema se puede asignar a la vez (`epigraph_node_id`) y se escribe **además** del tema: el
         *     epígrafe dice dónde encaja la pregunta y el tema mantiene los recuentos que ya existen.
         */
        post: operations["assign_question_topic_api_v1_questions__question_version_id__topics_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/questions/{question_version_id}/topics/{curriculum_node_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * Quita el tema de una pregunta y lo deja auditado
         * @description Retira el mapeo y deja su evento (`question.unmapped`) con el antes.
         *
         *     Quitar algo que no estaba es un 404: no es una retirada sin efecto, es que no había nada que
         *     retirar, y decirlo evita creer que se ha deshecho una asignación que sigue puesta en otro sitio.
         */
        delete: operations["unassign_question_topic_api_v1_questions__question_version_id__topics__curriculum_node_id__delete"];
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
         * El estado de estudio de cada nodo: dominio, preguntas y próximo repaso (ruta de §10)
         * @description Lo que la aplicación puede decir del estado de estudio de cada tema, sin inventar nada.
         *
         *     Los nodos sin intentos se declaran «sin datos» y los que tienen pocos, «evidencia insuficiente»:
         *     07_UI-UX §5 pide enseñar esa columna, y aquí se calcula con la misma regla para todos.
         *
         *     Desde DEBT-027 §5 la misma respuesta trae las otras dos columnas que pedía la especificación
         *     —cuántas preguntas tiene el tema y en qué estado, y cuándo toca repasarlo—, porque las tres se
         *     leen de la misma pantalla y con la misma clave (el nodo). La ruta conserva su nombre histórico
         *     (`/reviews/mastery` es una ruta registrada en ADR-013): el dominio sigue siendo el núcleo de la
         *     respuesta, y las otras dos cifras viajan con él en lugar de obligar a una segunda llamada.
         *
         *     **Esta ruta se declara antes que `/reviews/{review_id}` a propósito**: FastAPI resuelve por
         *     orden de declaración, así que una ruta literal registrada después de una con parámetro nunca
         *     se alcanza —se pedía `/reviews/mastery` y contestaba el 404 de «no existe repaso con ese
         *     identificador»—. Hay una prueba de contrato que recorre el orden de todas las rutas.
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
    "/api/v1/search/index": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Estado del índice léxico: completo o con fragmentos por indexar */
        get: operations["index_health_api_v1_search_index_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/search/reindex": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Rehace el índice léxico desde el texto de las evidencias (DEBT-015) */
        post: operations["reindex_api_v1_search_reindex_post"];
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
    "/api/v1/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Que estudiar, con la cifra: nota, flojos, tiempo y semanas (M6)
         * @description **Nada de frases sin cifra**: todo lo que sale de aqui lleva su número.
         *
         *     **Y si no hay intentos**, la nota es `null` y las listas van vacías:
         *     **la pantalla lo dice con palabras**, no con ceros.
         */
        get: operations["get_stats_api_v1_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/mistakes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Las preguntas que fallaste la última vez, con su tema, su fecha y cuántas veces
         * @description Los fallos, y de aquí sale un test.
         *
         *     Cada fila dice **de qué tema** era la pregunta —el dato que convierte la lista en algo que se
         *     puede usar— y el reparto por tema es lo que permite pedir un test solo con los fallos de un
         *     tema. Ese test lo compone el motor con el filtro de falladas, sobre los intentos de verdad: esta
         *     lista es para mirar, no la fuente de la composición.
         */
        get: operations["student_mistakes_api_v1_student_mistakes_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/mock-exams": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El simulacro antes de montarlo: sus variantes, sus partes y el bloque del supuesto
         * @description Qué va a caer en el simulacro, leído del perfil del examen.
         *
         *     Es la ruta que hace que se pueda elegir **sabiendo qué se elige**: cuántas preguntas tiene cada
         *     parte, cuántas de reserva, cuánto dura, con qué se corrige (la penalización publicada) y qué
         *     temas entran en cada uno de los dos bloques del supuesto. Nada de esto se escribe a mano en la
         *     pantalla: sale de la convocatoria, y lo que la convocatoria no publica viaja como `null`.
         */
        get: operations["student_mock_exam_plan_api_v1_student_mock_exams_get"];
        put?: never;
        /**
         * Monta el simulacro con el perfil del examen y el bloque elegido para el supuesto
         * @description El simulacro del perfil: 80 + 5 y el supuesto de 20 + 5 del bloque III o del IV.
         *
         *     Los dos supuestos son excluyentes y se monta el elegido. Si sus preguntas salen de los temas del
         *     bloque, la sesión lo dice (`practical_case_origin`).
         *
         *     La respuesta lleva `Server-Timing` con lo que tardó **la composición** (medido en el servidor,
         *     que es donde está el trabajo). Se publica porque el encargo de la velocidad pide separar lo que
         *     cuesta elegir las preguntas de lo que cuesta pintarlas, y esa frontera no se ve desde el
         *     navegador.
         */
        post: operations["student_create_mock_exam_api_v1_student_mock_exams_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/official-exams": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Los exámenes oficiales importados (hoy, ninguno: la lista vacía se dice)
         * @description Los exámenes oficiales que hay importados de esta oposición.
         *
         *     Una lista vacía es un **estado**, no un error: quiere decir que todavía no se ha importado
         *     ninguno, y la pantalla lo dice con esas palabras en vez de quedarse en blanco o de enseñar otra
         *     cosa con el nombre de «examen oficial».
         */
        get: operations["student_official_exams_api_v1_student_official_exams_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/official-exams/{posicion}/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Monta el examen oficial que ocupa esa posición de la lista
         * @description El examen se pide por su **sitio en la lista**, no por un identificador.
         *
         *     Es la misma regla que la hoja de respuestas: lo que el alumno tiene delante es la fila, y por
         *     eso
         *     la fila es la dirección. Así la zona del alumno sigue sin enseñar de dónde salen las preguntas.
         */
        post: operations["student_create_official_exam_api_v1_student_official_exams__posicion__sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Inicio: el test a medias, los fallos vencidos y el progreso por bloque
         * @description Lo que se pinta al entrar. La oposición la pone la configuración, no la petición.
         *
         *     No hay parámetro de oposición **a propósito**: la zona del alumno sirve un solo cuerpo
         *     (`OPOFUENTE_STUDENT_OPPOSITION`) y el filtro vive en el servidor, así que no existe forma de
         *     pedir el progreso de otro desde aquí.
         */
        get: operations["student_overview_api_v1_student_overview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/progress": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Acierto por bloque y por tema, los cinco más flojos e historial de tests */
        get: operations["student_progress_api_v1_student_progress_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/sessions/{sesion}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El test en curso: la pregunta que toca y la hoja de respuestas entera
         * @description El test en curso, en la pregunta que toca o en la **fila** que se pida.
         *
         *     Poder pedir una fila es lo que hace usable la hoja de respuestas: sin esto, una pregunta ya
         *     contestada no se podía volver a abrir desde la pantalla (§3.2 del encargo F36).
         */
        get: operations["student_session_api_v1_student_sessions__sesion__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/sessions/{sesion}/abandon": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Abandona el test: lo que hayas contestado se conserva y el test no cuenta
         * @description Salir de un test a medias, con lo que queda dicho.
         *
         *     **Qué pasa con el intento abandonado**: lo contestado se conserva, la sesión queda `abandoned`,
         *     **no cuenta** como test hecho ni entra en las notas, y se puede abrir para repasar lo que se
         *     llevaba. Cuando no se contestó nada, la sesión se descarta: no hay historial que conservar.
         *
         *     Es reintentable a propósito: abandonar dos veces no da un error, devuelve el mismo parte. Y una
         *     sesión ya terminada no se toca: tiene su resultado y convertirla en abandono sería tirarlo.
         */
        post: operations["student_abandon_api_v1_student_sessions__sesion__abandon_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/sessions/{sesion}/answers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Contesta la pregunta de una fila de la hoja y devuelve el test como queda
         * @description La respuesta se pide por la **fila** de la hoja de respuestas, no por un identificador.
         *
         *     Es lo que el alumno tiene delante, y así la capa no tiene que enseñar ningún identificador de
         *     pregunta. La corrección solo vuelve cuando el modo la permite (`can_show_correction`).
         */
        post: operations["student_answer_api_v1_student_sessions__sesion__answers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/sessions/{sesion}/finish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Termina el test y devuelve el resultado con la nota de cada parte */
        post: operations["student_finish_api_v1_student_sessions__sesion__finish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/sessions/{sesion}/result": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El resultado de un test terminado: la nota por parte, el tiempo y pregunta a pregunta
         * @description El resultado entero de un test terminado, con lo que hace falta para repasar.
         *
         *     Cada pregunta con tus opciones, lo que marcaste, cuál era la correcta y **de qué tema era**, más
         *     el desglose por tema. Es la pantalla que contesta a «qué he fallado y por dónde lo repaso», que
         *     es
         *     para lo que sirve un resultado; de un test sin terminar, el motor dice que no hay resultado y la
         *     respuesta lo repite en lugar de enseñar medio resultado.
         */
        get: operations["student_session_result_api_v1_student_sessions__sesion__result_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/sessions/{sesion}/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Arranca el test (arrancar uno que ya corre no cambia nada) */
        post: operations["student_start_api_v1_student_sessions__sesion__start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/syllabus": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * El temario: bloques y temas en orden numérico, con lo disponible y el acierto
         * @description El temario completo. El orden es el de la consulta del programa, que ya es numérico.
         *
         *     Aquí no se reordena nada: el orden se arregla en la consulta (`curriculum_order`, pieza 1 de F1)
         *     y esa misma consulta la usa el panel. Reordenar otra vez en esta capa sería tener dos órdenes
         *     que pueden divergir, y por eso `IV.1` sale antes que `IV.10` sin que nadie lo toque aquí.
         */
        get: operations["student_syllabus_api_v1_student_syllabus_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/tests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Monta un test de varios temas (los que elija el alumno)
         * @description Un test de los temas elegidos, por la composición declarada del servicio de estudio.
         *
         *     Si en esos temas no hay tantas preguntas como se piden, la sesión se monta con las que haya: un
         *     test de 50 con 30 disponibles es un test de 30, no un error que deja al alumno sin estudiar.
         */
        post: operations["student_create_test_api_v1_student_tests_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/tests/plan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Qué se puede elegir antes de montar un test: los tamaños y lo que dura su reloj
         * @description El formulario del test, con lo que solo sabe el servidor (F22).
         *
         *     La pantalla de Tests **decide poco**: los tamaños que se ofrecen y los minutos que les pondría
         *     el reloj salen de aquí, y salen del mismo sitio del que sale el reloj de la sesión de verdad.
         *     Una pantalla que calculara los minutos por su cuenta enseñaría una cifra que podría no ser la
         *     que se aplica al empezar.
         */
        get: operations["student_test_plan_api_v1_student_tests_plan_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/topics/{codigo}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Un tema por su código legible (IV.10): título, epígrafes, recuentos y progreso
         * @description Un tema por su código. **Nunca** por su identificador: los UUID no se enseñan al alumno.
         */
        get: operations["student_topic_api_v1_student_topics__codigo__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/topics/{codigo}/notes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Los apuntes de un tema: un capítulo para leer y el índice completo
         * @description Los apuntes del tema, **un capítulo cada vez**, tal como se leen.
         *
         *     Un tema **en borrador se sirve igual** que uno publicado: el estado viaja con el texto
         *     (`draft`) y la pantalla lo dice. No se esconden apuntes por no haber pasado una puerta —para eso
         *     está la marca— y un tema sin apuntes devuelve su estado y una lista vacía, no un 404: el tema
         *     existe y lo que falta es el texto.
         *
         *     `capitulo` elige el epígrafe oficial. No elegirlo sirve el primero, y pedir uno que no existe
         *     **también** sirve el primero: la respuesta dice en `chapter` cuál se sirvió de verdad y la
         *     pantalla corrige la dirección. Un tema del programa son varios epígrafes y servirlos todos de
         *     golpe es lo que hacía que I.1 midiera 314.000 px de alto.
         */
        get: operations["student_topic_notes_api_v1_student_topics__codigo__notes_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/student/topics/{codigo}/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Avisa de que un apartado de los apuntes está mal («esto está mal»)
         * @description Guarda el aviso del alumno sobre un apartado de los apuntes (decisión D2).
         *
         *     No es un registro de pantalla: entra en `notes_reports` y **en la auditoría**, en la misma
         *     transacción, y es lo que el propietario verá en su bandeja. El motivo es obligatorio y de una
         *     línea; el apartado se identifica por su clave y el anclaje lo pone el servidor.
         */
        post: operations["student_report_notes_api_v1_student_topics__codigo__reports_post"];
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
        /**
         * Descarta una sesión: la borra si no tiene respuestas, la abandona si las tiene
         * @description Lo que hace falta para no dejar el banco lleno de sesiones de prueba «sin empezar».
         *
         *     Nunca borra historial con respuestas: en cuanto hay un intento, la sesión se marca abandonada y
         *     el historial se conserva. Queda en la auditoría de la aplicación.
         */
        delete: operations["discard_study_session_api_v1_study_sessions__session_id__delete"];
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
    "/api/v1/study-sessions/{session_id}/diagnostic": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * La lectura por temas de un diagnóstico (ruta añadida: DEBT-012)
         * @description Qué dice la muestra de un diagnóstico, tema por tema y con su intervalo.
         *
         *     Ruta **añadida** al contrato §10 y registrada en ADR-013. Va aparte del resultado porque no es
         *     lo
         *     mismo: el resultado dice la puntuación directa de la muestra —que no es una nota— y esta lectura
         *     dice, por tema, qué se contestó y con qué incertidumbre. Mezclarlas invitaría a leer el
         *     intervalo
         *     como una calificación.
         */
        get: operations["diagnostic_reading_api_v1_study_sessions__session_id__diagnostic_get"];
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
         * AccountAcceptedSchema
         * @description Respuesta **uniforme** del alta y de la petición de recuperación.
         *
         *     Es la misma si la dirección era nueva o no, y por eso no tiene ningún campo que lo diga. El
         *     mensaje explica lo que hay que hacer a continuación sin informar de si la cuenta existía.
         */
        AccountAcceptedSchema: {
            /** Message */
            message: string;
            /**
             * Status
             * @default accepted
             * @constant
             */
            status: "accepted";
        };
        /**
         * AccountClosedSchema
         * @description Lo que se ha borrado al cerrar la cuenta, contado. Un «hecho» sin cifra no dice nada.
         */
        AccountClosedSchema: {
            /** Audit Events */
            audit_events: number;
            /** Sessions */
            sessions: number;
            /**
             * Status
             * @default closed
             * @constant
             */
            status: "closed";
            /** Study Rows */
            study_rows: number;
        };
        /**
         * AccountEventSchema
         * @description Un movimiento auditado de la cuenta, con lo que se puede contar de él.
         */
        AccountEventSchema: {
            /** Detail */
            detail: {
                [key: string]: unknown;
            };
            /** Kind */
            kind: string;
            /**
             * Occurred At
             * Format: date-time
             */
            occurred_at: string;
        };
        /**
         * AccountMeSchema
         * @description Quién soy, hasta cuándo dura esta sesión y qué ha pasado con mi cuenta.
         */
        AccountMeSchema: {
            account: components["schemas"]["AccountSchema"];
            /** Events */
            events: components["schemas"]["AccountEventSchema"][];
            /**
             * Session Expires At
             * Format: date-time
             */
            session_expires_at: string;
        };
        /**
         * AccountSchema
         * @description La cuenta tal como se enseña: su dirección y sus fechas. Nada más.
         */
        AccountSchema: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /** Id */
            id: string;
            /**
             * Password Changed At
             * Format: date-time
             */
            password_changed_at: string;
        };
        /**
         * AccountSessionSchema
         * @description Una sesión abierta. `current` marca la que se está usando.
         */
        AccountSessionSchema: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Current */
            current: boolean;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Id */
            id: string;
            /**
             * Last Seen At
             * Format: date-time
             */
            last_seen_at: string;
        };
        /** AccountSessionsSchema */
        AccountSessionsSchema: {
            /** Sessions */
            sessions: components["schemas"]["AccountSessionSchema"][];
        };
        /**
         * AccountsAvailableSchema
         * @description Si esta instalación tiene cuentas, y qué implica tenerlas o no.
         *
         *     La interfaz lo necesita para no ofrecer un acceso que no existe. Lo que **no** dice es si la
         *     sesión actual es válida: eso lo contesta `GET /accounts/me` con un 200 o un 401, que es la única
         *     respuesta que no se puede fingir desde la pantalla.
         */
        AccountsAvailableSchema: {
            /** Anonymous Study */
            anonymous_study: boolean;
            /** Delivery Channel */
            delivery_channel: string;
            /** Enabled */
            enabled: boolean;
            /** Session Cookie Name */
            session_cookie_name: string;
            /** Session Days */
            session_days: number;
        };
        /**
         * AccountsPolicySchema
         * @description Lo que la interfaz tiene que saber de las cuentas para ofrecer o no el acceso.
         */
        AccountsPolicySchema: {
            /** Anonymous Study */
            anonymous_study: boolean;
            /** Delivery Channel */
            delivery_channel: string;
            /** Enabled */
            enabled: boolean;
            /** Session Cookie Name */
            session_cookie_name: string;
            /** Session Days */
            session_days: number;
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
        /**
         * AnalyticsCountSchema
         * @description Un renglón del resumen: el tipo, la etiqueta y cuántas veces.
         */
        AnalyticsCountSchema: {
            /** Label */
            label: string;
            /** Name */
            name: string;
            /** Total */
            total: number;
        };
        /**
         * AnalyticsDaySchema
         * @description Cuántos sucesos hubo un día.
         */
        AnalyticsDaySchema: {
            /** Day */
            day: string;
            /** Total */
            total: number;
        };
        /**
         * AnalyticsEventSchema
         * @description El suceso que se cuenta. Solo dos campos, y los dos de una lista cerrada.
         */
        AnalyticsEventSchema: {
            /** Label */
            label: string;
            /** Name */
            name: string;
        };
        /**
         * AnalyticsPolicySchema
         * @description Si hay analítica y de qué depende.
         */
        AnalyticsPolicySchema: {
            /** Enabled */
            enabled: boolean;
            /** Requires Consent */
            requires_consent: boolean;
            /** Retention Days */
            retention_days: number;
        };
        /**
         * AnalyticsRecordedSchema
         * @description Acuse de un suceso contado. No devuelve lo contado: no hay nada que devolver.
         */
        AnalyticsRecordedSchema: {
            /** Day */
            day: string;
            /** Recorded */
            recorded: boolean;
        };
        /**
         * AnalyticsSummarySchema
         * @description Lo contado, agrupado por etiqueta y por día, con el plazo declarado.
         */
        AnalyticsSummarySchema: {
            /** Counts */
            counts: components["schemas"]["AnalyticsCountSchema"][];
            /** Days */
            days: components["schemas"]["AnalyticsDaySchema"][];
            /** Enabled */
            enabled: boolean;
            /** Notice */
            notice: string;
            /** Requires Consent */
            requires_consent: boolean;
            /** Retention Days */
            retention_days: number;
        };
        /**
         * AnswerCardSchema
         * @description Lo que se responde a una tarjeta, con las cuatro opciones de SM-2.
         */
        AnswerCardSchema: {
            respuesta: components["schemas"]["Respuesta"];
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
         * AreaUsageSchema
         * @description Lo que ocupa un área del árbol de datos. `readable=False` significa «no se ha podido medir»,
         *     que no es lo mismo que cero.
         */
        AreaUsageSchema: {
            /** Area */
            area: string;
            /** File Count */
            file_count: number;
            /** Note */
            note?: string | null;
            /** Path Display */
            path_display: string;
            /** Readable */
            readable: boolean;
            /** Size Bytes */
            size_bytes: number;
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
         * AssignTopicRequestSchema
         * @description Asignar un tema a una pregunta.
         *
         *     `actor` distingue quién lo hace y no es adorno: la clasificación automática de miles de
         *     preguntas tiene que quedar identificada en la auditoría, y `local` es la persona que está.
         *     `reason` es el motivo y va a la auditoría, que es donde se lee por qué se clasificó así.
         */
        AssignTopicRequestSchema: {
            /** Actor */
            actor?: string | null;
            /**
             * Confidence
             * @default 1
             */
            confidence: number;
            /** Curriculum Node Id */
            curriculum_node_id: string;
            /** Epigraph Node Id */
            epigraph_node_id?: string | null;
            /** Reason */
            reason?: string | null;
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
        BatchStatus: "queued" | "running" | "succeeded" | "failed" | "cancel_requested" | "cancelled" | "paused";
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
        /**
         * BulkRecalculationSchema
         * @description Recálculo en bloque: qué plantilla se usó, sesión por sesión, y cuántas cambiaron.
         */
        BulkRecalculationSchema: {
            /** Changed */
            changed: number;
            /** Detail */
            detail: string;
            /** Key Version */
            key_version: number;
            /** Question Set Id */
            question_set_id: string;
            /** Sessions */
            sessions: components["schemas"]["SessionRecalculationSchema"][];
        };
        /**
         * BulkTopicAssignmentReportSchema
         * @description El lote entero: cada fila con su desenlace y los totales por desenlace.
         */
        BulkTopicAssignmentReportSchema: {
            /**
             * Already Excluded
             * @default 0
             */
            already_excluded: number;
            /**
             * Created
             * @default 0
             */
            created: number;
            /**
             * Errors
             * @default 0
             */
            errors: number;
            /**
             * Excluded
             * @default 0
             */
            excluded: number;
            /**
             * Existing
             * @default 0
             */
            existing: number;
            /**
             * Promoted
             * @default 0
             */
            promoted: number;
            /** Results */
            results: components["schemas"]["BulkTopicAssignmentResultSchema"][];
        };
        /**
         * BulkTopicAssignmentResultSchema
         * @description Qué ha pasado con **una** fila del lote.
         *
         *     `outcome` es el vocabulario que hace utilizable el reintento: `created` (esta llamada lo creó),
         *     `existing` (ya estaba tal cual), `promoted` (ya estaba como **propuesta** y esta llamada la ha
         *     confirmado), `excluded` (marcada fuera de temario ahora), `already_excluded` (ya lo estaba) y
         *     `error` (la fila no se pudo aplicar, con el motivo en `detail`). Una fila mala **no** tumba el
         *     lote: se dice cuál y por qué.
         *
         *     `promoted` y `created` son distintos a propósito: la cola de revisión se despacha confirmando
         *     propuestas, y un informe que contara las confirmaciones como «ya estaban» dejaría al propietario
         *     sin saber si su decisión se aplicó.
         */
        BulkTopicAssignmentResultSchema: {
            assignment?: components["schemas"]["QuestionTopicAssignmentSchema"] | null;
            /** Detail */
            detail?: string | null;
            exclusion?: components["schemas"]["QuestionExclusionSchema"] | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "created" | "existing" | "promoted" | "excluded" | "already_excluded" | "error";
            /** Question Version Id */
            question_version_id: string;
        };
        /**
         * BulkTopicAssignmentSchema
         * @description Una fila del lote: o un tema (con su epígrafe, si se sabe) o un fuera de temario.
         *
         *     Las dos formas son excluyentes y se comprueba: una fila que dijera las dos cosas dejaría la
         *     pregunta clasificada y sin clasificar a la vez, y una que no dijera ninguna no pide nada.
         *
         *     `status` es opcional **a propósito**, y su ausencia significa algo: una fila sin `status` no
         *     toca lo que ya existe (crear si falta, y nada más), que es lo que necesita una clasificación por
         *     lotes que se reintenta. Una fila **con** `status` dice qué tiene que quedar: si la pregunta ya
         *     tenía una propuesta (`provisional`) a ese tema, se confirma —o se vuelve a proponer— y eso queda
         *     auditado. Es lo que hace el propietario al despachar la cola desde la pantalla de revisión, y
         *     por eso la confirmación viaja en el lote: no una petición por pregunta.
         */
        BulkTopicAssignmentSchema: {
            /**
             * Confidence
             * @default 1
             */
            confidence: number;
            /** Curriculum Node Id */
            curriculum_node_id?: string | null;
            /** Epigraph Node Id */
            epigraph_node_id?: string | null;
            /** Exclusion Reason */
            exclusion_reason?: ("otra_administracion" | "enunciado_roto") | null;
            /** Question Version Id */
            question_version_id: string;
            /** Reason */
            reason?: string | null;
            /**
             * Retire Others
             * @default false
             */
            retire_others: boolean;
            /** Status */
            status?: ("provisional" | "accepted") | null;
        };
        /**
         * BulkTopicAssignmentsSchema
         * @description Un lote de asignaciones con **un** actor.
         *
         *     El actor va en el sobre y no en cada fila: un lote lo firma quien lo manda, y repetirlo 200
         *     veces solo sirve para que alguna fila diga otra cosa que las demás por error.
         */
        BulkTopicAssignmentsSchema: {
            /** Actor */
            actor?: string | null;
            /** Assignments */
            assignments: components["schemas"]["BulkTopicAssignmentSchema"][];
        };
        /** CanjeResultadoSchema */
        CanjeResultadoSchema: {
            /** Creada */
            creada: boolean;
            /** Motivo */
            motivo: string;
        };
        /**
         * CanjeSchema
         * @description Lo que manda la pantalla: el token del enlace y la contrasena nueva.
         */
        CanjeSchema: {
            /** Contrasena */
            contrasena: string;
            /** Correo */
            correo: string;
            /** Token */
            token: string;
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
         * CardQueueSchema
         * @description La cola del día: **tarjetas, fallos vencidos y el total**, que son tres cosas distintas.
         */
        CardQueueSchema: {
            /**
             * Fallos
             * @default []
             */
            fallos: components["schemas"]["DueFailureSchema"][];
            /** Tarjetas */
            tarjetas: components["schemas"]["CardSchema"][];
            /**
             * Total
             * @description Cuántas vencen hoy, no cuántas caben en la pantalla
             */
            total: number;
        };
        /**
         * CardSchema
         * @description Una tarjeta tal como la pinta la pantalla de repaso.
         */
        CardSchema: {
            /** Back */
            back: string;
            /** Citation */
            citation?: string | null;
            /**
             * Due At
             * Format: date-time
             */
            due_at: string;
            /** Front */
            front: string;
            /** Id */
            id: string;
            /** Interval Days */
            interval_days: number;
            /** Repetitions */
            repetitions: number;
        };
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
        /**
         * ConflictingTopicSchema
         * @description Un tema ya decidido de una pregunta que tiene más de uno, con quién lo decidió.
         *
         *     `actor` viaja porque cambia cómo se mira: uno heredado de una migración (`local`) y uno
         *     propuesto por el modelo (`llm:…`) no se juzgan igual. Nulo es «no consta en la auditoría», que
         *     también hay que poder decir en lugar de inventarse un autor.
         */
        ConflictingTopicSchema: {
            /** Actor */
            actor?: string | null;
            /** Confidence */
            confidence: number;
            /** Created At */
            created_at?: string | null;
            /** Mapping Id */
            mapping_id: string;
            topic: components["schemas"]["ProgrammeNodeRefSchema"];
        };
        /**
         * ConsentDecisionSchema
         * @description Lo que se decide. Los dos fines son independientes y los dos nacen en falso.
         *
         *     Aceptar y rechazar usan **el mismo cuerpo**: la diferencia es el valor de dos booleanos, y por
         *     eso
         *     no hay ninguna forma de que un camino sea más fácil que el otro en el contrato. `necesarias` no
         *     se
         *     pide: no se puede rechazar lo que hace falta para que la aplicación funcione.
         */
        ConsentDecisionSchema: {
            /**
             * Analytics
             * @default false
             */
            analytics: boolean;
            /**
             * Preferences
             * @default false
             */
            preferences: boolean;
        };
        /**
         * ConsentStateSchema
         * @description Lo que se ha decidido, tal como queda guardado.
         */
        ConsentStateSchema: {
            /** Analytics */
            analytics: boolean;
            /**
             * Decided At
             * Format: date-time
             */
            decided_at: string;
            /** Necessary */
            necessary: boolean;
            /** Policy Version */
            policy_version: number;
            /** Preferences */
            preferences: boolean;
        };
        /**
         * ConsentSummarySchema
         * @description Cuántas decisiones se han tomado, contadas por desenlace y **sin ningún sujeto**.
         */
        ConsentSummarySchema: {
            /** Policy Version */
            policy_version: number;
            /**
             * Since
             * @description Cuándo se tomó la primera decisión que sigue guardada.
             */
            since?: string | null;
            /** Total */
            total: number;
            /** With Analytics */
            with_analytics: number;
            /** With Preferences */
            with_preferences: number;
        };
        /** ConvocationDetailSchema */
        ConvocationDetailSchema: {
            /** Code */
            code: string;
            /** Exam Date */
            exam_date?: string | null;
            /** Exam Date Note */
            exam_date_note?: string | null;
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
         * @description Estado de una convocatoria publicada.
         *
         *     `active` no significa «la última que ha salido» sino **la que la aplicación usa para trabajar**:
         *     es la que resuelven Programa, Estudio, Repaso y Banco, y solo puede haber una por oposición (lo
         *     garantiza un índice único parcial). Los demás estados describen por qué una convocatoria no es
         *     esa:
         *
         *     - `draft`: todavía no se ha publicado. Nadie la ha convocado, así que no es utilizable.
         *     - `available`: está publicada, es utilizable y **no es la vigente**. Es el caso de una oposición
         *       con dos procesos vivos a la vez —Celador tiene la convocatoria ordinaria de acceso libre y el
         *       proceso de estabilización de la Ley 20/2021—: ninguna sustituye a la otra, las dos se pueden
         *       estudiar y solo una se elige para trabajar.
         *     - `superseded`: otra convocatoria del **mismo proceso** la ha reemplazado (una orden corregida,
         *       una republicación). No es lo mismo que `available`: aquí sí hay un acto posterior que la deja
         *       atrás.
         *     - `archived`: la aplicación no debe usar esta convocatoria.
         * @enum {string}
         */
        ConvocationStatus: "draft" | "active" | "available" | "superseded" | "archived";
        /**
         * CookieSchema
         * @description Una cookie, con su finalidad, su duración y si es necesaria.
         */
        CookieSchema: {
            /** Duration */
            duration: string;
            /** Essential */
            essential: boolean;
            /** Name */
            name: string;
            /** Purpose */
            purpose: string;
            /** Purpose Key */
            purpose_key: string;
            /** Set By */
            set_by: string;
        };
        /**
         * CookiesSchema
         * @description Las cookies de esta aplicación y el texto vigente que se acepta.
         */
        CookiesSchema: {
            /** Cookies */
            cookies: components["schemas"]["CookieSchema"][];
            /** Essential */
            essential: string[];
            /** Notice */
            notice: string;
            /** Policy Version */
            policy_version: number;
            /** Purposes */
            purposes: string[];
            /** Updated On */
            updated_on: string;
        };
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
            /** Explanation Anchor Id */
            explanation_anchor_id?: string | null;
            /** Explanation Citation */
            explanation_citation?: string | null;
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
             * Origin Scope
             * @default desconocida
             * @enum {string}
             */
            origin_scope: "age" | "otra_administracion" | "desconocida";
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
            /**
             * Curriculum Node Id
             * @description Solo en `practice`: el tema cuyas preguntas catalogadas componen la sesión (S13). La composición la pone la catalogación del tema, así que no se mandan `sources`.
             */
            curriculum_node_id?: string | null;
            /** Feedback */
            feedback?: ("immediate" | "at_end") | null;
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam" | "mock_exam" | "diagnostic";
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
        /**
         * DataInventorySchema
         * @description El inventario completo: lo que se recoge y lo que no.
         */
        DataInventorySchema: {
            /** Not Collected */
            not_collected: components["schemas"]["NegativeClaimSchema"][];
            /** Notice */
            notice: string;
            /** Uses */
            uses: components["schemas"]["DataUseSchema"][];
        };
        /**
         * DataUseSchema
         * @description Una fila del inventario: qué, para qué, dónde y cuánto tiempo, con su base jurídica.
         */
        DataUseSchema: {
            /** Lawful Basis */
            lawful_basis: string;
            /** Needs Account */
            needs_account: boolean;
            /** Needs Consent */
            needs_consent: string | null;
            /** Retention */
            retention: string;
            /** What */
            what: string;
            /** Where */
            where: string;
            /** Why */
            why: string;
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
        /**
         * DiagnosticReadingSchema
         * @description La lectura de un diagnóstico: por tema y con el tamaño de la muestra delante.
         *
         *     Los intervalos viajan **con** sus recuentos porque sin ellos no se pueden leer: un intervalo
         *     ancho
         *     sobre dos preguntas y uno estrecho sobre veinte no dicen lo mismo.
         */
        DiagnosticReadingSchema: {
            /** Answered */
            answered: number;
            /** Detail */
            detail: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam" | "mock_exam" | "diagnostic";
            /** Sample Size */
            sample_size: number;
            /** Session Id */
            session_id: string;
            /** Topics */
            topics: components["schemas"]["DiagnosticTopicSchema"][];
        };
        /**
         * DiagnosticSchema
         * @description Diagnóstico sanitizado (09_SECURITY §12): sin secretos, sin contenido y sin rutas completas.
         *
         *     Es lo que se puede pegar en una incidencia. Lleva **lo que hace falta para juzgar el estado** y
         *     nada de lo que el usuario tiene dentro: ni una ruta absoluta, ni un enunciado, ni una clave.
         */
        DiagnosticSchema: {
            /** Capabilities */
            capabilities: components["schemas"]["CapabilitySchema"][];
            /** Checks */
            checks: components["schemas"]["CheckSchema"][];
            /** Counts */
            counts: {
                [key: string]: number;
            };
            /** Data Dir Display */
            data_dir_display: string;
            /** Database File Display */
            database_file_display: string;
            /** Degradations */
            degradations: components["schemas"]["DegradationSchema"][];
            /** Disk Free Bytes */
            disk_free_bytes: number;
            /** Disk Total Bytes */
            disk_total_bytes: number;
            /** Generated At */
            generated_at: string;
            /** Host */
            host: string;
            limits: components["schemas"]["LimitsSchema"];
            /** Log Level */
            log_level: string;
            /** Log Tail */
            log_tail: string[];
            /** Note */
            note: string;
            /** Platform */
            platform: string;
            /** Port */
            port: number;
            /** Python Version */
            python_version: string;
            /** Schema Revision */
            schema_revision: string;
            /** Version */
            version: string;
        };
        /**
         * DiagnosticTopicSchema
         * @description Lo que se contestó de un tema en la muestra, con su intervalo y su aviso.
         */
        DiagnosticTopicSchema: {
            /** Answered */
            answered: number;
            /** Correct */
            correct: number;
            interval?: components["schemas"]["IntervalSchema"] | null;
            /** Node Id */
            node_id: string;
            /** Note */
            note: string;
            /** Title */
            title: string;
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
         * DossierArchiveSchema
         * @description Resultado de archivar: el dossier archivado y si esa lectura ya estaba guardada.
         */
        DossierArchiveSchema: {
            /** Created */
            created: boolean;
            dossier: components["schemas"]["DossierSchema"];
            /** Version Id */
            version_id: string;
        };
        /** DossierHoleSchema */
        DossierHoleSchema: {
            /**
             * Code
             * @enum {string}
             */
            code: "sin_material" | "sin_texto" | "no_citable" | "sin_version_aceptada" | "mapeo_provisional" | "repetido_en_otra_fuente";
            /** Count */
            count: number;
            /** Reason */
            reason?: string | null;
        };
        /**
         * DossierNoteSectionSchema
         * @description Un apartado de los apuntes redactados, con el rastro de las preguntas que cubre.
         *
         *     `question_ids` son identificadores de pregunta, y eso es deliberado: esta pantalla es la del
         *     **propietario** (la ficha del tema en el programa), no la del alumno, y poder cruzar un apartado
         *     con sus preguntas es justo lo que hace falta para revisarlos. La zona del alumno tiene su propia
         *     ruta y su propio contrato, sin identificadores.
         */
        DossierNoteSectionSchema: {
            /**
             * Anchor
             * @description Anclaje estable del apartado, para enlazar desde una pregunta.
             */
            anchor: string;
            /** Body Markdown */
            body_markdown: string;
            /** Conflict Question Ids */
            conflict_question_ids: string[];
            /**
             * Conflicts
             * @description Preguntas que este apartado contesta con una letra distinta de su clave: van a revisión, no cuentan como cubiertas.
             */
            conflicts: number;
            /** Covered */
            covered: number;
            /** Doubtful */
            doubtful: number;
            /** Doubtful Question Ids */
            doubtful_question_ids: string[];
            /** Epigraph Code */
            epigraph_code: string;
            /** Facts Total */
            facts_total: number;
            /** Gap Question Ids */
            gap_question_ids: string[];
            /** Gaps */
            gaps: number;
            /** Key */
            key: string;
            /** Needs Review Reason */
            needs_review_reason?: string | null;
            /** Question Ids */
            question_ids: string[];
            /** Title */
            title: string;
        };
        /**
         * DossierNotesSchema
         * @description Los apuntes de un tema: los que se escriben a partir de sus preguntas y se comprueban con
         *     ellas.
         *
         *     Van dentro del dossier porque el tema es una unidad de lectura y de versionado: al guardar una
         *     versión se guarda el tema entero, citas **y** apuntes, y una versión antigua se lee como se
         *     leyó.
         */
        DossierNotesSchema: {
            /**
             * Conflicts
             * @description Preguntas cuya letra según los apuntes no coincide con la clave. No son cobertura: son la cola de revisión de la comprobación (paso E).
             */
            conflicts: number;
            /** Covered */
            covered: number;
            /** Doubtful */
            doubtful: number;
            /** Gaps */
            gaps: number;
            /** Generated At */
            generated_at?: string | null;
            /** Model */
            model?: string | null;
            /** Prompt Template Version */
            prompt_template_version: string;
            /** Questions Total */
            questions_total: number;
            /** Sections */
            sections: components["schemas"]["DossierNoteSectionSchema"][];
            /** Sections Total */
            sections_total: number;
        };
        /** DossierPassageSchema */
        DossierPassageSchema: {
            /** Citation Label */
            citation_label?: string | null;
            /** Evidence Id */
            evidence_id: string;
            /** Ordinal */
            ordinal: number;
            /** Page */
            page?: number | null;
            /** Quality */
            quality?: string | null;
            /** Repeated In */
            repeated_in: string[];
            /** Section Title */
            section_title?: string | null;
            /**
             * Text
             * @description Texto literal del tramo: la cita, tal cual se guardó.
             */
            text: string;
        };
        /**
         * DossierSchema
         * @description El dossier de un tema: sus fuentes citadas, sus huecos y con qué se construyó.
         */
        DossierSchema: {
            /** Accepted Sources */
            accepted_sources: number;
            /** Content Hash */
            content_hash: string;
            /** Depth */
            depth: number;
            /** Empty */
            empty: boolean;
            /** Format Version */
            format_version: number;
            /**
             * Generated At
             * Format: date-time
             */
            generated_at: string;
            /** Holes */
            holes: components["schemas"]["DossierHoleSchema"][];
            /** Node Id */
            node_id: string;
            notes?: components["schemas"]["DossierNotesSchema"] | null;
            /** Passages Total */
            passages_total: number;
            /** Path */
            path: string;
            /** Previous Version Id */
            previous_version_id?: string | null;
            /** Provisional */
            provisional: boolean;
            /** Provisional Sources */
            provisional_sources: number;
            /** Sources */
            sources: components["schemas"]["DossierSourceSchema"][];
            /** Sources Total */
            sources_total: number;
            /** Title */
            title: string;
            /** Version Id */
            version_id?: string | null;
        };
        /** DossierSourceSchema */
        DossierSourceSchema: {
            /** Authority Tier */
            authority_tier?: string | null;
            /** Document Id */
            document_id: string;
            /** Document Title */
            document_title: string;
            /** Document Type */
            document_type: string;
            /** Mappings */
            mappings: string[];
            /** Passages */
            passages: components["schemas"]["DossierPassageSchema"][];
            /** Passages Total */
            passages_total: number;
            /** Provisional */
            provisional: boolean;
            /** Quality */
            quality?: string | null;
            /** Version Id */
            version_id: string;
            /** Version Label */
            version_label?: string | null;
            /** Version Status */
            version_status: string;
        };
        /**
         * DossierVersionSchema
         * @description Una versión guardada del dossier: lo justo para listarla y elegir con cuál comparar.
         */
        DossierVersionSchema: {
            /**
             * Built At
             * Format: date-time
             */
            built_at: string;
            /** Content Hash */
            content_hash: string;
            /** Id */
            id: string;
            /** Passages Count */
            passages_count: number;
            /** Sources Count */
            sources_count: number;
        };
        /**
         * DueFailureAnswerSchema
         * @description Lo que manda la pantalla al contestar un fallo: **solo la letra elegida**.
         */
        DueFailureAnswerSchema: {
            /** Option Key */
            option_key: string;
        };
        /**
         * DueFailureCorrectionSchema
         * @description **La corrección de un fallo**: si está bien, qué letra valía y por qué.
         *
         *     **La explicación llega ahora, no antes**: hasta que el alumno contesta no se dice nada, que es
         *     lo mismo que hace un test.
         */
        DueFailureCorrectionSchema: {
            /** Citation */
            citation?: string | null;
            /** Correct */
            correct: boolean;
            /** Correct Option Keys */
            correct_option_keys: string[];
            /** Explanation */
            explanation?: string | null;
        };
        /**
         * DueFailureOptionSchema
         * @description Una opción del fallo, con su letra y su texto.
         */
        DueFailureOptionSchema: {
            /** Key */
            key: string;
            /** Text */
            text: string;
        };
        /**
         * DueFailureSchema
         * @description **Una pregunta fallada que vence hoy** (fase «lo que ve el alumno», punto 3).
         *
         *     **Lleva el enunciado y las opciones y NO la clave**: contestarla es lo que la saca de la cola, y
         *     la corrección la hace el servidor. **La explicación se sirve al corregir**, no antes.
         */
        DueFailureSchema: {
            /** Options */
            options: components["schemas"]["DueFailureOptionSchema"][];
            /** Question Version Id */
            question_version_id: string;
            /** Stem */
            stem: string;
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
        /**
         * EmailPasswordSchema
         * @description Cuerpo común del alta y del acceso.
         *
         *     Las longitudes son las del contrato: una dirección de más de 254 caracteres no es una dirección,
         *     y
         *     una contraseña de más de 256 no se admite porque el coste de derivarla crece con ella. Que el
         *     mínimo tenga que ser doce lo decide el dominio, no el esquema: así el mensaje de error dice
         *     **por
         *     qué** no vale, y no un «valor inválido» genérico.
         */
        EmailPasswordSchema: {
            /** Email */
            email: string;
            /** Password */
            password: string;
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
         * ExplanationSchema
         * @description Explicación de una pregunta entera o de una de sus opciones (07_UI-UX §7, S12.7).
         *
         *     `option_stable_key` nulo es «la pregunta entera»; con valor, es la explicación de esa opción
         *     («por qué la b no vale»). El origen y el estado no son adorno: una explicación generada por un
         *     modelo queda en borrador y se dice con qué modelo se escribió.
         */
        ExplanationSchema: {
            /** Citation */
            citation?: string | null;
            /** Created At */
            created_at?: string | null;
            /** Id */
            id: string;
            /** Model Name */
            model_name?: string | null;
            /** Note Anchor Id */
            note_anchor_id?: string | null;
            /** Option Stable Key */
            option_stable_key?: string | null;
            /**
             * Origin
             * @enum {string}
             */
            origin: "official" | "private" | "generated";
            /** Question Version Id */
            question_version_id: string;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "reviewed" | "rejected";
            /** Text */
            text: string;
        };
        /**
         * ExplanationTrayItemSchema
         * @description Una fila de la bandeja de revisión: la explicación **y la pregunta a la que pertenece**.
         *
         *     No es `ExplanationSchema` con dos campos más: **aquí la pregunta es el contexto y tiene que
         *     venir dentro**, porque el propietario aprueba una explicación **sabiendo de qué pregunta es**.
         *     Servirla suelta obligaría a abrir otra pantalla por cada fila, que es lo que la bandeja existe
         *     para evitar.
         *
         *     `options` no viene: quien revisa abre la ficha de la pregunta, y **la bandeja no repite la
         *     pregunta entera** — su trabajo es decidir si la explicación sirve, no volver a leer el examen.
         */
        ExplanationTrayItemSchema: {
            explanation: components["schemas"]["ExplanationSchema"];
            /** Question Version Id */
            question_version_id: string;
            /** Stem */
            stem: string;
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
         * GuardarPlanSchema
         * @description Lo que decide el alumno: la fecha, las horas y los descansos.
         */
        GuardarPlanSchema: {
            /**
             * Exam Date
             * Format: date
             */
            exam_date: string;
            /** Hours Per Week */
            hours_per_week: number;
            /** Rest Days */
            rest_days?: number[];
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /**
         * HousekeepingCandidateSchema
         * @description Algo que se puede retirar, con su motivo y su tamaño. La pantalla lo enseña **antes**.
         */
        HousekeepingCandidateSchema: {
            /** Action */
            action: string;
            /** Detail */
            detail: string;
            /** Display */
            display: string;
            /** Reference */
            reference: string;
            /** Size Bytes */
            size_bytes: number;
        };
        /** HousekeepingReportSchema */
        HousekeepingReportSchema: {
            /** Candidates */
            candidates: components["schemas"]["HousekeepingCandidateSchema"][];
            /** Reclaimable Bytes */
            reclaimable_bytes: number;
            /** Retention Days */
            retention_days: number;
            /** Total Bytes */
            total_bytes: number;
            /** Usage */
            usage: components["schemas"]["AreaUsageSchema"][];
        };
        /**
         * HoySchema
         * @description La semana en curso, **o el motivo de que no haya nada**.
         */
        HoySchema: {
            /** Motivos */
            motivos: string[];
            semana?: components["schemas"]["opofuente__api__routes__plan__SemanaSchema"] | null;
        };
        /**
         * ImportQuestionsFromDocumentSchema
         * @description Importar las preguntas de una **versión de documento** (DEBT-010).
         */
        ImportQuestionsFromDocumentSchema: {
            /** Document Version Id */
            document_version_id: string;
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
         * IndexHealthSchema
         * @description Si el índice léxico está completo. Cuando faltan fragmentos, se dice cuántos.
         */
        IndexHealthSchema: {
            /** Detail */
            detail: string;
            /** Healthy */
            healthy: boolean;
            /** Missing Entries */
            missing_entries: number;
        };
        /**
         * IntervalSchema
         * @description Un intervalo de confianza sobre una muestra pequeña, con su nivel declarado.
         */
        IntervalSchema: {
            /** Confidence */
            confidence: number;
            /** High */
            high: number;
            /** Low */
            low: number;
            /** Width */
            width: number;
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
        JobStatus: "queued" | "leased" | "running" | "succeeded" | "failed" | "cancel_requested" | "paused" | "cancelled";
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
         * KeySourceLinkSchema
         * @description Lo que se comparó al enlazar: la plantilla, pregunta a pregunta, contra la clave.
         */
        KeySourceLinkSchema: {
            /** Agreeing */
            agreeing: number;
            /** Ambiguous */
            ambiguous: number;
            /** Disagreeing */
            disagreeing: number;
            key: components["schemas"]["AnswerKeySchema"];
            /** Key Entries */
            key_entries: number;
            /** Lines */
            lines: number;
            /** Without Entry */
            without_entry: number;
        };
        /**
         * LegalBundleSchema
         * @description Los tres documentos, la fecha del texto vigente y lo que falta por rellenar.
         */
        LegalBundleSchema: {
            /** Documents */
            documents: components["schemas"]["LegalDocumentSchema"][];
            /** Notice */
            notice: string;
            /** Owner Fields Pending */
            owner_fields_pending: string[];
            /** Pending Owner Notice */
            pending_owner_notice: string;
            /** Text Version */
            text_version: number;
            /** Updated On */
            updated_on: string;
        };
        /**
         * LegalDocumentSchema
         * @description Un documento legal: su nombre corto, su título y su texto.
         */
        LegalDocumentSchema: {
            /** Body Markdown */
            body_markdown: string;
            /** Key */
            key: string;
            /** Summary */
            summary: string;
            /** Title */
            title: string;
        };
        /**
         * LegalPolicySchema
         * @description Lo que la interfaz necesita para pedir el consentimiento.
         */
        LegalPolicySchema: {
            /** Enabled */
            enabled: boolean;
            /** Essential */
            essential: string[];
            /** Owner Fields Pending */
            owner_fields_pending: boolean;
            /** Policy Version */
            policy_version: number;
            /** Purposes */
            purposes: string[];
            /** Text Version */
            text_version: number;
            /** Updated On */
            updated_on: string;
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
        /**
         * LinkKeySourceRequestSchema
         * @description La versión de documento que es la plantilla oficial de la clave (`null` desenlaza).
         */
        LinkKeySourceRequestSchema: {
            /** Source Document Version Id */
            source_document_version_id?: string | null;
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
        /**
         * MarkCorrectOptionSchema
         * @description Marca la respuesta correcta de esta pregunta.
         *
         *     `correct_option_keys` es **obligatorio y sin valor por defecto**: cambiar lo que se da por bueno
         *     es un acto deliberado, y admitir el cuerpo vacío dejaría la puerta abierta a una llamada que no
         *     dice qué quiere.
         */
        MarkCorrectOptionSchema: {
            /** Actor */
            actor?: string | null;
            /** Correct Option Keys */
            correct_option_keys: ("a" | "b" | "c" | "d" | "e" | "f" | "g" | "h")[];
            /** Note */
            note?: string | null;
        };
        /**
         * MarkCorrectResultSchema
         * @description Lo que devuelve marcar la correcta: la ficha al día y las dos plantillas.
         *
         *     `superseded_key_version_id` viaja porque el hecho que hay que poder comprobar es que la anterior
         *     **no se ha pisado**: queda `superseded` y se puede leer.
         */
        MarkCorrectResultSchema: {
            /** Actor */
            actor: string;
            /** Correct Option Keys */
            correct_option_keys: string[];
            file: components["schemas"]["QuestionFileSchema"];
            /** Key Version Id */
            key_version_id: string;
            /** Previous Option Keys */
            previous_option_keys: string[];
            /** Superseded Key Version Id */
            superseded_key_version_id: string | null;
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
         * NegativeClaimSchema
         * @description Lo que **no** se recoge, declarado para poder comprobarlo.
         */
        NegativeClaimSchema: {
            /** Claim */
            claim: string;
        };
        /**
         * NodeMasterySchema
         * @description El dominio de un nodo concreto del programa, con el estado de sus preguntas y su repaso.
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
            study_state: components["schemas"]["NodeStudyStateSchema"];
        };
        /**
         * NodeStudyStateSchema
         * @description Qué preguntas tiene un nodo y cuándo toca repasarlas.
         *
         *     Va con el dominio porque la pantalla de Programa las enseña juntas, en columnas distintas: son
         *     dos hechos independientes (un tema puede tener buen dominio y una sola pregunta, o ninguna).
         */
        NodeStudyStateSchema: {
            /** Next Review At */
            next_review_at?: string | null;
            /** Questions By Origin */
            questions_by_origin: components["schemas"]["QuestionCountSchema"][];
            /** Questions By Status */
            questions_by_status: components["schemas"]["QuestionCountSchema"][];
            /** Questions Total */
            questions_total: number;
            /** Reviews Due */
            reviews_due: number;
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
        /**
         * NotaSchema
         * @description La nota **con su intervalo**, y el intervalo puede no estar.
         */
        NotaSchema: {
            /** Frase */
            frase: string;
            /** Intentos */
            intentos: number;
            /** Maximo */
            maximo?: number | null;
            /** Minimo */
            minimo?: number | null;
            /** Nota */
            nota: number;
        };
        /**
         * NoteReportListSchema
         * @description Los avisos, cuántos siguen sin despachar y cuántos hay en cada estado.
         *
         *     Los recuentos van aparte de la lista aunque se puedan contar de ella: la lista viene filtrada y
         *     limitada (por estado, por tema y por búsqueda), y los números que el propietario necesita ver
         *     son los de la bandeja entera, no los de la página que está mirando. `pending` es solo `open`:
         *     un aviso «en curso» ya no espera a nadie, y por eso no cuenta ahí.
         */
        NoteReportListSchema: {
            /**
             * Dismissed
             * @description Avisos descartados: no eran un error.
             */
            dismissed: number;
            /**
             * In Progress
             * @description Avisos que el propietario tiene en la mano.
             */
            in_progress: number;
            /**
             * Pending
             * @description Avisos en estado `open`, con independencia del filtro.
             */
            pending: number;
            /** Reports */
            reports: components["schemas"]["NoteReportSchema"][];
            /**
             * Reviewed
             * @description Avisos resueltos.
             */
            reviewed: number;
            /**
             * Total
             * @description Avisos que devuelve el filtro, contados en la base.
             */
            total: number;
        };
        /**
         * NoteReportSchema
         * @description Un aviso del alumno: qué apartado, qué dice, cuándo llegó y cómo acabó.
         *
         *     `section_title` es `None` cuando el apartado ya no existe —los apuntes se reescriben—: el aviso
         *     se sigue enseñando, y ese hueco es justo lo que hay que mirar. `resolution_note` es lo que el
         *     propietario escribió de lo que hizo, y `reviewed_at` cuándo lo cerró (vuelve a estar vacío si lo
         *     reabre).
         */
        NoteReportSchema: {
            /** Anchor */
            anchor: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Id */
            id: string;
            /** Reason */
            reason: string;
            /** Resolution Note */
            resolution_note?: string | null;
            /** Reviewed At */
            reviewed_at?: string | null;
            /** Section Key */
            section_key: string;
            /** Section Title */
            section_title?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "in_progress" | "reviewed" | "dismissed";
            /** Topic Code */
            topic_code: string;
            /** Topic Title */
            topic_title: string;
        };
        /**
         * NoteReportUpdateSchema
         * @description Lo único que se puede cambiar de un aviso: en qué punto está y qué se ha hecho.
         *
         *     `note` es potestativa a propósito. El motivo del alumno es obligatorio porque un aviso sin él no
         *     se puede arreglar; la nota del propietario no, porque hay avisos que se cierran sin nada que
         *     escribir. Cuando viene, es **una línea** (el servidor la recorta) y sustituye a la que hubiera;
         *     cuando no viene, la que hubiera se queda.
         */
        NoteReportUpdateSchema: {
            /** Actor */
            actor?: string | null;
            /** Note */
            note?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "in_progress" | "reviewed" | "dismissed";
        };
        /**
         * NotesIncidentListSchema
         * @description Las incidencias de una página, con **las cuatro cifras** de la bandeja.
         *
         *     Los recuentos van aparte de la lista aunque se puedan contar de ella, y son de la **bandeja
         *     entera**, no del filtro: `total` es lo que devuelve el filtro (contado en la base), y
         *     `totals_by_category` las cuatro categorías con su número real. Es lo que permite que la pantalla
         *     diga «291 de norma cambiada» sin leerse las 453, y sin heredar la cifra de ningún documento.
         *
         *     Los cuatro estados salen siempre, con cero incluido: un botón de filtro que desaparece cuando su
         *     número es cero obliga a la pantalla a inventarse la ausencia.
         */
        NotesIncidentListSchema: {
            /**
             * Dismissed
             * @description Incidencias descartadas: el motor se equivocaba.
             */
            dismissed: number;
            /**
             * In Progress
             * @description Incidencias que el propietario tiene en la mano.
             */
            in_progress: number;
            /** Incidents */
            incidents: components["schemas"]["NotesIncidentSchema"][];
            /**
             * Pending
             * @description Incidencias en `open`, con independencia del filtro.
             */
            pending: number;
            /**
             * Reviewed
             * @description Incidencias ya resueltas.
             */
            reviewed: number;
            /**
             * Total
             * @description Incidencias que devuelve el filtro, contadas en la base.
             */
            total: number;
            /** Totals By Category */
            totals_by_category?: {
                [key: string]: number;
            };
        };
        /**
         * NotesIncidentSchema
         * @description Una incidencia del motor, con lo que hace falta para juzgarla y para ir a mirarla.
         *
         *     Cuatro bloques, y cada uno existe por algo:
         *
         *     1. **qué es**: la categoría, el motivo y el texto del dominio que explica por qué el motor la
         *        señaló (`category_help`), más el detalle que escribió la corrida (`detail`) y la frase
         *        verificada (`phrase`) cuando la hay;
         *     2. **dónde**: el tema, el apartado del que habla (`anchor` y `section_title`) y —lo que permite
         *        juzgarla sin abrir nada— el enunciado de la pregunta (`stem`). `section_title` es nulo cuando
         *        la pregunta **no se pudo situar en ninguna materia**: eso no es un dato que falte, es el
         *        hallazgo, y la pantalla lo dice en vez de mandar a un ancla que no está;
         *     3. **de dónde sale la clave**: el conjunto del que es la pregunta (`set_title`) y el material
         *     con
         *        su versión y su estado (`source_*`). Cuando la categoría es «norma cambiada», la
         *        contradicción
         *        tiene dos mitades y esta es la segunda;
         *     4. **cómo acabó**: el estado, la nota de lo que se hizo y cuándo se cerró.
         */
        NotesIncidentSchema: {
            /** Anchor */
            anchor: string;
            /** Attempts */
            attempts: number;
            /**
             * Category
             * @enum {string}
             */
            category: "hueco_sin_material" | "clave_sospechosa" | "pregunta_ambigua" | "norma_cambiada" | "pregunta_mal_importada" | "clave_no_fiable";
            /** Category Help */
            category_help: string;
            /**
             * Coverage
             * @enum {string}
             */
            coverage: "doubtful" | "conflict";
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Detail */
            detail: string;
            /** Id */
            id: string;
            /** Phrase */
            phrase?: string | null;
            /** Question Version Id */
            question_version_id: string;
            /**
             * Reason
             * @enum {string}
             */
            reason: "sin_frase_en_los_apuntes" | "letra_no_coincide" | "clave_contradice_la_norma" | "clave_sin_definir" | "sin_materia_en_el_indice";
            /** Resolution Note */
            resolution_note?: string | null;
            /** Reviewed At */
            reviewed_at?: string | null;
            /** Section Title */
            section_title?: string | null;
            /** Set Title */
            set_title: string;
            /** Source Document Id */
            source_document_id?: string | null;
            /** Source Document Title */
            source_document_title?: string | null;
            /** Source Document Type */
            source_document_type?: string | null;
            /** Source Version Label */
            source_version_label?: string | null;
            /** Source Version Status */
            source_version_status?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "in_progress" | "reviewed" | "dismissed" | "propuesta_lista" | "no_son_preguntas";
            /** Stem */
            stem: string;
            /** Topic Code */
            topic_code: string;
            /** Topic Title */
            topic_title: string;
        };
        /**
         * NotesIncidentUpdateSchema
         * @description Lo único que se puede cambiar de una incidencia: en qué punto está y qué se ha hecho.
         *
         *     No hay ruta para editarla ni para borrarla. La incidencia la escribió una comprobación y lo que
         *     la resuelve es otra cosa: añadir material, revisar una clave, reescribir una pregunta o
         *     comprobar la norma. Lo que el propietario decide aquí es **qué ha hecho con ella**, y eso se
         *     escribe.
         *
         *     `note` es potestativa, como en el aviso del alumno: hay incidencias que se cierran sin nada que
         *     escribir. Cuando viene, es **una línea** y sustituye a la que hubiera; cuando no viene, la que
         *     hubiera se queda.
         */
        NotesIncidentUpdateSchema: {
            /** Actor */
            actor?: string | null;
            /** Note */
            note?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "in_progress" | "reviewed" | "dismissed" | "propuesta_lista" | "no_son_preguntas";
        };
        /**
         * NotesReviewChecksSchema
         * @description Las comprobaciones guardadas del tema, contadas en la base.
         *
         *     No son la puerta de cobertura —esa tiene otro denominador— y por eso van con su propio nombre:
         *     «de las preguntas que el motor ha comprobado, cuántas quedaron cubiertas, sin frase, dudosas o
         *     en conflicto con su respuesta correcta».
         */
        NotesReviewChecksSchema: {
            /** Conflicts */
            conflicts: number;
            /** Covered */
            covered: number;
            /** Doubtful */
            doubtful: number;
            /** Gaps */
            gaps: number;
            /** Total */
            total: number;
        };
        /**
         * NotesReviewCountersSchema
         * @description Los números de la cabecera: cuántos temas hay de cada clase y cuántos esperan decisión.
         */
        NotesReviewCountersSchema: {
            /**
             * Approved
             * @description Con una decisión de aprobación escrita por el propietario.
             */
            approved: number;
            /**
             * Draft
             * @description Con apuntes escritos y **sin** versión archivada.
             */
            draft: number;
            /**
             * Pending Decision
             * @description Borradores sin aprobar: es lo que espera al propietario.
             */
            pending_decision: number;
            /**
             * Published
             * @description Con versión archivada: se leen como publicados.
             */
            published: number;
            /**
             * Rejected
             * @description Rechazados: esperan a que el texto se arregle.
             */
            rejected: number;
            /**
             * Topics Total
             * @description Temas del programa activo.
             */
            topics_total: number;
            /**
             * With Notes
             * @description Temas con apuntes escritos.
             */
            with_notes: number;
            /**
             * Without Notes
             * @description Temas que todavía no tienen apuntes escritos.
             */
            without_notes: number;
        };
        /**
         * NotesReviewDecisionRequestSchema
         * @description Aprobar o rechazar los apuntes de un tema, con la nota de lo decidido.
         *
         *     La nota es **opcional al aprobar** y **obligatoria al rechazar**: un rechazo sin motivo deja el
         *     borrador donde estaba y encima sin saber por qué. Lo comprueba el esquema (para contestar un 422
         *     con su campo) y lo vuelve a comprobar el dominio (para cualquier camino que no pase por aquí).
         *
         *     `validate_default` no es decorativo: sin él, un cuerpo que **no trae** `note` no pasa por el
         *     validador del campo —pydantic no valida los campos que no vienen— y el rechazo sin motivo se
         *     colaba hasta la última línea, donde solo quedaba un 500. Con él, el validador corre también
         *     cuando la nota no viene, y el 422 señala `note`, que es el campo que hay que rellenar.
         */
        NotesReviewDecisionRequestSchema: {
            /**
             * Actor
             * @description Quién decide. Si no viene, la cabecera `X-OpoFuente-Actor`; si no, `local`.
             */
            actor?: string | null;
            /**
             * Decision
             * @enum {string}
             */
            decision: "approved" | "rejected";
            /** Note */
            note?: string | null;
        };
        /**
         * NotesReviewDecisionResultSchema
         * @description Lo que ha pasado al decidir: la decisión y **si eso ha publicado** el tema.
         *
         *     `published` no es «aprobado»: aprobar un tema que no pasa las puertas lo deja aprobado y sin
         *     publicar, y `blocked_by` dice cuál de las dos lo frena. El listón no se toca.
         */
        NotesReviewDecisionResultSchema: {
            /**
             * Blocked By
             * @description Qué puerta impide publicar, cuando el tema está aprobado y no sale.
             */
            blocked_by?: ("cobertura" | "forma") | null;
            /** Published */
            published: boolean;
            topic: components["schemas"]["NotesReviewTopicSchema"];
            /**
             * Version Created
             * @description Si la aprobación ha archivado una versión nueva. `false` si la que había ya era la misma lectura; `null` si no se ha intentado archivar.
             */
            version_created?: boolean | null;
        };
        /**
         * NotesReviewDecisionSchema
         * @description Lo que el propietario decidió sobre un tema, con su nota, su fecha y quién lo firmó.
         */
        NotesReviewDecisionSchema: {
            /** Actor */
            actor: string;
            /**
             * Decision
             * @enum {string}
             */
            decision: "approved" | "rejected";
            /** Note */
            note?: string | null;
            /**
             * Reviewed At
             * Format: date-time
             */
            reviewed_at: string;
        };
        /**
         * NotesReviewFileSchema
         * @description Una **página** de la ficha de un tema: su fila de la tabla y los apartados de la hoja.
         *
         *     `sections_total` es el número de apartados del tema y no el de la hoja: el título de la pantalla
         *     dice cuántos hay, y la hoja que se está mirando se sabe por `page` y `pages`.
         */
        NotesReviewFileSchema: {
            /**
             * Page
             * @description La hoja que va en `sections`, empezando por 1.
             * @default 1
             */
            page: number;
            /**
             * Page Size
             * @description Cuántos apartados caben en una hoja.
             * @default 6
             */
            page_size: number;
            /**
             * Pages
             * @description Cuántas hojas tiene la ficha.
             * @default 1
             */
            pages: number;
            /**
             * Sections
             * @description Los apartados de la hoja servida, en el orden pedido. Vacío si el tema no tiene texto escrito.
             */
            sections: components["schemas"]["NotesReviewSectionSchema"][];
            /**
             * Sections Total
             * @description Apartados que tiene el tema entero, sumando todas las hojas.
             * @default 0
             */
            sections_total: number;
            topic: components["schemas"]["NotesReviewTopicSchema"];
        };
        /**
         * NotesReviewListSchema
         * @description La tabla entera, con los contadores de la cabecera.
         */
        NotesReviewListSchema: {
            counters: components["schemas"]["NotesReviewCountersSchema"];
            /**
             * Topics
             * @description Los temas del programa activo, en orden del temario. Siempre la lista entera.
             */
            topics: components["schemas"]["NotesReviewTopicSchema"][];
        };
        /**
         * NotesReviewReasonSchema
         * @description Por qué un tema está como está, en una frase con su cifra.
         *
         *     `code` es el vocabulario del dominio (para filtrar o probar) y `text` lo que se lee. El orden de
         *     la lista **es** el orden de lectura: la primera razón es el titular.
         */
        NotesReviewReasonSchema: {
            /**
             * Code
             * @description El código del motivo, del vocabulario del dominio.
             */
            code: string;
            /**
             * Figure
             * @description La cifra sola, para pintarla aparte del texto.
             */
            figure?: string | null;
            /**
             * Text
             * @description La frase, ya compuesta con su cifra.
             */
            text: string;
        };
        /**
         * NotesReviewSectionSchema
         * @description Un apartado de los apuntes, tal como se lee, con lo que se ha comprobado en él.
         */
        NotesReviewSectionSchema: {
            /** Anchor */
            anchor: string;
            /** Body Markdown */
            body_markdown: string;
            /** Conflicts */
            conflicts: number;
            /** Covered */
            covered: number;
            /** Doubtful */
            doubtful: number;
            /** Epigraph Code */
            epigraph_code: string;
            /** Facts Total */
            facts_total: number;
            /** Gaps */
            gaps: number;
            /** Key */
            key: string;
            /** Needs Review Reason */
            needs_review_reason?: string | null;
            /**
             * Position
             * @description El número con el que se lee, en orden de lectura.
             */
            position: number;
            /** Title */
            title: string;
            /** Words */
            words: number;
            /**
             * Worst
             * @description Cuánto queda sin resolver en este apartado (conflictos + dudosas + sin frase): es lo que ordena «los peores primero».
             */
            worst: number;
        };
        /**
         * NotesReviewTopicSchema
         * @description Una fila de la tabla: el tema, su estado, sus cifras, su motivo y su decisión.
         */
        NotesReviewTopicSchema: {
            /** Block Code */
            block_code: string;
            /** Block Title */
            block_title: string;
            checks: components["schemas"]["NotesReviewChecksSchema"];
            /**
             * Code
             * @description Código legible del tema, como `IV.7`.
             */
            code: string;
            /**
             * Coverage
             * @description `(cubiertas, con clave utilizable)`: el par que decide la puerta del §2.3.
             */
            coverage?: [
                number,
                number
            ] | null;
            /**
             * Coverage All Keys
             * @description `(cubiertas, con clave)` sobre **todas** las que tienen clave. Se enseña.
             */
            coverage_all_keys?: [
                number,
                number
            ] | null;
            /**
             * Coverage Threshold
             * @description El listón del §2.3, que no se toca.
             * @default 0.9
             */
            coverage_threshold: number;
            /**
             * Facts
             * @description Hechos guardados del tema (paso B).
             */
            facts: number;
            /**
             * Incidents By Category
             * @description Esas incidencias, por categoría. Vacío cuando no hay ninguna.
             */
            incidents_by_category: {
                [key: string]: number;
            };
            /**
             * Incidents Open
             * @description Incidencias del motor sin despachar de este tema.
             */
            incidents_open: number;
            /**
             * Measured
             * @description Si esta lectura ha medido la cobertura del tema (sin modelo y sin coste).
             */
            measured: boolean;
            /**
             * Reasons
             * @description Por qué el tema está como está, con sus cifras. Vacío en los temas publicados que la tabla no mide (ya pasaron las puertas): su ficha sí los mide.
             */
            reasons: components["schemas"]["NotesReviewReasonSchema"][];
            review?: components["schemas"]["NotesReviewDecisionSchema"] | null;
            /**
             * Sections Written
             * @description Apartados con texto.
             */
            sections_written: number;
            /**
             * State
             * @description `published`, `draft` o `none`.
             * @enum {string}
             */
            state: "published" | "draft" | "none";
            /** Title */
            title: string;
            version?: components["schemas"]["NotesReviewVersionSchema"] | null;
        };
        /**
         * NotesReviewVersionSchema
         * @description La versión archivada de un tema: lo que lo hace «publicado».
         */
        NotesReviewVersionSchema: {
            /**
             * Built At
             * Format: date-time
             */
            built_at: string;
            /** Id */
            id: string;
        };
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
        /**
         * OutdatedSessionsSchema
         * @description Sesiones terminadas del conjunto que no están corregidas con su plantilla activa (DEBT-013).
         *
         *     Los tres recuentos —al día, desactualizadas y sin corrección guardada— suman las terminadas: si
         *     se solaparan, el número que la pantalla enseña no se podría comprobar.
         */
        OutdatedSessionsSchema: {
            /** Detail */
            detail: string;
            /** Finished */
            finished: number;
            /** Key Id */
            key_id: string;
            /** Key Version */
            key_version: number;
            /** Outdated */
            outdated: number;
            /** Outdated Session Ids */
            outdated_session_ids: string[];
            /** Question Set Id */
            question_set_id: string;
            /** Up To Date */
            up_to_date: number;
            /** Without Evaluation */
            without_evaluation: number;
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
            kind: "direct" | "scaled" | "estimated" | "pass_fail";
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
        /** PasswordResetConfirmSchema */
        PasswordResetConfirmSchema: {
            /** Password */
            password: string;
            /** Token */
            token: string;
        };
        /** PasswordResetRequestSchema */
        PasswordResetRequestSchema: {
            /** Email */
            email: string;
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
         * PatchQuestionSetSchema
         * @description Lo que se puede cambiar de un conjunto sin tocar su contenido.
         *
         *     La **visibilidad** (un conjunto nace `personal` y se hace `public` a propósito, uno a uno) y la
         *     **procedencia** (`origin_scope`, que es lo que deja el material de otra administración fuera de
         *     un simulacro). Nada más se cambia por aquí — el título y el tipo son la identidad del conjunto,
         *     y reescribirlos rompería la trazabilidad de las preguntas que cuelgan de él.
         *
         *     Los dos campos son opcionales pero **al menos uno** tiene que venir: un `PATCH` que no cambia
         *     nada es un error de quien llama, no una operación correcta.
         */
        PatchQuestionSetSchema: {
            /** Distribution */
            distribution?: ("personal" | "public") | null;
            /** Origin Scope */
            origin_scope?: ("age" | "otra_administracion" | "desconocida") | null;
        };
        /**
         * PaymentCostSchema
         * @description Una línea de coste, con la marca de si se ha podido comprobar.
         */
        PaymentCostSchema: {
            /** Amount */
            amount: string;
            /** Concept */
            concept: string;
            /** Verified */
            verified: boolean;
        };
        /**
         * PaymentGatewaySchema
         * @description Una pasarela considerada: por qué, qué contratar, qué costaría y qué datos saldrían.
         */
        PaymentGatewaySchema: {
            /** Costs */
            costs: components["schemas"]["PaymentCostSchema"][];
            /** Integration Effort */
            integration_effort: string;
            /** Invoices In Spain */
            invoices_in_spain: string;
            /** Key */
            key: string;
            /** Name */
            name: string;
            /** Personal Data To Third Party */
            personal_data_to_third_party: string[];
            /** Price Page */
            price_page: string;
            /** Recommended */
            recommended: boolean;
            /** Rejected Because */
            rejected_because: string;
            /** What To Contract */
            what_to_contract: string[];
            /** Why */
            why: string;
        };
        /**
         * PaymentPlanSchema
         * @description Un hueco de plan. Sin precio decidido: eso no lo decide este bloque.
         */
        PaymentPlanSchema: {
            /** Detail */
            detail: string;
            /** Key */
            key: string;
            /** Name */
            name: string;
            /** Price */
            price: string;
        };
        /**
         * PaymentsSchema
         * @description El estado de los pagos: apagados, con la propuesta escrita y nada contratado.
         */
        PaymentsSchema: {
            /** Enabled */
            enabled: boolean;
            /** Gateways */
            gateways: components["schemas"]["PaymentGatewaySchema"][];
            /** Notice */
            notice: string;
            /** Plans */
            plans: components["schemas"]["PaymentPlanSchema"][];
            /** Provider */
            provider: string;
            /** Status */
            status: string;
        };
        /**
         * PendingActionSchema
         * @description Algo que espera a una persona, con la cifra y la pantalla donde se resuelve.
         */
        PendingActionSchema: {
            /** Count */
            count: number;
            /** Detail */
            detail: string;
            /** Href */
            href: string;
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Title */
            title: string;
        };
        /**
         * PendingActionsSchema
         * @description Todo lo que espera a una persona ahora mismo, ya ordenado.
         */
        PendingActionsSchema: {
            /** Actions */
            actions: components["schemas"]["PendingActionSchema"][];
            /** Total */
            total: number;
        };
        /**
         * PendingSchema
         * @description Solo el numero: lo que la cola ensena antes de empezar.
         */
        PendingSchema: {
            /** Vencen */
            vencen: number;
        };
        /**
         * PlanGuardadoSchema
         * @description Lo que hay guardado, o `null` si nadie ha puesto la fecha.
         */
        PlanGuardadoSchema: {
            /** Exam Date */
            exam_date?: string | null;
            /** Hours Per Week */
            hours_per_week?: number | null;
            /** Rest Days */
            rest_days?: number[];
        };
        /**
         * PlanSchema
         * @description El plan entero, **con lo que no cabe dicho**.
         */
        PlanSchema: {
            /** Cabe Todo */
            cabe_todo: boolean;
            /** Dentro */
            dentro: string[];
            /**
             * Fuera
             * @description Los temas que no entran antes del examen
             */
            fuera: string[];
            /** Semanas */
            semanas: components["schemas"]["opofuente__api__routes__plan__SemanaSchema"][];
        };
        /**
         * PlatformPolicySchema
         * @description **Una sola llamada** para saber qué está encendido en esta instalación.
         *
         *     Existe porque la web se construye una vez y se sirve en varias configuraciones: si las banderas
         *     se hornearan en el paquete, habría que construir dos veces la misma aplicación para probar la
         *     versión con cuentas y la versión sin ellas, y las dos acabarían divergiendo. Se pregunta al
         *     servidor en cada arranque, y lo que diga el servidor es lo que hay.
         *
         *     Es pública a propósito: dice qué funciones están encendidas, no nada de nadie.
         */
        PlatformPolicySchema: {
            accounts: components["schemas"]["AccountsPolicySchema"];
            analytics: components["schemas"]["AnalyticsPolicySchema"];
            legal: components["schemas"]["LegalPolicySchema"];
            /** Payments */
            payments: boolean;
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
         * ProgrammeNodeRefSchema
         * @description Un nodo del programa dentro de una propuesta: sus dos códigos y su título.
         *
         *     `official_code` es el número que publica la convocatoria («1») y `path` la posición legible del
         *     árbol («I.1»), que es la que el propietario reconoce en la pantalla.
         */
        ProgrammeNodeRefSchema: {
            /** Node Id */
            node_id: string;
            /** Official Code */
            official_code: string;
            /** Path */
            path: string;
            /** Title */
            title: string;
        };
        /**
         * ProgresoSchema
         * @description Como va el alumno respecto al plan, con la frase ya compuesta.
         */
        ProgresoSchema: {
            /** Esperados */
            esperados: number;
            /** Frase */
            frase: string;
            /** Leidos */
            leidos: number;
            /** Practicados */
            practicados: number;
            /** Total */
            total: number;
            /** Vas Bien */
            vas_bien: boolean;
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
            /** Question Set Id */
            question_set_id?: string | null;
            /**
             * Questions Catalogued
             * @default 0
             */
            questions_catalogued: number;
            /**
             * Questions Imported
             * @default 0
             */
            questions_imported: number;
            /** Questions Note */
            questions_note?: string | null;
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
        /**
         * PurgeRequestSchema
         * @description Qué retirar y con qué confirmación.
         *
         *     `confirm` es obligatorio y tiene que ser `true`: retirar material es una decisión, y el contrato
         *     pide que no pueda ocurrir por accidente. Se exige en el **mismo** cuerpo que las referencias,
         *     no en un segundo parámetro, para que no haya dos formas de pedir lo mismo.
         */
        PurgeRequestSchema: {
            /**
             * Confirm
             * @description debe ser `true`: retirar material no se hace por accidente
             */
            confirm: boolean;
            /** References */
            references?: string[] | null;
        };
        /** PurgeResultSchema */
        PurgeResultSchema: {
            /** Action */
            action: string;
            /** Detail */
            detail: string;
            /** Freed Bytes */
            freed_bytes: number;
            /** Removed */
            removed: number;
            /** Skipped */
            skipped: string[];
        };
        /**
         * QuestionCountSchema
         * @description Cuántas preguntas de un estado tiene un nodo (DEBT-027 §5).
         */
        QuestionCountSchema: {
            /** Count */
            count: number;
            /** Status */
            status: string;
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
         * QuestionExclusionPageSchema
         * @description La cola de fuera de temario: las marcas de una página y cuántas hay en total.
         *
         *     `totals_by_reason` cuenta **cada** motivo en la base, sin mirar el filtro de la petición: es lo
         *     que permite que la sección «No son preguntas» del panel (F16, decisión D6) diga cuántos
         *     enunciados rotos hay sin leerlos para contarlos. Un motivo sin ninguna marca no aparece.
         */
        QuestionExclusionPageSchema: {
            /** Exclusions */
            exclusions: components["schemas"]["QuestionExclusionSchema"][];
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Total */
            total: number;
            /** Totals By Reason */
            totals_by_reason?: {
                [key: string]: number;
            };
        };
        /**
         * QuestionExclusionSchema
         * @description Una pregunta declarada fuera del temario, con su motivo.
         *
         *     No lleva código de tema ni nodo: **no es un mapeo**, y por eso no se puede confundir con uno.
         *     Sí lleva el enunciado, que es lo que permite juzgar si la marca estaba bien puesta; al escribir
         *     la marca va nulo, porque ahí no hay nada que revisar.
         */
        QuestionExclusionSchema: {
            /** Actor */
            actor: string;
            /** Created At */
            created_at?: string | null;
            /** Note */
            note?: string | null;
            /** Question Version Id */
            question_version_id: string;
            /**
             * Reason
             * @enum {string}
             */
            reason: "otra_administracion" | "enunciado_roto";
            /** Stem */
            stem?: string | null;
        };
        /** QuestionFileExclusionSchema */
        QuestionFileExclusionSchema: {
            /** Actor */
            actor: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Note */
            note: string | null;
            /**
             * Reason
             * @enum {string}
             */
            reason: "otra_administracion" | "enunciado_roto";
        };
        /** QuestionFileIncidentSchema */
        QuestionFileIncidentSchema: {
            /**
             * Category
             * @enum {string}
             */
            category: "hueco_sin_material" | "clave_sospechosa" | "pregunta_ambigua" | "norma_cambiada" | "pregunta_mal_importada" | "clave_no_fiable";
            /**
             * Coverage
             * @enum {string}
             */
            coverage: "doubtful" | "conflict";
            /** Detail */
            detail: string;
            /** Id */
            id: string;
            /** Phrase */
            phrase: string | null;
            /** Reason */
            reason: string;
            /** Resolution Note */
            resolution_note: string | null;
            /** Reviewed At */
            reviewed_at: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "in_progress" | "reviewed" | "dismissed";
            /** Topic Code */
            topic_code: string;
            /** Topic Title */
            topic_title: string;
        };
        /**
         * QuestionFileKeySchema
         * @description La respuesta correcta que manda hoy y **de dónde sale**.
         */
        QuestionFileKeySchema: {
            /** Answer Key Version Id */
            answer_key_version_id: string;
            /** Approved At */
            approved_at: string | null;
            /** Correct Option Keys */
            correct_option_keys: string[];
            /** Notes */
            notes: string | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "keyed" | "annulled" | "unanswered" | "conflicting";
            /** Published At */
            published_at: string | null;
            /** Source Document Id */
            source_document_id: string | null;
            /** Source Document Title */
            source_document_title: string | null;
            /** Source Document Type */
            source_document_type: string | null;
            /** Source Version Label */
            source_version_label: string | null;
            /** Source Version Status */
            source_version_status: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "active" | "superseded" | "rejected";
            /** Version No */
            version_no: number;
        };
        /** QuestionFileKeyVersionSchema */
        QuestionFileKeyVersionSchema: {
            /** Approved At */
            approved_at: string | null;
            /** Correct Option Keys */
            correct_option_keys: string[];
            /** Created At */
            created_at: string | null;
            /** Id */
            id: string;
            /** Source Document Title */
            source_document_title: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "active" | "superseded" | "rejected";
            /** Version No */
            version_no: number;
        };
        /**
         * QuestionFileNotesSchema
         * @description Lo que contestan los apuntes, con el apartado y la frase verificada.
         */
        QuestionFileNotesSchema: {
            /** Anchor */
            anchor: string;
            /** Answer Letter */
            answer_letter: string | null;
            /** Checked At */
            checked_at: string | null;
            /** Coincides */
            coincides: boolean;
            /** Expected Letters */
            expected_letters: string[];
            /**
             * Key Status
             * @enum {string}
             */
            key_status: "active" | "draft" | "ninguna";
            /** Phrase */
            phrase: string | null;
            /** Result */
            result: ("covered" | "gap" | "doubtful" | "conflict") | null;
            /** Section Title */
            section_title: string | null;
            /** Topic Code */
            topic_code: string;
            /** Topic Title */
            topic_title: string;
        };
        /** QuestionFileOptionSchema */
        QuestionFileOptionSchema: {
            /** Label */
            label: string | null;
            /** Position */
            position: number;
            /** Stable Key */
            stable_key: string;
            /** Text */
            text: string;
        };
        /** QuestionFileProtectedSetSchema */
        QuestionFileProtectedSetSchema: {
            /** Id */
            id: string;
            /** Reason */
            reason: string;
            /** Set Type */
            set_type: string;
            /** Source Document Title */
            source_document_title: string | null;
            /** Title */
            title: string;
        };
        /** QuestionFileProtectionSchema */
        QuestionFileProtectionSchema: {
            /** Protected */
            protected: boolean;
            /** Reason */
            reason: string | null;
            /** Sets */
            sets: components["schemas"]["QuestionFileProtectedSetSchema"][];
        };
        /** QuestionFileRepairSchema */
        QuestionFileRepairSchema: {
            /** Detalle */
            detalle: string;
            /** Opciones */
            opciones: string[] | null;
            /** Por Que No */
            por_que_no: string | null;
            /** Reglas */
            reglas: string[];
            /** Stem */
            stem: string | null;
            /** Titulos */
            titulos: string[];
        };
        /**
         * QuestionFileSchema
         * @description La ficha entera de una pregunta.
         */
        QuestionFileSchema: {
            /** Created At */
            created_at: string | null;
            exclusion: components["schemas"]["QuestionFileExclusionSchema"] | null;
            /** Incidents */
            incidents: components["schemas"]["QuestionFileIncidentSchema"][];
            /** Is Reserve */
            is_reserve: boolean;
            key: components["schemas"]["QuestionFileKeySchema"] | null;
            /** Key Reliability */
            key_reliability: ("fiable" | "dudosa" | "no_fiable") | null;
            /** Keys */
            keys: components["schemas"]["QuestionFileKeyVersionSchema"][];
            /** Note */
            note: string | null;
            /** Notes */
            notes: components["schemas"]["QuestionFileNotesSchema"][];
            /** Options */
            options: components["schemas"]["QuestionFileOptionSchema"][];
            /**
             * Origin Type
             * @enum {string}
             */
            origin_type: "official" | "private" | "generated";
            /** Position */
            position: number;
            protection: components["schemas"]["QuestionFileProtectionSchema"];
            /** Question Set Id */
            question_set_id: string;
            /**
             * Question Type
             * @enum {string}
             */
            question_type: "single_choice" | "multi_mark_error" | "true_false" | "free_text_reference";
            /** Question Version Id */
            question_version_id: string;
            /** Reliability Source */
            reliability_source: string;
            repair: components["schemas"]["QuestionFileRepairSchema"];
            /** Reserve Order */
            reserve_order: number | null;
            /**
             * Set Distribution
             * @enum {string}
             */
            set_distribution: "personal" | "public";
            /** Set Title */
            set_title: string;
            /**
             * Set Type
             * @enum {string}
             */
            set_type: "official_exam" | "private_bank" | "practice" | "generated_batch";
            /** Stable Key */
            stable_key: string;
            /**
             * Status
             * @enum {string}
             */
            status: "incomplete" | "complete" | "verified" | "conflicting" | "annulled" | "superseded";
            /** Stem */
            stem: string;
            /** Superseded By */
            superseded_by: string | null;
            /** Version No */
            version_no: number;
            /** Versions */
            versions: components["schemas"]["QuestionFileVersionSchema"][];
        };
        /** QuestionFileVersionSchema */
        QuestionFileVersionSchema: {
            /** Correct Option Keys */
            correct_option_keys: string[];
            /** Created At */
            created_at: string | null;
            /** Id */
            id: string;
            /** Note */
            note: string | null;
            /** Option Count */
            option_count: number;
            /**
             * Status
             * @enum {string}
             */
            status: "incomplete" | "complete" | "verified" | "conflicting" | "annulled" | "superseded";
            /** Stem */
            stem: string;
            /** Version No */
            version_no: number;
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
             * Evidence Links
             * @default 0
             */
            evidence_links: number;
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
            /**
             * Mapped To Topics
             * @default 0
             */
            mapped_to_topics: number;
            /** Missing Columns */
            missing_columns: string[];
            /** Model Code Detected */
            model_code_detected?: string | null;
            /**
             * Option Explanations
             * @default 0
             */
            option_explanations: number;
            /** Parts Detected */
            parts_detected?: string[];
            /** Rejected */
            rejected: components["schemas"]["RejectedRowSchema"][];
            /** Set Id */
            set_id: string;
            /**
             * Topics From Column
             * @default 0
             */
            topics_from_column: number;
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
            /**
             * Distribution
             * @default personal
             * @enum {string}
             */
            distribution: "personal" | "public";
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
             * Origin Scope
             * @default desconocida
             * @enum {string}
             */
            origin_scope: "age" | "otra_administracion" | "desconocida";
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
         * QuestionTopicAssignmentSchema
         * @description El mapeo y si **esta** llamada lo creó.
         *
         *     `created` es lo que hace utilizable una ruta idempotente: reintentar la clasificación de un lote
         *     entero no puede confundir «lo asigné yo ahora» con «ya estaba asignado».
         *
         *     `promoted` es la tercera cosa que puede pasar, y la que necesita la cola de revisión: el mapeo
         *     ya estaba, pero como **propuesta**, y esta llamada la ha confirmado. No es «creado» —la fila
         *     existía— ni «ya estaba» —algo se ha escrito y queda auditado—.
         *
         *     `epigraph` viaja cuando se pidió asignar también un epígrafe: se asigna con su tema, y decir
         *     solo el tema escondería la mitad de lo que se ha escrito.
         *
         *     `retired` son las propuestas **de esa pregunta** que se han retirado en la misma operación: una
         *     pregunta no puede quedarse con dos temas propuestos cuando uno se acepta, y quien decide tiene
         *     que ver que las demás ya no están.
         */
        QuestionTopicAssignmentSchema: {
            /**
             * Confidence
             * @default 1
             */
            confidence: number;
            /** Created */
            created: boolean;
            /** Created At */
            created_at?: string | null;
            /** Curriculum Node Id */
            curriculum_node_id: string;
            epigraph?: components["schemas"]["QuestionTopicAssignmentSchema"] | null;
            /** Mapping Id */
            mapping_id: string;
            /** Official Code */
            official_code: string;
            /**
             * Promoted
             * @default false
             */
            promoted: boolean;
            /** Question Version Id */
            question_version_id: string;
            /**
             * Retired
             * @default 0
             */
            retired: number;
            /**
             * Status
             * @enum {string}
             */
            status: "provisional" | "accepted" | "rejected";
            /** Title */
            title: string;
        };
        /**
         * QuestionTopicConflictPageSchema
         * @description Las preguntas en dos temas de una página, y cuántas hay en total.
         */
        QuestionTopicConflictPageSchema: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Questions */
            questions: components["schemas"]["QuestionTopicConflictSchema"][];
            /** Total */
            total: number;
        };
        /**
         * QuestionTopicConflictSchema
         * @description Una pregunta que cuenta en **dos temas aceptados** a la vez, con los dos delante.
         *
         *     Es la otra cara de la cola: allí se revisa lo que nadie ha decidido y aquí lo que quedó decidido
         *     dos veces. Una pregunta en dos temas cuenta en los dos agregados, así que hay que poder dejarla
         *     con uno —eligiendo cuál— sin que la aplicación decida por su cuenta.
         */
        QuestionTopicConflictSchema: {
            /** Options */
            options: components["schemas"]["OptionSchema"][];
            /** Question Set Id */
            question_set_id: string;
            /** Question Version Id */
            question_version_id: string;
            /** Set Title */
            set_title: string;
            /** Stem */
            stem: string;
            /** Topics */
            topics: components["schemas"]["ConflictingTopicSchema"][];
        };
        /**
         * QuestionTopicProposalPageSchema
         * @description La cola de propuestas, contada en **preguntas** (tarjetas): las de una página y el total.
         */
        QuestionTopicProposalPageSchema: {
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
            /** Questions */
            questions: components["schemas"]["QuestionTopicProposalsSchema"][];
            /** Total */
            total: number;
        };
        /**
         * QuestionTopicProposalSchema
         * @description Un tema candidato para una pregunta, sin confirmar, con sus epígrafes propuestos.
         *
         *     No lleva la pregunta dentro: la pregunta es la tarjeta (`QuestionTopicProposalsSchema`) y esto
         *     es una de las respuestas que la máquina le dio.
         */
        QuestionTopicProposalSchema: {
            /** Confidence */
            confidence: number;
            /** Created At */
            created_at?: string | null;
            /** Epigraphs */
            epigraphs: components["schemas"]["ProgrammeNodeRefSchema"][];
            /** Mapping Id */
            mapping_id: string;
            /** Reason */
            reason?: string | null;
            topic: components["schemas"]["ProgrammeNodeRefSchema"];
        };
        /**
         * QuestionTopicProposalsSchema
         * @description Una pregunta de la cola con **todas** sus propuestas juntas: una tarjeta, no una por mapeo.
         *
         *     Es la unidad con la que se despacha: el propietario decide sobre la pregunta —«esta pregunta es
         *     del tema X»—, así que el mismo enunciado no puede salir dos veces. `accepted` va aparte de
         *     `proposals`: si la pregunta ya tiene tema decidido, ese manda y lo que queda son propuestas que
         *     se retiran.
         */
        QuestionTopicProposalsSchema: {
            accepted?: components["schemas"]["ProgrammeNodeRefSchema"] | null;
            /** Options */
            options: components["schemas"]["OptionSchema"][];
            /** Proposals */
            proposals: components["schemas"]["QuestionTopicProposalSchema"][];
            /** Question Set Id */
            question_set_id: string;
            /** Question Version Id */
            question_version_id: string;
            /** Set Title */
            set_title: string;
            /** Stem */
            stem: string;
        };
        /**
         * QuestionTopicSchema
         * @description Un tema del programa asignado a una pregunta, con el estado de su mapeo.
         *
         *     `status` viaja a propósito: `accepted` es un tema decidido y `provisional` es lo que propuso un
         *     motor sin que nadie lo haya confirmado. El panel tiene que poder distinguirlos, y el diagnóstico
         *     por temas solo cuenta lo aceptado.
         */
        QuestionTopicSchema: {
            /**
             * Confidence
             * @default 1
             */
            confidence: number;
            /** Created At */
            created_at?: string | null;
            /** Curriculum Node Id */
            curriculum_node_id: string;
            /** Mapping Id */
            mapping_id: string;
            /** Official Code */
            official_code: string;
            /** Question Version Id */
            question_version_id: string;
            /**
             * Status
             * @enum {string}
             */
            status: "provisional" | "accepted" | "rejected";
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
        /**
         * ReindexSchema
         * @description Resultado de rehacer el índice léxico (DEBT-015).
         */
        ReindexSchema: {
            /** After */
            after: number;
            /** Before */
            before: number;
            /** Detail */
            detail: string;
            /** Indexed */
            indexed: number;
            /** Took Seconds */
            took_seconds: number;
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
         * RepairQuestionSchema
         * @description Repara lo que una regla mecánica pueda reparar de esta pregunta.
         *
         *     No se manda texto: lo que se escribe lo decide una regla del dominio sobre el enunciado y las
         *     opciones que ya hay. `reglas` solo puede **restringir** lo que el dominio ofrece.
         */
        RepairQuestionSchema: {
            /** Actor */
            actor?: string | null;
            /** Note */
            note: string;
            /** Reglas */
            reglas?: string[] | null;
        };
        /** RepairResultSchema */
        RepairResultSchema: {
            /** Actor */
            actor: string;
            /** Dispatched Incidents */
            dispatched_incidents: number;
            file: components["schemas"]["QuestionFileSchema"];
            /** Key Version Id */
            key_version_id: string | null;
            /** Moved Anchors */
            moved_anchors: number;
            /** Moved Exclusion */
            moved_exclusion: boolean;
            /** Moved Topics */
            moved_topics: number;
            /** New Question Version Id */
            new_question_version_id: string;
            /** Reglas */
            reglas: string[];
            /** Superseded Question Version Id */
            superseded_question_version_id: string;
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
         * Respuesta
         * @description Las cuatro respuestas de la pantalla, que es lo que el alumno puede decir.
         * @enum {string}
         */
        Respuesta: "otra_vez" | "dificil" | "bien" | "facil";
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
            /** Context Label */
            context_label?: string | null;
            /**
             * Feedback
             * @enum {string}
             */
            feedback: "immediate" | "at_end";
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam" | "mock_exam" | "diagnostic";
            /** Note */
            note?: string | null;
            /** Shuffle */
            shuffle: boolean;
            /** Sources */
            sources: components["schemas"]["SessionSourceSchema"][];
            /** Time Limit Minutes */
            time_limit_minutes?: number | null;
        };
        /**
         * SessionDiscardSchema
         * @description Qué se hizo al descartar una sesión: borrarla (no tenía respuestas) o abandonarla.
         */
        SessionDiscardSchema: {
            /**
             * Action
             * @enum {string}
             */
            action: "deleted" | "abandoned";
            /** Detail */
            detail: string;
            /** Session Id */
            session_id: string;
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
         * SessionRecalculationSchema
         * @description Lo que cambió en una sesión al recalcularla en bloque (DEBT-013).
         */
        SessionRecalculationSchema: {
            /** Changed */
            changed: boolean;
            /** New Key Label */
            new_key_label: string;
            /** New Total */
            new_total: string;
            /** Previous Key Label */
            previous_key_label: string;
            /** Previous Total */
            previous_total: string;
            /** Session Id */
            session_id: string;
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
            mode: "practice" | "error_review" | "official_exam" | "mock_exam" | "diagnostic";
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
            mode: "practice" | "error_review" | "official_exam" | "mock_exam" | "diagnostic";
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
         * SetExplanationRequestSchema
         * @description Escribir (o sustituir) la explicación de una pregunta o de una de sus opciones.
         */
        SetExplanationRequestSchema: {
            /** Option Stable Key */
            option_stable_key?: string | null;
            /** Text */
            text: string;
        };
        /**
         * SetExplanationStatusRequestSchema
         * @description Aprobar o rechazar una explicación generada desde la bandeja (M1 de la fase 3).
         *
         *     **Solo dos estados.** `draft` no se acepta: **devolver una explicación a la cola no es una
         *     acción** —se deshace aprobando otra vez o no se aprueba—, y `generated` es el origen, no un
         *     estado.
         */
        SetExplanationStatusRequestSchema: {
            /**
             * Status
             * @enum {string}
             */
            status: "reviewed" | "rejected";
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
        /** StatsSchema */
        StatsSchema: {
            /** Comparacion Del Tiempo */
            comparacion_del_tiempo?: string | null;
            /** Flojos */
            flojos: components["schemas"]["TemaFlojoSchema"][];
            nota?: components["schemas"]["NotaSchema"] | null;
            /** Segundos Por Pregunta */
            segundos_por_pregunta?: number | null;
            /** Semanas */
            semanas: components["schemas"]["opofuente__api__routes__stats__SemanaSchema"][];
        };
        /**
         * StudentAbandonSchema
         * @description Qué queda de un test abandonado, en las palabras que se le enseñan al alumno.
         *
         *     Va aparte de `StudentSessionSchema` a propósito: lo que el alumno necesita saber al salirse de
         *     un examen a medias no es el estado interno, es si lo contestado se conserva y si eso cuenta.
         */
        StudentAbandonSchema: {
            /**
             * Action
             * @enum {string}
             */
            action: "deleted" | "abandoned";
            /** Detail */
            detail: string;
            /** Session Id */
            session_id: string;
        };
        /**
         * StudentAnswerRequestSchema
         * @description La respuesta a una pregunta, **por su fila en la hoja de respuestas**.
         */
        StudentAnswerRequestSchema: {
            /** Chosen */
            chosen?: string[];
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            /**
             * Elapsed Ms
             * @default 0
             */
            elapsed_ms: number;
            /** Position */
            position: number;
        };
        /**
         * StudentBlockProgressSchema
         * @description Un bloque del programa con sus temas y el agregado del bloque.
         */
        StudentBlockProgressSchema: {
            /** Accuracy */
            accuracy?: number | null;
            /** Answered */
            answered: number;
            /** Available Questions */
            available_questions: number;
            /** Code */
            code: string;
            /** Correct */
            correct: number;
            /**
             * Due Reviews
             * @default 0
             */
            due_reviews: number;
            /** Position */
            position: number;
            /** Title */
            title: string;
            /** Topics */
            topics: components["schemas"]["StudentTopicProgressSchema"][];
        };
        /**
         * StudentCorrectionSchema
         * @description La corrección de una pregunta respondida, cuando se puede enseñar.
         */
        StudentCorrectionSchema: {
            /**
             * Correct
             * @description Letras de la plantilla.
             */
            correct?: string[];
            /** Explanation */
            explanation?: string | null;
            /** Explanation Anchor Id */
            explanation_anchor_id?: string | null;
            /** Explanation Citation */
            explanation_citation?: string | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "correct" | "wrong" | "blank";
            /** Reason */
            reason?: string | null;
        };
        /**
         * StudentEpigraphSchema
         * @description Un epígrafe del tema: solo su código y su título.
         */
        StudentEpigraphSchema: {
            /** Code */
            code: string;
            /** Title */
            title: string;
        };
        /**
         * StudentMistakeSchema
         * @description Una pregunta fallada: qué decía, de qué era, cuándo y cuántas veces.
         */
        StudentMistakeSchema: {
            /** Due */
            due: boolean;
            /**
             * Last Failed At
             * Format: date-time
             */
            last_failed_at: string;
            /** Stem */
            stem: string;
            /** Times Failed */
            times_failed: number;
            /** Topics */
            topics?: components["schemas"]["StudentTopicRefSchema"][];
        };
        /**
         * StudentMistakeTopicSchema
         * @description Los fallos de un tema: es con lo que se pide un test solo de esos fallos.
         */
        StudentMistakeTopicSchema: {
            /** Code */
            code: string;
            /** Due */
            due: number;
            /** Failed */
            failed: number;
            /** Title */
            title: string;
        };
        /**
         * StudentMistakesSchema
         * @description Los fallos: los totales, los que se enseñan y su reparto por tema.
         */
        StudentMistakesSchema: {
            /** Due Total */
            due_total: number;
            /** Questions */
            questions: components["schemas"]["StudentMistakeSchema"][];
            /**
             * Servable Total
             * @default 0
             */
            servable_total: number;
            /** Topics */
            topics: components["schemas"]["StudentMistakeTopicSchema"][];
            /** Total */
            total: number;
        };
        /**
         * StudentMockCaseBlockSchema
         * @description Un bloque del que se puede elegir el supuesto (III o IV).
         */
        StudentMockCaseBlockSchema: {
            /** Code */
            code: string;
            /** Title */
            title: string;
            /** Topics */
            topics: components["schemas"]["StudentMockCaseTopicSchema"][];
        };
        /**
         * StudentMockCaseTopicSchema
         * @description Un tema del bloque del supuesto, con sus preguntas disponibles hoy.
         */
        StudentMockCaseTopicSchema: {
            /** Available Questions */
            available_questions: number;
            /** Code */
            code: string;
            /** Title */
            title: string;
        };
        /**
         * StudentMockExamPartSchema
         * @description Una parte del simulacro, con lo que publica el perfil del examen y nada más.
         */
        StudentMockExamPartSchema: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Ordinary Items */
            ordinary_items?: number | null;
            /** Pass Score */
            pass_score?: number | null;
            /** Penalty */
            penalty?: string | null;
            /** Reserve Items */
            reserve_items?: number | null;
            /** Score Max */
            score_max?: number | null;
            /** Time Minutes */
            time_minutes?: number | null;
        };
        /**
         * StudentMockExamPlanSchema
         * @description El simulacro antes de montarlo: las dos variantes y los bloques del supuesto.
         */
        StudentMockExamPlanSchema: {
            /** Case Blocks */
            case_blocks: components["schemas"]["StudentMockCaseBlockSchema"][];
            full: components["schemas"]["StudentMockExamVariantSchema"];
            opposition: components["schemas"]["StudentOppositionSchema"];
            short: components["schemas"]["StudentMockExamVariantSchema"];
        };
        /**
         * StudentMockExamRequestSchema
         * @description Lo que manda la pantalla para montar un simulacro: variante y bloque del supuesto.
         */
        StudentMockExamRequestSchema: {
            /**
             * Case Block
             * @default III
             * @enum {string}
             */
            case_block: "III" | "IV";
            /**
             * Variant
             * @default full
             * @enum {string}
             */
            variant: "full" | "short";
        };
        /**
         * StudentMockExamVariantSchema
         * @description Una variante del simulacro: qué cae, cuánto dura y qué es lo que **no** es.
         */
        StudentMockExamVariantSchema: {
            /** Note */
            note?: string | null;
            /** Parts */
            parts: components["schemas"]["StudentMockExamPartSchema"][];
            /** Time Limit Minutes */
            time_limit_minutes?: number | null;
            /** Title */
            title: string;
            /**
             * Variant
             * @enum {string}
             */
            variant: "full" | "short";
        };
        /**
         * StudentNoteAnchorSchema
         * @description El apartado de los apuntes que contesta una pregunta, con su tema, su capítulo y su anclaje.
         *
         *     Es lo que permite que «Ver en apuntes» del resultado deje al alumno **en el párrafo** que
         *     explica su fallo (`/temario/IV.7?capitulo=IV.7.2#apartado-udp`) en vez de en la portada del
         *     tema, que no explica nada. El **capítulo** viaja con el anclaje porque los apuntes se leen por
         *     epígrafes oficiales: sin él, la página abriría el primer capítulo de IV.7 y el párrafo no
         *     estaría en ella.
         */
        StudentNoteAnchorSchema: {
            /**
             * Anchor
             * @description El anclaje del apartado dentro de los apuntes del tema.
             */
            anchor: string;
            /**
             * Epigraph Code
             * @description El epígrafe oficial (capítulo) que contiene ese apartado, para abrir la página por él. Vacío si el apartado no dice a qué epígrafe pertenece.
             * @default
             */
            epigraph_code: string;
            /**
             * Topic Code
             * @description El tema al que pertenece el apartado, por su código legible.
             */
            topic_code: string;
        };
        /**
         * StudentNoteChapterSchema
         * @description Un capítulo de los apuntes: un **epígrafe oficial** del tema, con sus apartados.
         *
         *     `code` es el código del epígrafe (`IV.7.2`), que es lo que lleva el parámetro `capitulo` de la
         *     petición y lo que viaja en el enlace «Ver en apuntes». `position` es su lugar en el tema (1..N),
         *     para poder ofrecer «anterior» y «siguiente» sin ordenar nada en la pantalla.
         */
        StudentNoteChapterSchema: {
            /** Code */
            code: string;
            /** Position */
            position: number;
            /** Sections */
            sections: components["schemas"]["StudentNoteChapterSectionSchema"][];
            /** Title */
            title: string;
        };
        /**
         * StudentNoteChapterSectionSchema
         * @description Un apartado **del índice**: sin su texto, para que viaje el índice entero.
         *
         *     Es la mitad barata del contrato: con esto la pantalla puede enseñar todos los apartados de todos
         *     los capítulos y resolver a qué capítulo pertenece un anclaje, sin que un tema de 314.000 px
         *     viaje de una vez.
         */
        StudentNoteChapterSectionSchema: {
            /** Anchor */
            anchor: string;
            /** Key */
            key: string;
            /** Number */
            number: number;
            /** Questions Covered */
            questions_covered: number;
            /** Title */
            title: string;
        };
        /**
         * StudentNoteSectionSchema
         * @description Un apartado de los apuntes, con su sitio en el índice y su dirección en la página.
         *
         *     `anchor` es lo que convierte el índice en navegable: el enlace del índice lleva al párrafo y el
         *     aviso del alumno apunta a él. `questions_covered` es el dato que acompaña al párrafo («N
         *     preguntas de este tema se contestan aquí»), y es un recuento real de las comprobaciones del
         *     tema, no una afirmación sobre exámenes.
         */
        StudentNoteSectionSchema: {
            /** Anchor */
            anchor: string;
            /** Body Markdown */
            body_markdown: string;
            /** Epigraph Code */
            epigraph_code: string;
            /** Key */
            key: string;
            /** Number */
            number: number;
            /** Questions Covered */
            questions_covered: number;
            /** Title */
            title: string;
        };
        /**
         * StudentNotesSchema
         * @description Los apuntes de un tema: cómo están, **un capítulo** para leer y el índice completo.
         *
         *     Un tema en `draft` se sirve **igual** que uno en `published`: la marca distingue uno de otro y
         *     el alumno puede leer los dos. Un tema en `none` no trae apartados, y eso no es un error.
         *
         *     `sections` trae el texto del capítulo servido y `chapters` el índice de todos los capítulos, con
         *     sus apartados pero sin sus textos. `chapter` dice cuál de ellos viaja en `sections`, y puede no
         *     ser el pedido: un `capitulo` que ya no existe sirve el primero, y la pantalla lo dice
         *     corrigiendo la dirección en vez de dejar al alumno en un error.
         */
        StudentNotesSchema: {
            /** Chapter */
            chapter?: string | null;
            /** Chapters */
            chapters: components["schemas"]["StudentNoteChapterSchema"][];
            /** Code */
            code: string;
            /** Generated At */
            generated_at?: string | null;
            /** Sections */
            sections: components["schemas"]["StudentNoteSectionSchema"][];
            /**
             * State
             * @enum {string}
             */
            state: "published" | "draft" | "none";
        };
        /**
         * StudentOfficialExamSchema
         * @description Un examen oficial, por su sitio en la lista: título, fecha, tamaño y si se puede hacer.
         */
        StudentOfficialExamSchema: {
            /** Blocked Reason */
            blocked_reason?: ("faltan_respuestas" | "faltan_preguntas") | null;
            /** Held At */
            held_at?: string | null;
            /** Held Year */
            held_year?: number | null;
            /**
             * Origin Scope
             * @default desconocida
             * @enum {string}
             */
            origin_scope: "age" | "otra_administracion" | "desconocida";
            /** Position */
            position: number;
            /** Questions */
            questions: number;
            /** Ready */
            ready: boolean;
            /** Title */
            title: string;
        };
        /**
         * StudentOfficialExamsSchema
         * @description Los exámenes oficiales importados. Una lista vacía es un estado, no un error.
         */
        StudentOfficialExamsSchema: {
            /** Exams */
            exams: components["schemas"]["StudentOfficialExamSchema"][];
        };
        /**
         * StudentOppositionSchema
         * @description La oposición que sirve la zona del alumno.
         */
        StudentOppositionSchema: {
            /** Code */
            code: string;
            /** Name */
            name: string;
        };
        /**
         * StudentOptionSchema
         * @description Una opción: su letra (`a`) y su texto.
         */
        StudentOptionSchema: {
            /** Key */
            key: string;
            /** Text */
            text: string;
        };
        /**
         * StudentOverviewSchema
         * @description Inicio: el test a medias, los fallos vencidos, el progreso por bloque y lo último hecho.
         */
        StudentOverviewSchema: {
            /** Blocks */
            blocks: components["schemas"]["StudentBlockProgressSchema"][];
            /** Due Reviews */
            due_reviews: number;
            in_progress?: components["schemas"]["StudentSessionSchema"] | null;
            opposition: components["schemas"]["StudentOppositionSchema"];
            /** Recent Tests */
            recent_tests: components["schemas"]["StudentSessionSchema"][];
        };
        /**
         * StudentPartScoreSchema
         * @description La nota de una parte, con la forma con la que se calculó.
         *
         *     `kind` dice cómo se corrigió (`estimated` cuando la puntuación es la directa escalada a la banda
         *     de la parte) y `verdict_note` lo explica en palabras: una estimación no es la calificación
         *     oficial, y `passed` se queda en `None` para no declarar un aprobado que nadie ha calculado.
         */
        StudentPartScoreSchema: {
            /** Blank */
            blank: number;
            /** Correct */
            correct: number;
            /** Kind */
            kind: string;
            /** Part Code */
            part_code?: string | null;
            /** Part Name */
            part_name?: string | null;
            /** Pass Score */
            pass_score?: number | null;
            /** Passed */
            passed?: boolean | null;
            /** Score */
            score: string;
            /** Score Decimal */
            score_decimal: string;
            /** Score Max */
            score_max?: number | null;
            /** Verdict Note */
            verdict_note?: string | null;
            /** Wrong */
            wrong: number;
        };
        /**
         * StudentProgressSchema
         * @description El progreso: acierto por bloque y por tema, los cinco más flojos e historial.
         *
         *     `tests_finished` es el número de tests **terminados** de esta persona, no los que caben en el
         *     historial: la cifra se lee al lado de una lista de veinte y tiene que ser la de verdad.
         */
        StudentProgressSchema: {
            /** Blocks */
            blocks: components["schemas"]["StudentBlockProgressSchema"][];
            /** History */
            history: components["schemas"]["StudentSessionSchema"][];
            opposition: components["schemas"]["StudentOppositionSchema"];
            /** Tests Finished */
            tests_finished: number;
            /** Weakest Topics */
            weakest_topics: components["schemas"]["StudentTopicProgressSchema"][];
        };
        /**
         * StudentQuestionSchema
         * @description La pregunta que se está contestando, por su posición en la hoja.
         */
        StudentQuestionSchema: {
            /** Answered */
            answered: boolean;
            /** Chosen */
            chosen?: string[];
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            correction?: components["schemas"]["StudentCorrectionSchema"] | null;
            /**
             * Derived Key
             * @description La clave de esta pregunta es derivada: los apuntes (con su cita verificada) y el modelo preguntado sin apuntes dicen la misma letra. Se enseña como «clave revisada automáticamente».
             * @default false
             */
            derived_key: boolean;
            /**
             * In Review
             * @description La clave de esta pregunta está en revisión: su conjunto discrepa de los apuntes entre el 15 % y el 30 % de las preguntas medidas.
             * @default false
             */
            in_review: boolean;
            /** Is Reserve */
            is_reserve: boolean;
            /** Options */
            options: components["schemas"]["StudentOptionSchema"][];
            /** Position */
            position: number;
            /** Question Type */
            question_type: string;
            /** Stem */
            stem: string;
        };
        /**
         * StudentReportRequestSchema
         * @description Lo que manda la pantalla cuando el alumno marca «esto está mal» en un apartado.
         *
         *     El motivo es **una línea** y es obligatorio: se recorta, no puede quedar vacío y tiene su tope
         *     (`MAX_REASON_CHARS`). El apartado se manda por su clave, no por su anclaje: el anclaje lo pone
         *     el servidor a partir del apartado que existe hoy.
         */
        StudentReportRequestSchema: {
            /** Reason */
            reason: string;
            /** Section Key */
            section_key: string;
        };
        /**
         * StudentReportSchema
         * @description El aviso ya guardado: dónde, qué se escribió y cuándo.
         */
        StudentReportSchema: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Reason
             * @description El motivo, en una línea (máximo 300 caracteres).
             */
            reason: string;
            /** Section Key */
            section_key: string;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "reviewed" | "dismissed";
        };
        /**
         * StudentResultQuestionSchema
         * @description Una pregunta corregida: sus opciones, lo que se marcó, la correcta y de qué era.
         */
        StudentResultQuestionSchema: {
            /** Chosen */
            chosen?: string[];
            /** Correct */
            correct?: string[];
            /**
             * Derived Key
             * @description La clave de esta pregunta es derivada (los apuntes, con su cita verificada, y el modelo sin apuntes dicen la misma letra): se enseña como «clave revisada automáticamente».
             * @default false
             */
            derived_key: boolean;
            /** Elapsed Ms */
            elapsed_ms?: number | null;
            /** Explanation */
            explanation?: string | null;
            /** Explanation Anchor Id */
            explanation_anchor_id?: string | null;
            /** Explanation Citation */
            explanation_citation?: string | null;
            /**
             * In Review
             * @description La clave de esta pregunta está en revisión: un fallo puede ser de la clave y no del alumno.
             * @default false
             */
            in_review: boolean;
            /** Is Reserve */
            is_reserve: boolean;
            /** @description El apartado de los apuntes que contesta esta pregunta. Con él, una fallada ofrece «Ver en apuntes» al párrafo exacto; sin él no se ofrece la salida, en vez de mandar al alumno a la portada del tema. */
            note_anchor?: components["schemas"]["StudentNoteAnchorSchema"] | null;
            /** Options */
            options: components["schemas"]["StudentOptionSchema"][];
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "correct" | "wrong" | "blank" | "void";
            /** Part Code */
            part_code?: string | null;
            /** Part Name */
            part_name?: string | null;
            /** Position */
            position: number;
            /** Stem */
            stem: string;
            /** Topics */
            topics?: components["schemas"]["StudentTopicRefSchema"][];
        };
        /**
         * StudentResultSchema
         * @description El resultado de un test: la sesión terminada, la nota por parte y el total.
         */
        StudentResultSchema: {
            /** Official Available */
            official_available: boolean;
            /** Official Note */
            official_note?: string | null;
            /** Parts */
            parts: components["schemas"]["StudentPartScoreSchema"][];
            session: components["schemas"]["StudentSessionSchema"];
            total: components["schemas"]["StudentPartScoreSchema"];
        };
        /**
         * StudentResultTopicSchema
         * @description Cómo fue el test en un tema: aciertos, fallos, blancos y el porcentaje que sale de ellos.
         */
        StudentResultTopicSchema: {
            /** Accuracy */
            accuracy?: number | null;
            /** Blank */
            blank: number;
            /** Code */
            code: string;
            /** Correct */
            correct: number;
            /** Graded */
            graded: number;
            /** Title */
            title: string;
            /** Wrong */
            wrong: number;
        };
        /**
         * StudentRunSchema
         * @description El test en curso: la sesión, la pregunta que toca y la hoja de respuestas entera.
         */
        StudentRunSchema: {
            /** Answered */
            answered: number;
            /** Finished */
            finished: boolean;
            /** Pending */
            pending: number;
            /** Position */
            position?: number | null;
            question?: components["schemas"]["StudentQuestionSchema"] | null;
            /**
             * Questions Derived
             * @description Cuántas preguntas del test llevan la marca «clave revisada automáticamente»: su clave es derivada y no sale de la plantilla del conjunto.
             * @default 0
             */
            questions_derived: number;
            /**
             * Questions In Review
             * @description Cuántas preguntas del test llevan la marca «clave en revisión».
             * @default 0
             */
            questions_in_review: number;
            session: components["schemas"]["StudentSessionSchema"];
            /** Sheet */
            sheet: components["schemas"]["StudentSheetRowSchema"][];
            /** Total */
            total: number;
        };
        /**
         * StudentScoreSchema
         * @description Cómo fue un test: aciertos, fallos, blancos y la puntuación directa con su penalización.
         *
         *     La puntuación viaja como fracción exacta en texto (`128/3`) **y** como decimal redondeado: el
         *     decimal es para leerlo, el exacto es el que vale (DEBT-006). `passed` es `None` cuando la
         *     convocatoria no publica el umbral, en lugar de inventar un aprobado.
         */
        StudentScoreSchema: {
            /** Blank */
            blank: number;
            /** Correct */
            correct: number;
            /** Maximum */
            maximum?: number | null;
            /** Passed */
            passed?: boolean | null;
            /** Points */
            points: string;
            /** Points Decimal */
            points_decimal: string;
            /** Wrong */
            wrong: number;
        };
        /**
         * StudentSessionResultSchema
         * @description El resultado de un test terminado, con el tiempo empleado y las preguntas una a una.
         */
        StudentSessionResultSchema: {
            /** Duration Seconds */
            duration_seconds?: number | null;
            /** Official Available */
            official_available: boolean;
            /** Official Note */
            official_note?: string | null;
            /** Parts */
            parts: components["schemas"]["StudentPartScoreSchema"][];
            /** Questions */
            questions: components["schemas"]["StudentResultQuestionSchema"][];
            session: components["schemas"]["StudentSessionSchema"];
            /** Topics */
            topics: components["schemas"]["StudentResultTopicSchema"][];
            total: components["schemas"]["StudentPartScoreSchema"];
        };
        /**
         * StudentSessionSchema
         * @description Un test del alumno: lo que se pinta en «Continuar», en el historial y al terminar.
         *
         *     `title` lo compone la capa del alumno a partir de lo que se eligió; **nunca** es el título del
         *     conjunto de origen.
         */
        StudentSessionSchema: {
            /** Answered Questions */
            answered_questions: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Finished At */
            finished_at?: string | null;
            /** Id */
            id: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "practice" | "error_review" | "official_exam" | "mock_exam" | "diagnostic";
            /** Practical Case Origin */
            practical_case_origin?: string | null;
            /** Practical Case Statement */
            practical_case_statement?: string | null;
            result?: components["schemas"]["StudentScoreSchema"] | null;
            /**
             * Server Now
             * Format: date-time
             */
            server_now: string;
            /** Started At */
            started_at?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "running" | "finished" | "abandoned";
            /** Time Limit Minutes */
            time_limit_minutes?: number | null;
            /** Title */
            title: string;
            /** Total Questions */
            total_questions: number;
        };
        /**
         * StudentSheetRowSchema
         * @description Una fila de la hoja de respuestas: qué se marcó en esa posición y cómo quedó.
         */
        StudentSheetRowSchema: {
            /** Answered */
            answered: boolean;
            /** Chosen */
            chosen?: string[];
            /** Confidence */
            confidence?: ("low" | "medium" | "high") | null;
            /** Correct */
            correct?: string[];
            /** Outcome */
            outcome?: ("correct" | "wrong" | "blank") | null;
            /** Position */
            position: number;
        };
        /**
         * StudentSyllabusSchema
         * @description El temario: bloques y temas **en orden numérico** (IV.1 antes de IV.10).
         */
        StudentSyllabusSchema: {
            /** Blocks */
            blocks: components["schemas"]["StudentBlockProgressSchema"][];
            opposition: components["schemas"]["StudentOppositionSchema"];
        };
        /**
         * StudentTestCountSchema
         * @description Un tamaño de test ofrecido, con lo que duraría con el reloj puesto.
         */
        StudentTestCountSchema: {
            /** Minutes */
            minutes: number;
            /** Questions */
            questions: number;
        };
        /**
         * StudentTestPlanSchema
         * @description Lo que la pantalla de Tests puede ofrecer antes de montar un test (F22).
         *
         *     Ni un tamaño ni un minuto se calculan en la pantalla: los sirve el servidor, que es el mismo que
         *     después pone el reloj. `timed_note` es la frase que acompaña al interruptor del reloj, y también
         *     viene de aquí por la misma razón que la nota del simulacro: la regla se escribe una vez.
         *     `convocation_minutes` es el tiempo del test cuando **no** se le pone el reloj del test; `null`
         *     significa que la convocatoria no lo publica, no que no haya ninguno.
         */
        StudentTestPlanSchema: {
            /** Convocation Minutes */
            convocation_minutes?: number | null;
            /** Counts */
            counts: components["schemas"]["StudentTestCountSchema"][];
            /** Timed Note */
            timed_note: string;
        };
        /**
         * StudentTestRequestSchema
         * @description Lo que manda la pantalla para montar un test: sus temas, cuántas y con qué filtro.
         */
        StudentTestRequestSchema: {
            /** Count */
            count: number;
            /**
             * Feedback
             * @default immediate
             * @enum {string}
             */
            feedback: "immediate" | "at_end";
            /**
             * Filter
             * @default all
             * @enum {string}
             */
            filter: "all" | "unseen" | "failed" | "flagged";
            /**
             * Nodes
             * @description Códigos de tema, como `IV.10`.
             */
            nodes: string[];
            /**
             * Timed
             * @default false
             */
            timed: boolean;
        };
        /**
         * StudentTopicProgressSchema
         * @description Un tema con lo que tiene y lo que se ha hecho en él.
         *
         *     `accuracy` es `None` cuando no hay nada corregido todavía: un tema sin tocar no está
         *     suspendido. `notes_state` es lo que permite pintar en el temario si sus apuntes están
         *     publicados, en borrador o sin escribir.
         */
        StudentTopicProgressSchema: {
            /** Accuracy */
            accuracy?: number | null;
            /** Answered */
            answered: number;
            /** Available Questions */
            available_questions: number;
            /** Code */
            code: string;
            /** Correct */
            correct: number;
            /**
             * Due Reviews
             * @default 0
             */
            due_reviews: number;
            /**
             * Notes State
             * @default none
             * @enum {string}
             */
            notes_state: "published" | "draft" | "none";
            /** Number */
            number?: number | null;
            /** Title */
            title: string;
        };
        /**
         * StudentTopicRefSchema
         * @description Un tema por su código legible: la respuesta a «¿de qué era esto?».
         */
        StudentTopicRefSchema: {
            /** Code */
            code: string;
            /** Title */
            title: string;
        };
        /**
         * StudentTopicSchema
         * @description Un tema por su código legible, con sus epígrafes y su progreso.
         */
        StudentTopicSchema: {
            /** Block Code */
            block_code: string;
            /** Block Title */
            block_title: string;
            /** Code */
            code: string;
            /** Description */
            description?: string | null;
            /** Epigraphs */
            epigraphs: components["schemas"]["StudentEpigraphSchema"][];
            /** Number */
            number?: number | null;
            progress?: components["schemas"]["StudentTopicProgressSchema"] | null;
            /** Title */
            title: string;
        };
        /**
         * StudyReadinessSchema
         * @description Si esta oposición se puede estudiar ya, paso a paso, y qué falta si falta algo.
         */
        StudyReadinessSchema: {
            /** Convocation Code */
            convocation_code: string | null;
            /**
             * Missing
             * @description Una frase por paso que no está listo, tal y como se enseña.
             */
            missing: string[];
            /** Opposition Id */
            opposition_id: string;
            /** Opposition Name */
            opposition_name: string;
            /** Ready */
            ready: boolean;
            /** Steps */
            steps: components["schemas"]["StudyReadinessStepSchema"][];
        };
        /**
         * StudyReadinessStepSchema
         * @description Un paso hacia poder estudiar: qué es, cómo está y por dónde se resuelve.
         */
        StudyReadinessStepSchema: {
            /** Action Href */
            action_href: string;
            /** Action Label */
            action_label: string;
            /** Count */
            count: number;
            /** Detail */
            detail: string;
            /** Key */
            key: string;
            /**
             * Status
             * @enum {string}
             */
            status: "ready" | "incomplete" | "empty";
            /** Title */
            title: string;
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
         * TareaSchema
         * @description Una tarea con su boton: el tipo dice a que pantalla lleva.
         */
        TareaSchema: {
            /** Codigo */
            codigo?: string | null;
            /** Minutos */
            minutos: number;
            /** Tipo */
            tipo: string;
            /** Titulo */
            titulo: string;
        };
        /** TemaFlojoSchema */
        TemaFlojoSchema: {
            /** Acierto */
            acierto: number;
            /** Codigo */
            codigo: string;
            /** Frase */
            frase: string;
            /** Intentos */
            intentos: number;
            /** Titulo */
            titulo: string;
        };
        /**
         * TrayBulkRequestSchema
         * @description Una acción en bloque sobre un conjunto: qué se hace, dónde y quién lo hace.
         *
         *     La nota es potestativa —una acción en bloque tiene su propio texto por defecto— y, cuando viene,
         *     es **una línea**, como la del despacho de una en una: es la misma regla y se normaliza igual.
         */
        TrayBulkRequestSchema: {
            /**
             * Action
             * @enum {string}
             */
            action: "aceptar_derivadas" | "dejar_fuera" | "no_son_preguntas";
            /** Actor */
            actor?: string | null;
            /** Note */
            note?: string | null;
            /** Set Id */
            set_id: string;
        };
        /**
         * TrayBulkResultSchema
         * @description Qué hizo la acción en bloque: cuántas incidencias cerró y cuántas claves escribió.
         *
         *     Los dos números van separados porque no tienen por qué coincidir: aceptar las derivadas escribe
         *     una clave por propuesta —salvo las que ya estuvieran escritas— y cerrar un conjunto entero no
         *     escribe ninguna.
         */
        TrayBulkResultSchema: {
            /**
             * Action
             * @enum {string}
             */
            action: "aceptar_derivadas" | "dejar_fuera" | "no_son_preguntas";
            /** Incidents */
            incidents: number;
            /** Keys Written */
            keys_written: number;
            /** Set Id */
            set_id: string;
        };
        /**
         * TraySchema
         * @description Una **hoja** de la bandeja, en dos secciones, con **la cifra** de la medida de éxito (§2.4).
         *
         *     `entradas_de_decision` no es el número de incidencias ni el de filas: es lo que de verdad
         *     depende del criterio del propietario, contado con la regla de `domain.tray` —una por conjunto no
         *     oficial, una por incidencia oficial—. Va en la respuesta y no se calcula en la pantalla porque
         *     es la cifra que decide si la bandeja sirve, y una cifra que se calcula en dos sitios acaba
         *     diciendo dos cosas.
         *
         *     `rest` son las filas de **la hoja**; `filas`, `total_pendiente`, `propuestas` y
         *     `entradas_de_decision` son de la bandeja **entera** y no cambian al pasar de hoja: paginar no
         *     puede mover la cifra del trabajo que queda. La sección de oficiales va entera en todas las
         *     hojas: son ocho como mucho y sus incidencias no se deciden en bloque.
         */
        TraySchema: {
            /**
             * Entradas De Decision
             * @description La medida de éxito: lo que de verdad depende del propietario.
             */
            entradas_de_decision: number;
            /**
             * Filas
             * @description Cuántas filas tiene la bandeja entera.
             */
            filas: number;
            /** Official Section */
            official_section?: components["schemas"]["TraySetSchema"][];
            /**
             * Page
             * @description La hoja que va en `rest`, empezando por 1.
             * @default 1
             */
            page: number;
            /**
             * Page Size
             * @description Cuántas filas caben en una hoja.
             * @default 50
             */
            page_size: number;
            /**
             * Pages
             * @description Cuántas hojas tiene la lista de bancos.
             * @default 1
             */
            pages: number;
            /**
             * Propuestas
             * @description Incidencias ya propuestas, que se aprueban en bloque.
             */
            propuestas: number;
            /**
             * Rest
             * @description Las filas de la hoja que se está mirando.
             */
            rest?: components["schemas"]["TraySetSchema"][];
            /**
             * Rest Total
             * @description Filas de la sección de bancos, sumando todas las hojas.
             * @default 0
             */
            rest_total: number;
            /**
             * Total Pendiente
             * @description Incidencias que esperan criterio.
             */
            total_pendiente: number;
        };
        /**
         * TraySetSchema
         * @description Una **fila** de la bandeja: un conjunto y lo que espera dentro.
         *
         *     Es la pieza que hace trabajable una bandeja de cientos de filas. `pendientes` cuenta por
         *     categoría lo que espera criterio; `propuestas` lo que ya está resuelto por regla y solo falta
         *     aprobar en bloque. `resumen` es el título de la fila —«50 claves sospechosas»—, calculado por el
         *     dominio para que la pantalla no tenga que componerlo y no haya dos versiones del mismo texto.
         *
         *     `acciones` viaja **calculado**: los conjuntos oficiales llegan con la lista vacía, porque su
         *     clave no se toca y sus incidencias las decide el propietario una a una. La pantalla no tiene que
         *     saberse la regla; la lee.
         */
        TraySetSchema: {
            /** Acciones */
            acciones?: ("aceptar_derivadas" | "dejar_fuera" | "no_son_preguntas")[];
            /** Entradas De Decision */
            entradas_de_decision: number;
            /** Key Reliability */
            key_reliability: string;
            /** Official */
            official: boolean;
            /** Origin Scope */
            origin_scope: string;
            /** Pendientes */
            pendientes?: {
                [key: string]: number;
            };
            /** Propuestas */
            propuestas: number;
            /** Resumen */
            resumen: string;
            /**
             * Section
             * @enum {string}
             */
            section: "oficial" | "resto";
            /** Set Id */
            set_id: string;
            /** Title */
            title: string;
            /** Total Pendiente */
            total_pendiente: number;
        };
        /**
         * UrlRequest
         * @description URL que se descargará con la guarda de red (09_SECURITY §4).
         */
        UrlRequest: {
            /** Url */
            url: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
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
        /**
         * WithdrawDocumentResultSchema
         * @description Lo que pasó al retirar un documento entero: las versiones retiradas y las que no.
         */
        WithdrawDocumentResultSchema: {
            /** Document Id */
            document_id: string;
            /** Failed */
            failed?: components["schemas"]["PromotionOutcomeSchema"][];
            /** Withdrawn Version Ids */
            withdrawn_version_ids: string[];
        };
        /**
         * WithdrawRequestSchema
         * @description Retirar exige decir por qué: queda en la auditoría junto a quién y cuándo.
         */
        WithdrawRequestSchema: {
            /** Reason */
            reason: string;
        };
        /** SemanaSchema */
        opofuente__api__routes__plan__SemanaSchema: {
            /**
             * Empieza
             * Format: date
             */
            empieza: string;
            /** Numero */
            numero: number;
            /** Tareas */
            tareas: components["schemas"]["TareaSchema"][];
        };
        /** SemanaSchema */
        opofuente__api__routes__stats__SemanaSchema: {
            /** Acierto */
            acierto: number;
            /** Empieza */
            empieza: string;
            /** Intentos */
            intentos: number;
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
    configuration_api_v1_accounts_configuration_get: {
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
                    "application/json": components["schemas"]["AccountsAvailableSchema"];
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
    events_api_v1_accounts_events_get: {
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
                    "application/json": components["schemas"]["AccountEventSchema"][];
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
    login_api_v1_accounts_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmailPasswordSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccountMeSchema"];
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
    logout_api_v1_accounts_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
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
    me_api_v1_accounts_me_get: {
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
                    "application/json": components["schemas"]["AccountMeSchema"];
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
    close_account_api_v1_accounts_me_delete: {
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
                    "application/json": components["schemas"]["AccountClosedSchema"];
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
    request_reset_api_v1_accounts_password_resets_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PasswordResetRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccountAcceptedSchema"];
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
    confirm_reset_api_v1_accounts_password_resets_confirm_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PasswordResetConfirmSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccountSchema"];
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
    register_api_v1_accounts_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmailPasswordSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccountAcceptedSchema"];
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
    sessions_api_v1_accounts_sessions_get: {
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
                    "application/json": components["schemas"]["AccountSessionsSchema"];
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
    revoke_session_api_v1_accounts_sessions__session_id__delete: {
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
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
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
    record_event_api_v1_analytics_events_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AnalyticsEventSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AnalyticsRecordedSchema"];
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
    analytics_summary_api_v1_analytics_summary_get: {
        parameters: {
            query?: {
                days?: number;
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
                    "application/json": components["schemas"]["AnalyticsSummarySchema"];
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
    pending_cards_api_v1_cards_pending_get: {
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
                    "application/json": components["schemas"]["PendingSchema"];
                };
            };
        };
    };
    card_queue_api_v1_cards_queue_get: {
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
                    "application/json": components["schemas"]["CardQueueSchema"];
                };
            };
        };
    };
    answer_due_failure_api_v1_cards_queue_failures__question_version_id__post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                question_version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DueFailureAnswerSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DueFailureCorrectionSchema"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    answer_card_api_v1_cards__card_id__answer_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                card_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AnswerCardSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CardSchema"];
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
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobSchema"];
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
    remove_collection_item_api_v1_collections__collection_id__items_delete: {
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
    activate_convocation_api_v1_convocations__convocation_id__activate_post: {
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
                    "application/json": components["schemas"]["ConvocationReferenceSchema"];
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
    node_dossier_api_v1_curriculum_nodes__node_id__dossier_get: {
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
                    "application/json": components["schemas"]["DossierSchema"];
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
    list_dossier_versions_api_v1_curriculum_nodes__node_id__dossier_versions_get: {
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
                    "application/json": components["schemas"]["DossierVersionSchema"][];
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
    archive_dossier_api_v1_curriculum_nodes__node_id__dossier_versions_post: {
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
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DossierArchiveSchema"];
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
    get_dossier_version_api_v1_curriculum_nodes__node_id__dossier_versions__version_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                node_id: string;
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
                    "application/json": components["schemas"]["DossierSchema"];
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
    diagnostics_api_v1_diagnostics_get: {
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
                    "application/json": components["schemas"]["DiagnosticSchema"];
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
    diagnostics_text_api_v1_diagnostics_text_get: {
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
                    "text/plain": string;
                };
            };
            /** @description Error interno inesperado (RFC 9457). */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/plain": components["schemas"]["ProblemDetail"];
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
                collection_id?: string | null;
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
    reinstate_version_api_v1_documents__document_id__versions__version_id__reinstate_post: {
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
    withdraw_version_api_v1_documents__document_id__versions__version_id__withdraw_post: {
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
                "application/json": components["schemas"]["WithdrawRequestSchema"];
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
    withdraw_document_api_v1_documents__document_id__withdraw_post: {
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
                "application/json": components["schemas"]["WithdrawRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WithdrawDocumentResultSchema"];
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
    list_pending_explanations_api_v1_explanations_pending_get: {
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
                    "application/json": components["schemas"]["ExplanationTrayItemSchema"][];
                };
            };
        };
    };
    regenerate_explanation_api_v1_explanations__explanation_id__regenerate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                explanation_id: string;
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
                    "application/json": components["schemas"]["ExplanationTrayItemSchema"];
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
    set_explanation_status_api_v1_explanations__explanation_id__status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                explanation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SetExplanationStatusRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
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
    housekeeping_report_api_v1_housekeeping_get: {
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
                    "application/json": components["schemas"]["HousekeepingReportSchema"];
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
    purge_old_jobs_api_v1_housekeeping_old_jobs_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PurgeRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PurgeResultSchema"];
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
    purge_orphan_artifacts_api_v1_housekeeping_orphan_artifacts_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PurgeRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PurgeResultSchema"];
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
    purge_temps_api_v1_housekeeping_temps_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PurgeRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PurgeResultSchema"];
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
    pause_batch_api_v1_ingestion_batches__batch_id__pause_post: {
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
    resume_batch_api_v1_ingestion_batches__batch_id__resume_post: {
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
    accept_invitation_api_v1_invitations_accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CanjeSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CanjeResultadoSchema"];
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
    read_consent_api_v1_legal_consent_get: {
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
                    "application/json": components["schemas"]["ConsentStateSchema"] | null;
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
    decide_consent_api_v1_legal_consent_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConsentDecisionSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConsentStateSchema"];
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
    consent_summary_api_v1_legal_consent_summary_get: {
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
                    "application/json": components["schemas"]["ConsentSummarySchema"];
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
    cookies_api_v1_legal_cookies_get: {
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
                    "application/json": components["schemas"]["CookiesSchema"];
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
    data_inventory_api_v1_legal_data_inventory_get: {
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
                    "application/json": components["schemas"]["DataInventorySchema"];
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
    documents_api_v1_legal_documents_get: {
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
                    "application/json": components["schemas"]["LegalBundleSchema"];
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
    one_document_api_v1_legal_documents__key__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                key: string;
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
                    "application/json": components["schemas"]["LegalDocumentSchema"];
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
    list_notes_incidents_api_v1_notes_incidents_get: {
        parameters: {
            query?: {
                /** @description Filtra por categoría; sin ella salen todas. */
                category?: ("hueco_sin_material" | "clave_sospechosa" | "pregunta_ambigua" | "norma_cambiada" | "pregunta_mal_importada" | "clave_no_fiable") | null;
                /** @description Filtra por estado; sin él salen todas. */
                status?: ("open" | "in_progress" | "reviewed" | "dismissed" | "propuesta_lista" | "no_son_preguntas") | null;
                /** @description Código legible del tema, como `I.2`, para ver solo las de un tema. */
                topic?: string | null;
                /** @description Conjunto de origen: es lo que despliega una fila de la bandeja agrupada. */
                set_id?: string | null;
                /** @description Busca en el enunciado de la pregunta, el motivo, la frase y el apartado. */
                q?: string | null;
                /** @description Cuántas incidencias se devuelven como mucho. */
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
                    "application/json": components["schemas"]["NotesIncidentListSchema"];
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
    read_tray_api_v1_notes_incidents_tray_get: {
        parameters: {
            query?: {
                /** @description Qué hoja de la lista de bancos se sirve, empezando por la 1. Cincuenta filas por hoja: con los datos del propietario son 157 filas con cuatro acciones cada una. */
                pagina?: number;
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
                    "application/json": components["schemas"]["TraySchema"];
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
    read_tray_actions_api_v1_notes_incidents_tray_actions_get: {
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
                    "application/json": {
                        [key: string]: string;
                    };
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
    dispatch_tray_bulk_api_v1_notes_incidents_tray_bulk_post: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TrayBulkRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TrayBulkResultSchema"];
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
    update_notes_incident_api_v1_notes_incidents__incident_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                /** @description Identificador de la incidencia, tal como lo devuelve la bandeja. */
                incident_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NotesIncidentUpdateSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotesIncidentSchema"];
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
    list_note_reports_api_v1_notes_reports_get: {
        parameters: {
            query?: {
                /** @description Filtra por estado; sin él salen todos. */
                status?: ("open" | "in_progress" | "reviewed" | "dismissed") | null;
                /** @description Código legible del tema, como `IV.7`, para ver solo los de un tema. */
                topic?: string | null;
                /** @description Busca en el motivo del alumno y en el título del apartado. */
                q?: string | null;
                /** @description Cuántos avisos se devuelven como mucho. */
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
                    "application/json": components["schemas"]["NoteReportListSchema"];
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
    update_note_report_api_v1_notes_reports__report_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                /** @description Identificador del aviso, tal como lo devuelve la bandeja. */
                report_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NoteReportUpdateSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoteReportSchema"];
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
    list_notes_review_api_v1_notes_review_get: {
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
                    "application/json": components["schemas"]["NotesReviewListSchema"];
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
    notes_review_summary_api_v1_notes_review_summary_get: {
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
                    "application/json": components["schemas"]["NotesReviewCountersSchema"];
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
    notes_review_file_api_v1_notes_review__codigo__get: {
        parameters: {
            query?: {
                /** @description Qué hoja de apartados se sirve, empezando por la 1. Una hoja son seis apartados: los cuerpos de todos a la vez eran el 92 % de la respuesta y el navegador tardaba en pintar el primero. */
                pagina?: number;
                /** @description `lectura` es el orden del tema; `peores`, lo que queda sin resolver antes. */
                orden?: "lectura" | "peores";
            };
            header?: never;
            path: {
                /** @description Código legible del tema, como `I.4` (también se acepta `I-4`). */
                codigo: string;
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
                    "application/json": components["schemas"]["NotesReviewFileSchema"];
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
    decide_notes_review_api_v1_notes_review__codigo__decision_post: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                /** @description Código legible del tema, como `I.4`. */
                codigo: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NotesReviewDecisionRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotesReviewDecisionResultSchema"];
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
    get_readiness_api_v1_oppositions__opposition_id__readiness_get: {
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
                    "application/json": components["schemas"]["StudyReadinessSchema"];
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
    payment_plans_api_v1_payments_plans_get: {
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
                    "application/json": components["schemas"]["PaymentsSchema"];
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
    get_pending_actions_api_v1_pending_actions_get: {
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
                    "application/json": components["schemas"]["PendingActionsSchema"];
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
    leer_guardado_api_v1_plan_get: {
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
                    "application/json": components["schemas"]["PlanGuardadoSchema"];
                };
            };
        };
    };
    guardar_plan_api_v1_plan_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuardarPlanSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlanSchema"];
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
    plan_de_hoy_api_v1_plan_hoy_get: {
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
                    "application/json": components["schemas"]["HoySchema"];
                };
            };
        };
    };
    progreso_api_v1_plan_progreso_get: {
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
                    "application/json": components["schemas"]["ProgresoSchema"];
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
    platform_policy_api_v1_platform_policy_get: {
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
                    "application/json": components["schemas"]["PlatformPolicySchema"];
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
    list_question_exclusions_api_v1_question_exclusions_get: {
        parameters: {
            query?: {
                reason?: string | null;
                /** @description Busca en el enunciado de la pregunta excluida. */
                q?: string | null;
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
                    "application/json": components["schemas"]["QuestionExclusionPageSchema"];
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
    get_question_file_api_v1_question_files__question_version_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Identificador de la versión de la pregunta, el que usa la bandeja del motor. */
                question_version_id: string;
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
                    "application/json": components["schemas"]["QuestionFileSchema"];
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
    mark_correct_option_api_v1_question_files__question_version_id__answer_key_post: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                /** @description Identificador de la versión de la pregunta. */
                question_version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkCorrectOptionSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MarkCorrectResultSchema"];
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
            /** @description El cambio no encaja con lo que hay (`classification_conflict`), y se dice por qué. Por ejemplo, asignar una pregunta a un nodo del programa que no es un tema. */
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
    repair_question_api_v1_question_files__question_version_id__repairs_post: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                /** @description Identificador de la versión de la pregunta. */
                question_version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RepairQuestionSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepairResultSchema"];
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
            /** @description El cambio no encaja con lo que hay (`classification_conflict`), y se dice por qué. Por ejemplo, asignar una pregunta a un nodo del programa que no es un tema. */
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
    update_question_set_api_v1_question_sets__set_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                set_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PatchQuestionSetSchema"];
            };
        };
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
    link_answer_key_source_api_v1_question_sets__set_id__answer_keys__key_id__source_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                set_id: string;
                key_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LinkKeySourceRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KeySourceLinkSchema"];
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
    import_from_document_api_v1_question_sets__set_id__import_document_post: {
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
                "application/json": components["schemas"]["ImportQuestionsFromDocumentSchema"];
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
    outdated_sessions_api_v1_question_sets__set_id__outdated_sessions_get: {
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
                    "application/json": components["schemas"]["OutdatedSessionsSchema"];
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
    recalculate_set_api_v1_question_sets__set_id__recalculate_sessions_post: {
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
                    "application/json": components["schemas"]["BulkRecalculationSchema"];
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
    list_question_topic_conflicts_api_v1_question_topic_conflicts_get: {
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
                    "application/json": components["schemas"]["QuestionTopicConflictPageSchema"];
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
    list_question_topic_proposals_api_v1_question_topic_proposals_get: {
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
                    "application/json": components["schemas"]["QuestionTopicProposalPageSchema"];
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
    assign_question_topics_bulk_api_v1_questions_topics_bulk_post: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BulkTopicAssignmentsSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BulkTopicAssignmentReportSchema"];
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
            /** @description El cambio no encaja con lo que hay (`classification_conflict`), y se dice por qué. Por ejemplo, asignar una pregunta a un nodo del programa que no es un tema. */
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
    list_question_explanations_api_v1_questions__question_id__explanations_get: {
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
                    "application/json": components["schemas"]["ExplanationSchema"][];
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
    set_question_explanation_api_v1_questions__question_id__explanations_post: {
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
                "application/json": components["schemas"]["SetExplanationRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExplanationSchema"];
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
    list_question_topics_api_v1_questions__question_version_id__topics_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                question_version_id: string;
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
                    "application/json": components["schemas"]["QuestionTopicSchema"][];
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
    assign_question_topic_api_v1_questions__question_version_id__topics_post: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                question_version_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssignTopicRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuestionTopicAssignmentSchema"];
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
            /** @description El cambio no encaja con lo que hay (`classification_conflict`), y se dice por qué. Por ejemplo, asignar una pregunta a un nodo del programa que no es un tema. */
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
    unassign_question_topic_api_v1_questions__question_version_id__topics__curriculum_node_id__delete: {
        parameters: {
            query?: never;
            header?: {
                "X-OpoFuente-Actor"?: string | null;
            };
            path: {
                question_version_id: string;
                curriculum_node_id: string;
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
    index_health_api_v1_search_index_get: {
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
                    "application/json": components["schemas"]["IndexHealthSchema"];
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
    reindex_api_v1_search_reindex_post: {
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
                    "application/json": components["schemas"]["ReindexSchema"];
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
    get_stats_api_v1_stats_get: {
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
                    "application/json": components["schemas"]["StatsSchema"];
                };
            };
        };
    };
    student_mistakes_api_v1_student_mistakes_get: {
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
                    "application/json": components["schemas"]["StudentMistakesSchema"];
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
    student_mock_exam_plan_api_v1_student_mock_exams_get: {
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
                    "application/json": components["schemas"]["StudentMockExamPlanSchema"];
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
    student_create_mock_exam_api_v1_student_mock_exams_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StudentMockExamRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentSessionSchema"];
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
    student_official_exams_api_v1_student_official_exams_get: {
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
                    "application/json": components["schemas"]["StudentOfficialExamsSchema"];
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
    student_create_official_exam_api_v1_student_official_exams__posicion__sessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Su sitio en la lista de exámenes oficiales (el primero, el segundo). */
                posicion: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentSessionSchema"];
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
    student_overview_api_v1_student_overview_get: {
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
                    "application/json": components["schemas"]["StudentOverviewSchema"];
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
    student_progress_api_v1_student_progress_get: {
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
                    "application/json": components["schemas"]["StudentProgressSchema"];
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
    student_session_api_v1_student_sessions__sesion__get: {
        parameters: {
            query?: {
                /** @description Fila de la hoja de respuestas que se quiere leer. Sin ella se sirve la primera pregunta sin contestar, que es el avance de siempre. */
                position?: number | null;
            };
            header?: never;
            path: {
                /** @description Identificador de la sesión, el que devolvió al montarla. */
                sesion: string;
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
                    "application/json": components["schemas"]["StudentRunSchema"];
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
    student_abandon_api_v1_student_sessions__sesion__abandon_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                sesion: string;
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
                    "application/json": components["schemas"]["StudentAbandonSchema"];
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
    student_answer_api_v1_student_sessions__sesion__answers_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                sesion: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StudentAnswerRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentRunSchema"];
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
    student_finish_api_v1_student_sessions__sesion__finish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                sesion: string;
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
                    "application/json": components["schemas"]["StudentResultSchema"];
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
    student_session_result_api_v1_student_sessions__sesion__result_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                sesion: string;
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
                    "application/json": components["schemas"]["StudentSessionResultSchema"];
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
    student_start_api_v1_student_sessions__sesion__start_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                sesion: string;
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
                    "application/json": components["schemas"]["StudentRunSchema"];
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
    student_syllabus_api_v1_student_syllabus_get: {
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
                    "application/json": components["schemas"]["StudentSyllabusSchema"];
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
    student_create_test_api_v1_student_tests_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StudentTestRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentSessionSchema"];
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
    student_test_plan_api_v1_student_tests_plan_get: {
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
                    "application/json": components["schemas"]["StudentTestPlanSchema"];
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
    student_topic_api_v1_student_topics__codigo__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Código legible del tema, como `IV.10` (también se acepta `IV-10`). */
                codigo: string;
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
                    "application/json": components["schemas"]["StudentTopicSchema"];
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
    student_topic_notes_api_v1_student_topics__codigo__notes_get: {
        parameters: {
            query?: {
                /** @description El epígrafe oficial que se quiere leer, como `IV.7.2`. Sin él se sirve el primero. */
                capitulo?: string | null;
            };
            header?: never;
            path: {
                /** @description Código legible del tema, como `IV.10` (también se acepta `IV-10`). */
                codigo: string;
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
                    "application/json": components["schemas"]["StudentNotesSchema"];
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
    student_report_notes_api_v1_student_topics__codigo__reports_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Código legible del tema, como `IV.10`. */
                codigo: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StudentReportRequestSchema"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentReportSchema"];
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
    discard_study_session_api_v1_study_sessions__session_id__delete: {
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
                    "application/json": components["schemas"]["SessionDiscardSchema"];
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
    diagnostic_reading_api_v1_study_sessions__session_id__diagnostic_get: {
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
                    "application/json": components["schemas"]["DiagnosticReadingSchema"];
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

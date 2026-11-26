function escapeText(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[character]));
}

const GRADE_4_SESSION_GAMES = [
    {
        session: 1,
        title: "Sesión 1: Creo videos de la presentación de los animales vertebrados",
        icon: "bi-camera-reels-fill",
        color: "text-primary",
        badgeColor: "bg-primary",
        description: "Manejar las herramientas de la aplicación CapCut para la creación de videos e imágenes clasificando animales vertebrados.",
        gameName: "Reto CapCut: Animales Vertebrados",
        question: "¿Cuál es la diferencia principal entre un archivo de Video y una imagen animada en formato GIF?",
        options: [
            "El GIF se repite continuamente sin pista de sonido, mientras que el video tiene archivo de audio y mayor duración",
            "El GIF es impreso en papel y el video es solo música",
            "El GIF solo se puede abrir en Word",
            "No existe ninguna diferencia entre GIF y video"
        ],
        correct: "El GIF se repite continuamente sin pista de sonido, mientras que el video tiene archivo de audio y mayor duración",
        feedback: "¡Excelente! CapCut nos permite editar videos completos añadiendo imágenes de animales vertebrados y pistas de audio."
    },
    {
        session: 2,
        title: "Sesión 2: Elaboro videos sobre el cuidado del agua para el TikTok",
        icon: "bi-tiktok",
        color: "text-danger",
        badgeColor: "bg-danger",
        description: "Utiliza imágenes PNG, estilos de texto y configura el formato flyer ideal para publicar en TikTok.",
        gameName: "Reto CapCut: Cuidado del Agua en TikTok",
        question: "¿Qué ventaja principal ofrecen las imágenes en formato PNG para la edición de nuestros videos?",
        options: [
            "Tienen fondo transparente que permite superponerlas fácilmente sobre el video",
            "Tienen sonido integrado automáticamente",
            "Solo se pueden reproducir en televisión",
            "No se pueden modificar ni cambiar de tamaño"
        ],
        correct: "Tienen fondo transparente que permite superponerlas fácilmente sobre el video",
        feedback: "¡Muy bien! Las imágenes en PNG con transparencia son perfectas para colocar sobre nuestro video del cuidado del agua."
    },
    {
        session: 3,
        title: "Sesión 3: Diseño videos sobre los desastres naturales del Perú",
        icon: "bi-tsunami",
        color: "text-warning",
        badgeColor: "bg-warning text-dark",
        description: "Incorpora texto, efectos de animación para imágenes y comprende el proceso de importación y exportación.",
        gameName: "Reto CapCut: Desastres Naturales del Perú",
        question: "¿En qué consiste el procedimiento de 'Exportar' un video finalizado en CapCut?",
        options: [
            "Procesar y guardar el proyecto terminado en un formato de video (como MP4) para poder reproducirlo y compartirlo",
            "Eliminar todas las fotos guardadas en la computadora",
            "Apagar la pantalla del editor",
            "Imprimir el video en una hoja de papel"
        ],
        correct: "Procesar y guardar el proyecto terminado en un formato de video (como MP4) para poder reproducirlo y compartirlo",
        feedback: "¡Correcto! Exportar procesa nuestro proyecto de CapCut con imágenes y efectos para convertirlo en un video listo."
    },
    {
        session: 4,
        title: "Sesión 4: Elaboro un video reflexivo sobre el cuidado del medio ambiente",
        icon: "bi-cloud-check-fill",
        color: "text-success",
        badgeColor: "bg-success",
        description: "Incorpora audio, estilos de texto, videos tutoriales y entiende el almacenamiento en La Nube y tecnología QR.",
        gameName: "Reto CapCut: Medio Ambiente y La Nube",
        question: "¿Por qué se le conoce como 'La Nube' al almacenamiento digital de archivos y videos en Internet?",
        options: [
            "Porque permite guardar archivos en servidores de Internet para acceder a ellos desde cualquier lugar o mediante código QR",
            "Porque guarda los videos dentro de las nubes del cielo",
            "Porque cambia de color según el clima",
            "Porque solo funciona cuando está lloviendo"
        ],
        correct: "Porque permite guardar archivos en servidores de Internet para acceder a ellos desde cualquier lugar o mediante código QR",
        feedback: "¡Genial! La nube nos permite almacenar nuestros videos reflexivos y compartirlos fácilmente."
    },
    {
        session: 5,
        title: "Sesión 5: Elaboro un cuento para el área de Plan Lector",
        icon: "bi-file-earmark-word-fill",
        color: "text-primary",
        badgeColor: "bg-primary",
        description: "Utiliza Microsoft Word para crear textos narrativos con títulos con efectos, bordes de página, columnas periodísticas e imágenes en línea.",
        gameName: "Reto MS Word: Cuento de Plan Lector",
        question: "¿De qué color característico es el ícono de la aplicación Microsoft Word y con qué letra se identifica?",
        options: [
            "Es de color Azul y se identifica con la letra 'W'",
            "Es de color Verde y se identifica con la letra 'X'",
            "Es de color Rojo y se identifica con la letra 'P'",
            "Es de color Amarillo y se identifica con la letra 'A'"
        ],
        correct: "Es de color Azul y se identifica con la letra 'W'",
        feedback: "¡Exacto! Microsoft Word (ícono azul con la letra W) es el programa de procesamiento de textos utilizado para nuestros cuentos."
    }
];

const GRADE_4_SESSION_EVALUATIONS = {
    1: {
        title: "Evaluación Sesión 1: Animales Vertebrados en CapCut",
        description: "Evaluación de competencias sobre edición de video, importación de imágenes y clasificación de animales vertebrados.",
        questions: [
            {
                q: "¿Qué tipo de archivos importamos en CapCut para representar a los animales vertebrados?",
                options: ["Imágenes y fotos en formato gráfico (JPG/PNG)", "Impresiones de papel", "Cartillas de cartón", "Solo archivos de audio sin imagen"],
                answer: "Imágenes y fotos en formato gráfico (JPG/PNG)"
            },
            {
                q: "¿Cuál es el propósito principal de editar un video sobre la clasificación de los animales?",
                options: ["Presentar información educativa de forma dinámica y ordenada", "Eliminar todas las imágenes de la computadora", "Apagar el monitor", "Solo escuchar canciones"],
                answer: "Presentar información educativa de forma dinámica y ordenada"
            }
        ]
    },
    2: {
        title: "Evaluación Sesión 2: Cuidado del Agua para TikTok",
        description: "Evaluación sobre formato vertical, tamaño flyer y textos para TikTok en la edición con CapCut.",
        questions: [
            {
                q: "¿Cuál es el formato y tamaño ideal de video para publicar en redes como TikTok?",
                options: ["Formato vertical 9:16 (Flyer/Smartphone)", "Formato cuadrado 1:1 antiguo", "Formato panorámico gigante para cine", "Formato de texto impreso"],
                answer: "Formato vertical 9:16 (Flyer/Smartphone)"
            },
            {
                q: "¿Para qué agregamos títulos y textos descriptivos en el video del cuidado del agua?",
                options: ["Para comunicar el mensaje reflexivo sobre el ahorro del agua", "Para tapar las imágenes por completo", "Para borrar el video", "Para cambiar el color del monitor"],
                answer: "Para comunicar el mensaje reflexivo sobre el ahorro del agua"
            }
        ]
    },
    3: {
        title: "Evaluación Sesión 3: Desastres Naturales del Perú",
        description: "Evaluación sobre efectos visuales, tiempos de animación e importación/exportación de archivos.",
        questions: [
            {
                q: "¿Qué extensión de imagen moderna podemos importar para crear videos publicitarios o educativos?",
                options: ["Extensiones tipo PNG, JPG o WEBP", "Solo archivos de texto ejecutable", "Archivos de hoja de cálculo .xlsx", "Documentos impresos"],
                answer: "Extensiones tipo PNG, JPG o WEBP"
            },
            {
                q: "¿Por qué es importante ajustar los segundos de animación de cada imagen en un video?",
                options: ["Para que el espectador pueda leer el texto e interpretar la imagen con claridad", "Para que las imágenes pasen tan rápido que no se vean", "Para apagar el programa CapCut", "Para cambiar de teclado"],
                answer: "Para que el espectador pueda leer el texto e interpretar la imagen con claridad"
            }
        ]
    },
    4: {
        title: "Evaluación Sesión 4: Video Reflexivo Medio Ambiente, Nube y QR",
        description: "Evaluación sobre incorporación de audio, tecnología QR y almacenamiento digital en La Nube.",
        questions: [
            {
                q: "¿Qué función cumple un código QR al adjuntarse a una ficha de información sobre el medio ambiente?",
                options: ["Permite a los usuarios escanearlo con el celular para abrir y ver el video alojado en La Nube", "Sustituye la pantalla de la computadora", "Limpia los archivos de la memoria", "Imprime automáticamente el video"],
                answer: "Permite a los usuarios escanearlo con el celular para abrir y ver el video alojado en La Nube"
            },
            {
                q: "¿Qué recurso multimedia añadimos para que un video reflexivo transmita emoción e inspiración?",
                options: ["Pistas de audio y música de fondo adecuada", "Imágenes borrosas", "Textos sin formato", "Silencio total sin voz"],
                answer: "Pistas de audio y música de fondo adecuada"
            }
        ]
    },
    5: {
        title: "Evaluación Sesión 5: Cuento para el área de Plan Lector (MS Word)",
        description: "Evaluación sobre creación de textos narrativos, bordes de página, efectos de títulos y columnas en Word.",
        questions: [
            {
                q: "¿Qué herramienta de Microsoft Word se usa para dividir el texto del cuento en columnas como en los periódicos?",
                options: ["Formato de Columnas (Disposición/Diseño)", "Borde de Página", "Color de Fuente", "Alineación a la izquierda"],
                answer: "Formato de Columnas (Disposición/Diseño)"
            },
            {
                q: "¿Cómo podemos enriquecer visualmente la lectura de nuestro cuento en Microsoft Word?",
                options: ["Insertando imágenes en línea relacionadas con los personajes del cuento", "Borrando todo el texto escrito", "Cambiando la fecha de la computadora", "Desconectando la impresora"],
                answer: "Insertando imágenes en línea relacionadas con los personajes del cuento"
            }
        ]
    }
};

let evaluationTimer = null;
let selectedTopicId = null;

function truncateText(value, maxLength = 450) {
    const text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength - 3).trimEnd() + '...';
}

const messagesModal = document.getElementById('messagesModal');
if (messagesModal) messagesModal.addEventListener('show.bs.modal', loadStudentMessages);

async function loadStudentMessages() {
    const messagesList = document.getElementById('messages-student-list');
    if (!messagesList) return;
    messagesList.innerHTML = '<p class="text-muted text-center">Cargando mensajes...</p>';
    try {
        const response = await fetch('/student/api/messages');
        const data = await response.json();
        if (!data.success || !data.messages?.length) {
            messagesList.innerHTML = '<p class="text-muted text-center">No tienes mensajes de tu profesor aún.</p>';
            return;
        }
        messagesList.innerHTML = data.messages.map(message => `<article class="student-message-card alert ${message.is_read ? 'alert-success' : 'alert-info'} mb-2" data-message-id="${message.id}"><div class="d-flex justify-content-between align-items-start gap-2"><div class="flex-grow-1"><strong>${message.message}</strong><small class="d-block text-muted mt-1">${new Date(message.created_at).toLocaleString('es-ES')}</small></div><button type="button" class="btn btn-sm ${message.is_read ? 'btn-success' : 'btn-secondary'} btn-mark-message-read" ${message.is_read ? 'disabled' : ''}>${message.is_read ? 'Leído' : 'Marcar como leído'}</button></div></article>`).join('');
        messagesList.querySelectorAll('.btn-mark-message-read:not(:disabled)').forEach(button => button.addEventListener('click', async () => {
            const card = button.closest('.student-message-card');
            button.disabled = true;
            const response = await fetch(`/student/api/messages/${card.dataset.messageId}/read`, {method: 'PUT'});
            const result = await response.json();
            if (result.success) {
                button.textContent = 'Leído';
                button.className = 'btn btn-sm btn-success btn-mark-message-read';
                card.classList.remove('alert-info');
                card.classList.add('alert-success');
            } else {
                button.disabled = false;
            }
        }));
    } catch (error) {
        messagesList.innerHTML = '<p class="text-danger text-center">No se pudieron cargar los mensajes.</p>';
    }
}

async function loadStudentRiskPrediction() {
    const card = document.getElementById('student-risk-card');
    if (!card) return;

    try {
        const response = await fetch('/student/api/risk-prediction');
        if (!response.ok) return;
        const data = await response.json();

        // Actualizar etiqueta y badge de riesgo
        const modelNotice = document.getElementById('student-model-notice');
        if (modelNotice) modelNotice.textContent = data.model_notice || '';
        const badge = document.getElementById('student-risk-badge');
        const levelLabel = document.getElementById('student-risk-level-label');
        if (badge && levelLabel) {
            levelLabel.textContent = data.risk_level_label || 'No disponible';
            badge.className = `badge ${data.badge_class || 'bg-primary'} fs-6 px-3 py-2 rounded-pill shadow-sm`;
        }

        // Estado académico
        const statusEl = document.getElementById('student-academic-status');
        if (statusEl && data.academic_status) {
            statusEl.textContent = data.academic_status;
        }

        // Porcentaje y barra de progreso
        const percentageEl = document.getElementById('student-risk-percentage');
        const progressBar = document.getElementById('student-risk-progress-bar');
        if (percentageEl) {
            if (data.probability !== null && data.probability !== undefined) {
                const percent = Math.round(data.probability * 100);
                percentageEl.textContent = `${percent}%`;
                if (progressBar) {
                    progressBar.style.width = `${percent}%`;
                    progressBar.className = `progress-bar ${data.risk_level === 'HIGH' ? 'bg-danger' : (data.risk_level === 'MEDIUM' ? 'bg-warning' : 'bg-success')}`;
                }
                percentageEl.className = `display-6 fw-bold ${data.risk_level === 'HIGH' ? 'text-danger' : (data.risk_level === 'MEDIUM' ? 'text-warning' : 'text-success')}`;
            } else {
                percentageEl.textContent = '--%';
                if (progressBar) progressBar.style.width = '0%';
            }
        }

        // Mensaje motivacional
        const alertBox = document.getElementById('student-motivational-alert');
        const alertIcon = document.getElementById('student-motivational-icon');
        const alertText = document.getElementById('student-motivational-text');
        if (alertBox && alertText) {
            alertText.textContent = data.motivational_message || 'Continúa practicando para seguir avanzando.';
            const alertClass = data.risk_level === 'HIGH' ? 'alert-danger' : (data.risk_level === 'MEDIUM' ? 'alert-warning' : 'alert-success');
            alertBox.className = `alert ${alertClass} border-0 d-flex align-items-center gap-2 mb-3 py-2 px-3 rounded-3`;
            if (alertIcon) {
                alertIcon.textContent = data.risk_level === 'HIGH' ? '💪' : (data.risk_level === 'MEDIUM' ? '🚀' : '⭐');
            }
        }

        // Factores explicativos
        const factorsList = document.getElementById('student-risk-factors-list');
        if (factorsList && Array.isArray(data.factors) && data.factors.length > 0) {
            factorsList.innerHTML = data.factors.map(factor => `
                <li class="text-secondary mb-1 d-flex align-items-start gap-1">
                    <span class="text-primary">•</span> <span>${factor}</span>
                </li>
            `).join('');
        }

        // Recomendaciones
        const recsList = document.getElementById('student-risk-recommendations-list');
        if (recsList && Array.isArray(data.recommendations) && data.recommendations.length > 0) {
            recsList.innerHTML = data.recommendations.map(rec => `
                <li class="text-dark mb-1 d-flex align-items-start gap-1">
                    <i class="bi bi-check-circle-fill text-success mt-1" style="font-size: 0.75rem;"></i>
                    <span>${rec}</span>
                </li>
            `).join('');
        }
    } catch (err) {
        console.warn('No se pudo actualizar la predicción del estudiante:', err);
    }
}

function getMaterialsNavButton() {
    return document.querySelector('.sidebar-btn[data-section="material"]');
}

function enableStudentMaterialsSection() {
    const materialButton = getMaterialsNavButton();
    if (!materialButton) return;
    materialButton.disabled = false;
    materialButton.removeAttribute('title');
}

function openClassAndEnableMaterials(topicId, topicTitle) {
    if (!topicId) return;
    selectedTopicId = String(topicId);
    enableStudentMaterialsSection();
    const selectedBadge = document.getElementById('selected-topic-badge');
    if (selectedBadge) {
        selectedBadge.classList.remove('text-secondary');
        selectedBadge.classList.add('text-primary');
        selectedBadge.innerHTML = `<i class="bi bi-stars"></i> ${topicTitle || 'Clase seleccionada'}`;
    }
    const selectedView = document.getElementById('selected-activity-view');
    if (selectedView) {
        selectedView.hidden = true;
        selectedView.innerHTML = '';
    }
    switchToStudentSection('material');
    loadLesson(topicId);
    loadMaterials(topicId);
}

function switchToStudentSection(sectionName) {
    const navBtn = document.querySelector(`.sidebar-btn[data-section="${sectionName}"]`);
    if (navBtn) {
        if (sectionName === 'material' && navBtn.disabled) return;
        navBtn.click();
    } else {
        const panels = document.querySelectorAll('.section-panel');
        panels.forEach(p => p.classList.remove('active'));
        const target = document.getElementById('section-' + sectionName);
        if (target) {
            target.classList.add('active');
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

function attachAdaptiveActionHandlers() {
    document.querySelectorAll('.btn-adaptive-action').forEach(btn => {
        btn.onclick = () => {
            const actionType = btn.dataset.actionType;
            const materialId = parseInt(btn.dataset.materialId || '1', 10);
            const gameId = parseInt(btn.dataset.gameId || '1', 10);
            const topicId = parseInt(btn.dataset.topicId || '4', 10);

            if (actionType === 'open_material') {
                enableStudentMaterialsSection();
                switchToStudentSection('material');
                setTimeout(() => {
                    if (typeof openReadMaterialModal === 'function') {
                        openReadMaterialModal(materialId);
                    } else {
                        const matCard = document.getElementById(`material-card-col-${materialId}`);
                        if (matCard) matCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 300);
            } else if (actionType === 'play_game') {
                switchToStudentSection('juegos');
                setTimeout(() => {
                    if (typeof openReinforcementGame === 'function') {
                        openReinforcementGame(gameId);
                    }
                }, 300);
            } else if (actionType === 'open_games') {
                switchToStudentSection('juegos');
            } else if (actionType === 'open_evaluation') {
                switchToStudentSection('evaluaciones');
                setTimeout(() => {
                    const evalBtn = document.querySelector(`.btn-eval-tab[data-eval="${topicId}"]`);
                    if (evalBtn) {
                        document.querySelectorAll('.btn-eval-tab').forEach(b => b.classList.remove('active'));
                        evalBtn.classList.add('active');
                    }
                    if (typeof renderSessionEvaluation === 'function') {
                        renderSessionEvaluation(topicId);
                    }
                }, 300);
            }
        };
    });
}

function attachPersonalizedTrainingHandler() {
    const button = document.querySelector('.btn-personalized-training');
    if (!button) return;
    button.onclick = () => {
        const gameId = Number(button.dataset.gameId || 0);
        const materialId = Number(button.dataset.materialId || 0);
        if (gameId) {
            switchToStudentSection('juegos');
            setTimeout(() => document.querySelector(`[data-ai-game-id="${gameId}"]`)?.click(), 350);
        } else if (materialId) {
            enableStudentMaterialsSection();
            switchToStudentSection('material');
            setTimeout(() => window.openReadMaterialModal?.(materialId), 350);
        } else {
            switchToStudentSection('recomendaciones');
        }
    };
}

async function loadPersonalizedTraining() {
    const title = document.getElementById('personalized-training-title');
    if (!title) return;
    try {
        const response = await fetch('/student/api/adaptive-learning');
        const data = await response.json();
        const training = data.training;
        if (!response.ok || !data.success || !training) return;
        const activity = training.recommended_activity || {};
        title.textContent = activity.title || 'Preparando tu siguiente práctica';
        document.getElementById('personalized-training-message').textContent = activity.message || '';
        document.getElementById('personalized-training-difficulty').textContent = training.recommended_difficulty || 'medium';
        const button = document.querySelector('.btn-personalized-training');
        if (button) {
            button.dataset.trainingType = activity.type || '';
            button.dataset.gameId = activity.game_id || '';
            button.dataset.materialId = activity.material_id || '';
            button.disabled = !activity.game_id && !activity.material_id;
        }
        attachPersonalizedTrainingHandler();
    } catch (error) {
        console.warn('No se pudo cargar el entrenamiento personalizado.', error);
    }
}

async function loadRecommendations() {
    try {
        const resp = await fetch('/student/api/recommendations');
        if (!resp.ok) return;
        const data = await resp.json();
        if (!data.success) return;

        const diag = data.student_diagnosis || {};

        const nameEl = document.getElementById('adaptive-student-name');
        if (nameEl && diag.student_name) nameEl.textContent = diag.student_name;

        const evidenceEl = document.getElementById('adaptive-evidence-text');
        if (evidenceEl && diag.evidence) evidenceEl.textContent = diag.evidence;

        const topicEl = document.getElementById('adaptive-topic-text');
        if (topicEl && data.primary_topic) topicEl.textContent = data.primary_topic;

        const notesVal = document.getElementById('pillar-notes-val');
        if (notesVal && diag.average_score !== undefined) notesVal.textContent = `${diag.average_score}/20`;

        const evalsVal = document.getElementById('pillar-evals-val');
        if (evalsVal && diag.failed_questions_count !== undefined) evalsVal.textContent = `${diag.failed_questions_count} fallas`;

        const gamesVal = document.getElementById('pillar-games-val');
        if (gamesVal && diag.games_count !== undefined) gamesVal.textContent = `${diag.games_count} completados`;

        const mlVal = document.getElementById('pillar-ml-val');
        if (mlVal && diag.ml_risk_level) mlVal.textContent = `${diag.ml_risk_level} (${diag.ml_probability || '--'}%)`;

        const headlineEl = document.getElementById('adaptive-headline');
        if (headlineEl && data.headline) headlineEl.textContent = data.headline;

        // Renderizar las 3 acciones canónicas
        const grid = document.getElementById('adaptive-actions-grid');
        if (grid && data.actions && data.actions.length) {
            grid.innerHTML = data.actions.map(act => `
                <div class="col-md-4">
                    <div class="card h-100 border-2 shadow-xs rounded-4 p-3 bg-white border-${act.color} d-flex flex-column">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="badge bg-${act.color} px-2 py-1 rounded-pill small fw-bold">
                                ${act.badge}
                            </span>
                            <i class="bi ${act.icon} text-${act.color} fs-4"></i>
                        </div>
                        <h5 class="fw-bold text-dark mb-1">${act.title}</h5>
                        <p class="text-secondary small flex-grow-1 mb-3" style="line-height: 1.4;">${act.summary}</p>
                        <button type="button" class="btn btn-${act.color} btn-sm w-100 rounded-pill fw-bold btn-adaptive-action mt-auto"
                            data-action-type="${act.action_type}"
                            data-material-id="${act.material_id || 1}"
                            data-game-id="${act.game_id || 1}"
                            data-topic-id="${act.topic_id || 4}">
                            <i class="bi bi-arrow-right-circle me-1"></i> ${act.button_text}
                        </button>
                    </div>
                </div>
            `).join('');
            attachAdaptiveActionHandlers();
        }

        // Actualizar la lista en la tarjeta de inicio del alumno
        const homeList = document.getElementById('student-risk-recommendations-list');
        if (homeList && data.actions && data.actions.length) {
            homeList.innerHTML = data.actions.map(act => `
                <li class="text-dark mb-1 d-flex align-items-start gap-1">
                    <span class="fw-semibold text-primary">${act.badge}:</span>
                    <span class="text-secondary">${act.title}</span>
                </li>
            `).join('');
        }
    } catch (err) {
        console.warn('Error al actualizar recomendaciones adaptativas:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#section-juegos .card').forEach(card => {
        if (card.textContent.includes('Práctica Lúdica Antes del Examen') || card.querySelector('#reinforcement-games-selector-grid')) {
            card.remove();
        }
    });
    document.querySelectorAll('#section-juegos .section-title').forEach(title => {
        if (title.textContent.includes('Retos Educativos por Sesiones')) {
            title.closest('.d-flex.align-items-center.justify-content-between')?.remove();
        }
    });
    document.getElementById('session-filter-chips')?.remove();
    document.querySelector('#section-juegos > .alert.alert-success')?.remove();

    loadStudentRiskPrediction();
    loadRecommendations();
    attachAdaptiveActionHandlers();
    loadPersonalizedTraining();
    attachPersonalizedTrainingHandler();

    document.querySelectorAll('.btn-go-to-recommendations').forEach(btn => {
        btn.addEventListener('click', () => switchToStudentSection('recomendaciones'));
    });

    const panels = document.querySelectorAll('.section-panel');
    const navBtns = document.querySelectorAll('.sidebar-btn[data-section]');

    document.getElementById('btn-back-to-materials-from-games')?.addEventListener('click', () => {
        switchToStudentSection('material');
    });

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.dataset.section;
            const materialButton = getMaterialsNavButton();
            if (section === 'material' && materialButton?.disabled) return;
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            panels.forEach(p => p.classList.remove('active'));
            const target = document.getElementById('section-' + section);
            if (target) {
                target.classList.add('active');
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (section === 'material') {
                    if (selectedTopicId) {
                        loadMaterials(selectedTopicId);
                    }
                }
                if (section === 'juegos') renderSessionGames();
                if (section === 'evaluaciones') renderSessionEvaluation(document.querySelector('.btn-eval-tab')?.dataset.eval);
                if (section === 'recomendaciones') loadRecommendations();
                if (section === 'progreso') loadProgress();
            }
        });
    });

    document.querySelectorAll('.recommendation-filter').forEach(filter => {
        filter.addEventListener('click', () => {
            document.querySelectorAll('.recommendation-filter').forEach(item => item.classList.remove('active'));
            filter.classList.add('active');
            const category = filter.dataset.filter;
            document.querySelectorAll('[data-recommendation-category]').forEach(card => {
                card.hidden = category !== 'all' && card.dataset.recommendationCategory !== category;
            });
        });
    });

    document.querySelectorAll('.activity-route-card').forEach(route => {
        route.addEventListener('click', () => {
            if (!selectedTopicId) return;
            const target = route.dataset.activityTarget;
            if (target === 'lesson-content') {
                const selectedView = document.getElementById('selected-activity-view');
                if (!selectedView) return;
                selectedView.hidden = false;
                renderPracticalActivity(selectedTopicId, selectedView);
                selectedView.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }
            const selectedView = document.getElementById('selected-activity-view');
            if (!selectedView) return;
            if (target === 'juegos') {
                switchToStudentSection('juegos');
                // The generated games are scoped to the class the child just
                // opened. Calling the endpoint without this id queried topic
                // 0 and made a published game look unavailable.
                loadAiPublishedGames(selectedTopicId);
                return;
            }
            selectedView.hidden = false;
            selectedView.innerHTML = '<p class="text-muted mb-0">Cargando contenido del tema seleccionado...</p>';
            if (target === 'evaluaciones') renderSessionEvaluation(selectedTopicId, 'selected-activity-view');
            selectedView.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    document.getElementById('recommendations-dynamic-list')?.addEventListener('click', event => {
        const button = event.target.closest('.recommendation-cta');
        if (!button) return;
        showRecommendationDetails(button.closest('.recommendation-card'), button.dataset.targetSection || 'material');
    });

    document.querySelectorAll('.btn-comenzar').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const topicId = btn.dataset.topicId;
            if (!topicId) return;
            const topicTitle = btn.closest('.topic-card')?.querySelector('.topic-info h5')?.textContent?.trim() || '';
            openClassAndEnableMaterials(topicId, topicTitle);
        });
    });

    // Inicializar juegos y evaluaciones
    renderSessionGames();
    loadAiPublishedGames();
    // La evaluación se genera únicamente cuando el alumno elige una clase y pulsa su tarjeta.

    // Manejador de Tabs de Evaluación
    const evalTabs = document.querySelectorAll('#evaluations-selector .btn-eval-tab');
    evalTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            evalTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderSessionEvaluation(parseInt(tab.dataset.eval));
        });
    });
});

// =========================================================================
// GOAL 5: Juegos Interactivos de Reforzamiento (Práctica antes del Examen)
// =========================================================================
let reinforcementGamesCache = [];

async function loadReinforcementGames() {
    const container = document.getElementById('reinforcement-games-selector-grid');
    if (!container) return;

    try {
        const resp = await fetch('/student/api/reinforcement-games');
        const data = await resp.json();
        if (data.success && data.games) {
            reinforcementGamesCache = data.games;
            renderReinforcementGamesCards(data.games);
        } else {
            container.innerHTML = '<div class="col-12 text-muted">No se pudieron cargar los juegos de reforzamiento.</div>';
        }
    } catch (err) {
        console.error('Error cargando juegos de reforzamiento:', err);
        container.innerHTML = '<div class="col-12 text-danger">Error de conexión al cargar juegos de reforzamiento.</div>';
    }
}

function renderReinforcementGamesCards(games) {
    const container = document.getElementById('reinforcement-games-selector-grid');
    if (!container) return;

    const gameIcons = {
        'opcion_multiple': 'bi-calculator text-primary',
        'verdadero_falso': 'bi-globe-americas text-warning',
        'completar': 'bi-flower1 text-success'
    };

    const typeBadges = {
        'opcion_multiple': '<span class="badge bg-primary-subtle text-primary border border-primary-subtle">Opción Múltiple</span>',
        'verdadero_falso': '<span class="badge bg-warning-subtle text-dark border border-warning-subtle">Verdadero / Falso</span>',
        'completar': '<span class="badge bg-success-subtle text-success border border-success-subtle">Completar</span>'
    };

    container.innerHTML = games.map(g => `
    <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm rounded-4 p-3 bg-light hover-card position-relative border-top border-3 ${g.id === 1 ? 'border-primary' : g.id === 2 ? 'border-warning' : 'border-success'}">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    ${typeBadges[g.game_type] || '<span class="badge bg-secondary">Juego</span>'}
                    <i class="bi ${gameIcons[g.game_type] || 'bi-controller text-info'} fs-4"></i>
                </div>
                <h6 class="fw-bold text-dark mb-1">${g.title}</h6>
                <p class="text-muted small mb-2">Misión: ${g.topic_title}</p>
                <p class="text-secondary small flex-grow-1 mb-3" style="font-size: 0.82rem;">${g.instructions || ''}</p>
                <button class="btn btn-outline-success btn-sm w-100 rounded-pill fw-bold btn-launch-game" data-game-id="${g.id}">
                    <i class="bi bi-play-circle-fill me-1"></i> Ver mi misión
                </button>
            </div>
        </div>
    `).join('');

    container.querySelectorAll('.btn-launch-game').forEach(btn => {
        btn.addEventListener('click', () => {
            const gameId = parseInt(btn.dataset.gameId, 10);
            openReinforcementGame(gameId);
        });
    });
}

function openReinforcementGame(gameId) {
    const arena = document.getElementById('reinforcement-game-arena');
    const game = reinforcementGamesCache.find(g => g.id === gameId);
    if (!arena || !game) return;
    const rules = {
        opcion_multiple: 'Escoge la pista que responde mejor a la pregunta.',
        verdadero_falso: 'Lee con calma y elige la respuesta que creas correcta.',
        completar: 'Busca una palabra que complete la idea.'
    };
    arena.style.display = 'block';
    arena.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    arena.innerHTML = `
        <section class="mission-screen" aria-label="Inicio de misión de práctica">
            <div class="mission-mascot" aria-hidden="true"><i class="bi bi-lightning-charge-fill"></i></div>
            <div>
                <span class="mission-eyebrow"><i class="bi bi-stars"></i> Misión de práctica</span>
                <h2>${escapeText(game.title)}</h2>
                <p>Antes de avanzar, tienes un reto corto para entrenar lo que aprendiste.</p>
                <div class="mission-rules">
                    <span class="mission-rule"><i class="bi bi-bookmark-star-fill"></i>${escapeText(game.topic_title || 'Tu clase')}</span>
                    <span class="mission-rule"><i class="bi bi-lightbulb-fill"></i>${rules[game.game_type] || 'Resuelve el reto a tu ritmo.'}</span>
                    <span class="mission-rule"><i class="bi bi-star-fill"></i>Gana una estrella</span>
                </div>
                <button type="button" class="mission-start-btn" id="btn-start-rf-mission"><i class="bi bi-play-fill me-1"></i> Comenzar</button>
            </div>
        </section>`;
    arena.querySelector('#btn-start-rf-mission')?.addEventListener('click', () => renderReinforcementRound(gameId));
}

function renderReinforcementRound(gameId) {
    const arena = document.getElementById('reinforcement-game-arena');
    if (!arena) return;

    const game = reinforcementGamesCache.find(g => g.id === gameId);
    if (!game) return;

    arena.style.display = 'block';
    arena.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    let gameContentHtml = '';
    const startTime = Date.now();

    if (game.game_type === 'opcion_multiple') {
        // Juego 1: ¿Cuánto es 5x5?
        gameContentHtml = `
            <div class="p-3 bg-light rounded-3 mb-3 border">
                <h5 class="fw-bold text-dark mb-3">
                    <i class="bi bi-question-circle-fill text-primary me-2"></i> ${game.question}
                </h5>
                <div class="d-grid gap-2" id="rf-options-container">
                    ${(game.options || []).map((opt, idx) => `
                        <button class="btn btn-outline-primary text-start p-3 rounded-3 rf-opt-btn fw-bold d-flex align-items-center justify-content-between" data-val="${opt}">
                            <span><span class="badge bg-primary text-white me-2">${String.fromCharCode(65 + idx)}</span> ${opt}</span>
                            <i class="bi bi-circle rf-check-icon"></i>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    } else if (game.game_type === 'verdadero_falso') {
        // Juego 2: La tierra gira alrededor del sol.
        gameContentHtml = `
            <div class="p-3 bg-light rounded-3 mb-3 border">
                <div class="alert alert-info py-2 small mb-3">
                    <i class="bi bi-info-circle me-1"></i> Lee con atención la afirmación y determina si es verdadera o falsa.
                </div>
                <h5 class="fw-bold text-dark mb-4 text-center py-2 border-bottom">
                    "${game.question}"
                </h5>
                <div class="row g-3 justify-content-center" id="rf-options-container">
                    <div class="col-sm-6">
                        <button class="btn btn-outline-success w-100 p-3 rounded-4 rf-opt-btn fw-bold fs-5 text-center" data-val="Verdadero">
                            <i class="bi bi-check-circle-fill me-2 fs-4"></i> Verdadero
                        </button>
                    </div>
                    <div class="col-sm-6">
                        <button class="btn btn-outline-danger w-100 p-3 rounded-4 rf-opt-btn fw-bold fs-5 text-center" data-val="Falso">
                            <i class="bi bi-x-circle-fill me-2 fs-4"></i> Falso
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else if (game.game_type === 'completar') {
        // Juego 3: La fotosíntesis ocurre en ______
        const parts = game.question.split('______');
        const before = parts[0] || 'La fotosíntesis ocurre en ';
        const after = parts[1] || '';

        gameContentHtml = `
            <div class="p-3 bg-light rounded-3 mb-3 border">
                <div class="alert alert-success py-2 small mb-3">
                    <i class="bi bi-lightbulb me-1"></i> Puedes pulsar una palabra del banco o escribirla en el espacio en blanco.
                </div>
                <div class="fs-5 fw-bold text-dark text-center my-4 p-3 bg-white rounded-3 shadow-sm border">
                    ${before}
                    <span id="rf-blank-space" class="badge bg-warning-subtle text-dark border border-warning px-3 py-2 fs-5 mx-1" style="min-width: 140px; display: inline-block;">
                        ______
                    </span>
                    ${after}
                </div>

                <div class="text-center mb-3">
                    <label class="form-label small fw-bold text-muted d-block">Banco de Palabras (haz clic para completar):</label>
                    <div class="d-flex justify-content-center gap-2 flex-wrap" id="rf-word-bank">
                        ${(game.options || []).map(opt => `
                            <button type="button" class="btn btn-outline-success rounded-pill px-3 fw-bold rf-word-btn" data-word="${opt}">
                                <i class="bi bi-plus-circle me-1"></i> ${escapeText(opt)}
                            </button>
                        `).join('')}
                    </div>
                </div>

                <div class="mt-3 text-center">
                    <div class="input-group justify-content-center" style="max-width: 400px; margin: 0 auto;">
                        <span class="input-group-text bg-white"><i class="bi bi-pencil-fill text-muted"></i></span>
                        <input type="text" id="rf-text-input" class="form-control" placeholder="Escribe tu respuesta aquí...">
                    </div>
                </div>
            </div>
        `;
    }

    arena.innerHTML = `
        <header class="game-header">
            <div><span class="game-kicker"><i class="bi bi-lightning-charge-fill"></i> Reto de práctica</span><h2>${escapeText(game.title)}</h2></div>
            <button class="game-exit-btn" type="button" onclick="document.getElementById('reinforcement-game-arena').style.display='none'" aria-label="Salir de la misión"><i class="bi bi-x-lg"></i><span>Salir</span></button>
        </header>
        <div class="mission-progress" aria-label="Progreso del reto">
            <span id="rf-progress-label">Elige una pista</span>
            <div class="mission-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="mission-progress-value" id="rf-progress-value" style="--progress:0%"></div></div>
            <span class="mission-reward"><i class="bi bi-star-fill"></i> +1</span>
        </div>
        <div class="game-stage">${gameContentHtml}</div>
        <div id="rf-feedback-box" class="mt-3" style="display: none;"></div>
        <div class="text-center mt-3"><button id="btn-submit-rf-game" class="game-primary-btn" disabled><i class="bi bi-check2-circle me-1"></i> Comprobar mi respuesta</button></div>`;

    let selectedAnswer = null;
    const submitBtn = document.getElementById('btn-submit-rf-game');
    const feedbackBox = document.getElementById('rf-feedback-box');

    if (game.game_type === 'opcion_multiple' || game.game_type === 'verdadero_falso') {
        const optBtns = arena.querySelectorAll('.rf-opt-btn');
        optBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                optBtns.forEach(b => {
                    b.classList.remove('active', 'btn-primary', 'btn-success', 'btn-danger', 'text-white');
                    if (game.game_type === 'opcion_multiple') {
                        b.classList.add('btn-outline-primary');
                        const icon = b.querySelector('.rf-check-icon');
                        if (icon) icon.className = 'bi bi-circle rf-check-icon';
                    } else {
                        if (b.dataset.val === 'Verdadero') b.classList.add('btn-outline-success');
                        else b.classList.add('btn-outline-danger');
                    }
                });

                if (game.game_type === 'opcion_multiple') {
                    btn.classList.remove('btn-outline-primary');
                    btn.classList.add('btn-primary', 'text-white', 'active');
                    const icon = btn.querySelector('.rf-check-icon');
                    if (icon) icon.className = 'bi bi-check-circle-fill rf-check-icon text-white';
                } else {
                    if (btn.dataset.val === 'Verdadero') {
                        btn.classList.remove('btn-outline-success');
                        btn.classList.add('btn-success', 'text-white', 'active');
                    } else {
                        btn.classList.remove('btn-outline-danger');
                        btn.classList.add('btn-danger', 'text-white', 'active');
                    }
                }

                selectedAnswer = btn.dataset.val;
                submitBtn.disabled = false;
                const progress = arena.querySelector('#rf-progress-value');
                const progressLabel = arena.querySelector('#rf-progress-label');
                if (progress) progress.style.setProperty('--progress', '45%');
                if (progressLabel) progressLabel.textContent = 'Pista elegida: revisa tu respuesta';
            });
        });
    } else if (game.game_type === 'completar') {
        const textInput = document.getElementById('rf-text-input');
        const blankSpace = document.getElementById('rf-blank-space');
        const wordBtns = arena.querySelectorAll('.rf-word-btn');

        wordBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                wordBtns.forEach(b => {
                    b.classList.remove('btn-success', 'text-white');
                    b.classList.add('btn-outline-success');
                });
                btn.classList.remove('btn-outline-success');
                btn.classList.add('btn-success', 'text-white');

                selectedAnswer = btn.dataset.word;
                if (blankSpace) blankSpace.textContent = selectedAnswer;
                if (textInput) textInput.value = selectedAnswer;
                submitBtn.disabled = false;
                const progress = arena.querySelector('#rf-progress-value');
                const progressLabel = arena.querySelector('#rf-progress-label');
                if (progress) progress.style.setProperty('--progress', '45%');
                if (progressLabel) progressLabel.textContent = 'Palabra elegida: revisa tu respuesta';
            });
        });

        if (textInput) {
            textInput.addEventListener('input', () => {
                const val = textInput.value.trim();
                selectedAnswer = val;
                if (blankSpace) blankSpace.textContent = val || '______';
                submitBtn.disabled = val.length === 0;
                const progress = arena.querySelector('#rf-progress-value');
                const progressLabel = arena.querySelector('#rf-progress-label');
                if (progress) progress.style.setProperty('--progress', val ? '45%' : '0%');
                if (progressLabel) progressLabel.textContent = val ? 'Palabra elegida: revisa tu respuesta' : 'Elige una pista';
            });
        }
    }

    submitBtn.addEventListener('click', async () => {
        if (!selectedAnswer) return;
        submitBtn.disabled = true;
        const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));

        try {
            const resp = await fetch(`/student/api/reinforcement-games/${game.id}/play`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    answer: selectedAnswer,
                    time_spent: timeSpent
                })
            });
            const data = await resp.json();
            if (!resp.ok || !data.success) {
                feedbackBox.style.display = 'block';
                feedbackBox.innerHTML = `<div class="alert alert-danger">${data.error || 'Error al calificar'}</div>`;
                submitBtn.disabled = false;
                return;
            }

            const res = data.result;
            feedbackBox.style.display = 'block';
            const progress = arena.querySelector('#rf-progress-value');
            const progressLabel = arena.querySelector('#rf-progress-label');
            if (progress) progress.style.setProperty('--progress', res.is_correct ? '100%' : '45%');
            if (progressLabel) progressLabel.textContent = res.is_correct ? 'Reto completado' : 'Buen intento: vuelve a revisar';

            if (res.is_correct) {
                feedbackBox.innerHTML = `
                    <div class="game-feedback is-correct"><div class="celebration-stars"><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i></div><span class="game-feedback-icon"><i class="bi bi-trophy-fill"></i></span><h3>¡Misión completada!</h3><p>${escapeText(res.feedback || 'Resolviste el reto correctamente.')}</p><p><strong>Ganaste una estrella para tu progreso.</strong></p></div>
                `;
            } else {
                feedbackBox.innerHTML = `
                    <div class="game-feedback is-try-again"><span class="game-feedback-icon"><i class="bi bi-lightbulb-fill"></i></span><h3>¡Casi lo logras!</h3><p>${escapeText(res.feedback || 'Mira la pista y vuelve a intentarlo.')}</p><p>Todo explorador aprende en cada intento.</p></div>
                `;
            }

            // Actualizar progreso general y recomendaciones en vivo
            loadProgress();
            loadRecommendations();
        } catch (e) {
            console.error('Error enviando respuesta del juego:', e);
            feedbackBox.style.display = 'block';
            feedbackBox.innerHTML = `<div class="alert alert-danger">Error de comunicación con el servidor.</div>`;
            submitBtn.disabled = false;
        }
    });
}

// =========================================================================
// GOAL: Juegos Educativos Mágicos Generados por IA (UX Infantil)
// =========================================================================
let aiPublishedGamesCache = [];

async function renderSessionGames(filterSession = 'all') {
    const grid = document.getElementById('sessions-games-grid');
    if (!grid) return;

    grid.innerHTML = '<div class="col-12"><div class="alert alert-info">Cargando juegos...</div></div>';

    const filteredGames = [];

    if (filteredGames.length === 0) {
        grid.innerHTML = '';
        return;
    }

    const sessionCards = filteredGames.map(game => `
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm rounded-4 overflow-hidden panel-card position-relative p-3">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="badge ${game.badgeColor} rounded-pill px-3 py-1 font-weight-bold">
                        Sesión ${game.session}
                    </span>
                    <i class="bi ${game.icon} ${game.color} fs-3"></i>
                </div>
                <h5 class="fw-bold text-dark mb-1" style="font-size: 1.05rem;">${escapeText(game.title)}</h5>
                <p class="small text-muted mb-3 flex-grow-1" style="line-height: 1.4;">${game.description}</p>
                <div class="pt-2 border-top">
                    <button class="btn btn-outline-primary w-100 rounded-3 btn-play-session-game fw-bold" data-session="${game.session}">
                        <i class="bi bi-controller me-1 text-success"></i> Jugar Reto de Sesión ${game.session}
                    </button>
                </div>
            </div>
        </div>
    `).join('');

    grid.innerHTML = sessionCards;

    grid.querySelectorAll('.btn-play-session-game').forEach(button => {
        button.addEventListener('click', () => {
            const sessionNum = parseInt(button.dataset.session);
            playSessionGame(sessionNum);
        });
    });
}

function playSessionGame(sessionNum) {
    const game = GRADE_4_SESSION_GAMES.find(g => g.session === sessionNum);
    const area = document.getElementById('evaluation-play-area');
    if (!game || !area) return;

    area.scrollIntoView({ behavior: 'smooth', block: 'start' });

    area.innerHTML = `
        <div class="card border-primary border-2 shadow-lg rounded-4 p-4 bg-white" style="animation: fadeIn 0.3s ease;">
            <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-3">
                <div class="d-flex align-items-center gap-2">
                    <div class="avatar bg-primary text-white rounded-circle p-2 d-flex align-items-center justify-content-center" style="width: 44px; height: 44px;">
                        <i class="bi ${game.icon} fs-4"></i>
                    </div>
                    <div>
                        <h5 class="fw-bold mb-0 text-primary">${game.gameName}</h5>
                        <small class="text-muted"><i class="bi bi-award-fill text-warning"></i> 4° Primaria · ${game.title}</small>
                    </div>
                </div>
                <button class="btn-close" onclick="document.getElementById('evaluation-play-area').innerHTML=''"></button>
            </div>

            <div class="mb-4">
                <h6 class="fw-bold text-dark fs-5 mb-3">
                    <i class="bi bi-question-circle-fill text-primary me-2"></i> ${game.question}
                </h6>
                <div class="d-grid gap-2" id="game-options-container">
                    ${game.options.map((opt, idx) => `
                        <button class="btn btn-outline-secondary text-start p-3 rounded-3 session-option-btn fw-semibold" data-val="${opt}">
                            <span class="badge bg-light text-dark border me-2">${String.fromCharCode(65 + idx)}</span> ${escapeText(opt)}
                        </button>
                    `).join('')}
                </div>
            </div>

            <div id="game-feedback-box" class="mb-3" hidden></div>

            <div class="d-flex justify-content-between align-items-center">
                <button id="btn-submit-session-game" class="btn btn-success px-4 py-2 rounded-3 fw-bold shadow-sm" disabled>
                    <i class="bi bi-check-circle-fill me-1"></i> Comprobar Respuesta
                </button>
                <small class="text-muted"><i class="bi bi-star-fill text-warning me-1"></i> Gana 100% de puntaje al responder correctamente</small>
            </div>
        </div>
    `;

    let selectedAnswer = null;
    const optionBtns = area.querySelectorAll('.session-option-btn');
    const submitBtn = document.getElementById('btn-submit-session-game');
    const feedbackBox = document.getElementById('game-feedback-box');

    optionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            optionBtns.forEach(b => {
                b.classList.remove('btn-primary', 'text-white');
                b.classList.add('btn-outline-secondary');
            });
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-primary', 'text-white');
            selectedAnswer = btn.dataset.val;
            submitBtn.disabled = false;
        });
    });

    submitBtn.addEventListener('click', async () => {
        if (!selectedAnswer) return;
        const isCorrect = (selectedAnswer === game.correct);
        const score = isCorrect ? 100 : 40;

        feedbackBox.hidden = false;
        if (isCorrect) {
            feedbackBox.innerHTML = `
                <div class="alert alert-success d-flex align-items-center gap-3 rounded-3 shadow-sm mb-0">
                    <i class="bi bi-check-circle-fill fs-2 text-success"></i>
                    <div>
                        <strong class="d-block fs-5">¡Puntaje Perfecto: 100%! 🎉</strong>
                        <span>${game.feedback}</span>
                    </div>
                </div>
            `;
        } else {
            feedbackBox.innerHTML = `
                <div class="alert alert-warning d-flex align-items-center gap-3 rounded-3 shadow-sm mb-0">
                    <i class="bi bi-exclamation-triangle-fill fs-2 text-warning"></i>
                    <div>
                        <strong class="d-block fs-5">¡Sigue intentando! Puntaje registrado: ${score}%</strong>
                        <span>La respuesta correcta era: <strong>${game.correct}</strong>. ${game.feedback}</span>
                    </div>
                </div>
            `;
        }

        submitBtn.disabled = true;

        try {
            await fetch(`/student/api/topics/1/activity`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    answers: { '0': selectedAnswer },
                    activity_type: 'juegos',
                    score: score
                })
            });
            loadProgress();
            loadRecommendations();
        } catch (e) {
            console.log('Juego registrado:', score);
        }
    });
}

async function renderSessionEvaluation(topicId, targetId = 'evaluation-container-box') {
    if (evaluationTimer) clearInterval(evaluationTimer);
    return window.StudentAssessmentRunner.load(topicId, targetId);
}

function roundScore(val) {
    return Math.round(val);
}

async function loadRecommendations() {
    const box = document.getElementById('recommendations-dynamic-list');
    if (box) {
        try {
            const res = await fetch('/student/api/recommendations');
            const data = await res.json();
            if (data.success && data.recommendations && data.recommendations.length > 0) {
                box.innerHTML = data.recommendations.slice(0, 4).map((rec, index) => renderRecommendationCard(rec, index)).join('');
            }
        } catch (e) {
            console.log('Error al cargar recomendaciones:', e);
        }
    }
    await loadReinforcementRecommendations();
}

async function loadReinforcementRecommendations() {
    const container = document.getElementById('reinforcement-recommendations-list');
    if (!container) return;
    container.innerHTML = '<span class="small text-muted">Cargando recomendaciones...</span>';
    try {
        const response = await fetch('/student/api/reinforcement-games/recommendations');
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'No se pudieron cargar los juegos recomendados.');
        }
        const games = data.recommendations || [];
        if (!games.length) {
            container.innerHTML = '<span class="small text-muted">Cuando una evaluación detecte un tema para reforzar, aquí aparecerán juegos relacionados.</span>';
            return;
        }
        container.innerHTML = games.map(game => `
            <button type="button" class="btn btn-sm btn-outline-success rounded-pill btn-launch-recommended-game" data-game-id="${escapeText(game.id)}">
                <i class="bi bi-play-circle-fill me-1"></i>${escapeText(game.title)} · ${escapeText(game.topic_title)}
            </button>
        `).join('');
        container.querySelectorAll('.btn-launch-recommended-game').forEach(button => {
            button.addEventListener('click', () => {
                const gameId = Number(button.dataset.gameId);
                document.querySelector('[data-section="juegos"]')?.click();
                window.setTimeout(() => openReinforcementGame(gameId), 250);
            });
        });
    } catch (error) {
        container.innerHTML = `<span class="small text-danger">${escapeText(error.message || 'No se pudieron cargar los juegos recomendados.')}</span>`;
    }
}

function renderRecommendationCard(rec, index) {
    const title = String(rec.title || 'Recomendación');
    const category = title.toLowerCase().includes('apoyo') ? 'refuerzo' : title.toLowerCase().includes('evaluac') ? 'tareas' : 'practica';
    const label = category === 'refuerzo' ? 'Refuerzo' : category === 'tareas' ? 'Tarea' : 'Práctica';
    return `<div class="recommendation-card recommendation-card-${index % 3}" data-recommendation-category="${category}">
        <div class="recommendation-art"><i class="bi bi-lightbulb-fill"></i></div>
        <div class="recommendation-content"><span class="recommendation-kicker">${label}</span><h6>${title}</h6><p>${rec.summary || ''}</p><span class="recommendation-detail"><i class="bi bi-check-circle me-1"></i>Actividad adaptada a tu progreso</span></div>
        <div class="recommendation-meta"><span><i class="bi bi-clock"></i> 20 min</span><span><i class="bi bi-bar-chart"></i> Nivel medio</span><button type="button" class="recommendation-cta" data-target-section="${category === 'tareas' ? 'evaluaciones' : 'material'}">Ver detalles <i class="bi bi-chevron-right"></i></button></div>
    </div>`;
}

function showRecommendationDetails(card, targetSection) {
    const modalElement = document.getElementById('recommendationDetailsModal');
    if (!card || !modalElement || !window.bootstrap) return;
    const category = card.querySelector('.recommendation-kicker')?.textContent || 'Ruta personalizada';
    const title = card.querySelector('h6')?.textContent || 'Recomendación';
    const summary = card.querySelector('p')?.textContent || 'Continúa practicando para avanzar en tu aprendizaje.';
    document.getElementById('recommendation-detail-category').textContent = category;
    document.getElementById('recommendation-detail-title').textContent = title;
    document.getElementById('recommendation-detail-summary').textContent = summary;
    const action = document.getElementById('recommendation-detail-action');
    action.textContent = targetSection === 'evaluaciones' ? 'Ir a evaluación ' : 'Ir a material ';
    action.insertAdjacentHTML('beforeend', '<i class="bi bi-arrow-right"></i>');
    action.onclick = () => {
        bootstrap.Modal.getOrCreateInstance(modalElement).hide();
        const navButton = document.querySelector(`[data-section="${targetSection}"]`);
        if (navButton && !navButton.disabled) navButton.click();
        else document.querySelector('[data-section="temas"]')?.click();
    };
    bootstrap.Modal.getOrCreateInstance(modalElement).show();
}

async function loadLesson(topicId) {
    const lesson = document.getElementById('lesson-content');
    const activity = document.getElementById('lesson-activity');
    if (!lesson || !activity) return;
    lesson.innerHTML = '<p class="text-muted">Cargando contenido educativo...</p>';
    activity.hidden = true;
    try {
        const response = await fetch(`/student/api/topics/${topicId}/lesson`);
        const data = await response.json();
        if (!data.success) throw new Error(data.error || 'No se pudo cargar la lección');
        lesson.innerHTML = '';
    } catch (error) {
        lesson.innerHTML = `<p class="text-danger">${error.message}</p>`;
    }
}

async function loadPersonalizedGame(topicId, targetId = 'lesson-activity') {
    const activity = document.getElementById(targetId);
    if (!activity) return;
    activity.hidden = false;
    activity.innerHTML = '<p class="text-muted">Cargando tu reto de entrenamiento...</p>';
    try {
        const response = await fetch(`/student/api/topics/${topicId}/personalized-game`);
        const data = await response.json();
        if (!data.success) throw new Error(data.error || 'No se pudo cargar el juego');
        const game = data.game;
        const pairs = game.pares || [];
        activity.innerHTML = `<div class="panel-card border border-success"><h6><i class="bi bi-stars text-success"></i> ${game.titulo}</h6><p class="text-muted">${game.instrucciones}</p>${pairs.map((pair, index) => `<div class="mb-3"><label class="form-label">${index + 1}. ${pair.termino}</label><select class="form-select personalized-game-answer" data-index="${index}"><option value="">Selecciona una definición</option>${pairs.map(option => `<option value="${option.definicion}">${option.definicion}</option>`).join('')}</select></div>`).join('')}<button class="btn btn-success" id="btn-check-personalized-game">Verificar reto</button><div id="personalized-game-result" class="mt-3"></div></div>`;
        document.getElementById('btn-check-personalized-game').addEventListener('click', () => {
            let correct = 0;
            activity.querySelectorAll('.personalized-game-answer').forEach(select => { const expected = pairs[Number(select.dataset.index)].definicion; const isCorrect = select.value === expected; select.classList.toggle('is-valid', isCorrect); select.classList.toggle('is-invalid', !isCorrect); if (isCorrect) correct += 1; });
            document.getElementById('personalized-game-result').innerHTML = `<div class="alert alert-${correct === pairs.length ? 'success' : 'warning'}">Obtuviste ${correct} de ${pairs.length} correctas.</div>`;
        });
    } catch (error) {
        activity.innerHTML = `<p class="text-danger">${error.message}</p>`;
    }
}

function getOpenedMaterialsSession() {
    try {
        const value = sessionStorage.getItem('opened-materials');
        return value ? JSON.parse(value) : [];
    } catch (error) {
        return [];
    }
}

function setOpenedMaterialsSession(ids) {
    sessionStorage.setItem('opened-materials', JSON.stringify(ids));
}

async function loadMaterials(topicId = null) {
    const container = document.getElementById('materials-container');
    if (!container) return;
    if (!topicId) topicId = selectedTopicId;
    if (!topicId) return;
    container.innerHTML = '<p class="text-muted">Cargando materiales...</p>';
    const response = await fetch(`/student/api/topics/${topicId}/materials`);
    const data = await response.json();
    const materials = data.materials || [];
    const items = data.items || {};
    const hasContent = materials.length || (items.activities || []).length || (items.games || []).length || (items.evaluations || []).length;
    const openedMaterials = new Set(getOpenedMaterialsSession().map(String));
    
    if (!data.success || !hasContent) {
        container.innerHTML = '<p class="text-muted">No hay materiales de archivo para este tema.</p>';
        return;
    }

    const materialHtml = materials.map(material => {
        const materialId = String(material.id);
        const isReviewed = String(material.reviewed) === 'true' || material.reviewed === true || material.reviewed === 1 || material.reviewed === '1' || openedMaterials.has(materialId);
        const instructionText = (material.description || '').trim() || 'Entrega tu trabajo según la indicación del profesor.';
        return `<article class="student-resource-card ${isReviewed ? 'reviewed' : ''} ${material.source === 'presentation' ? 'student-resource-file' : ''}" data-material-id="${material.id}" style="${isReviewed ? 'background:#ebfff3;border-color:#7ad8a6;box-shadow: inset 0 0 0 1px rgba(40,167,69,0.16);' : ''}">
            <div class="d-flex justify-content-between gap-3"><div class="flex-grow-1"><strong><i class="bi ${material.source === 'presentation' ? 'bi-file-earmark-slides' : 'bi-book-half'}"></i> ${material.title}</strong>
                <div class="mt-2 p-2 rounded-3 border border-success-subtle bg-success-subtle text-dark" style="background:#eafaf1;border:1px solid #c8eed8;">
                    <div class="fw-bold small text-success mb-1"><i class="bi bi-send-check-fill me-1"></i>Entrega:</div>
                    <div class="small mb-0">${truncateText(instructionText, 260)}</div>
                </div>
            </div>
            <span class="badge ${isReviewed ? 'bg-success' : 'bg-secondary'}" style="${isReviewed ? 'background:#28a745;color:#fff;' : ''}">${isReviewed ? 'Abierto' : material.material_type}</span></div>
            ${material.content ? `<p class="mt-2 mb-2">${material.content}</p>` : ''}
            ${material.resource_url ? `<a class="btn btn-sm ${isReviewed ? 'btn-success' : 'btn-outline-primary'} open-material-link" href="${material.resource_url}" target="_blank" rel="noopener" data-material-id="${material.id}" data-material-source="${material.source || 'material'}">${isReviewed ? 'Material abierto' : 'Abrir material'}</a>` : ''}
            ${material.source === 'material' && !isReviewed ? `<button class="btn btn-sm btn-success mark-material-reviewed" data-material-id="${material.id}">Marcar como revisado</button>` : ''}
        </article>`;
    }).join('');

    const activities = items.activities || [];
    const activitiesHtml = activities.length ? `
        <section class="student-resource-card mt-3" id="published-activities-${topicId}">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <strong><i class="bi bi-pencil-square me-1"></i> Actividades de la sesión</strong>
                <span class="badge bg-primary">${activities.length}</span>
            </div>
            ${activities.map((item, index) => `
                <div class="mb-3">
                    <label class="form-label fw-semibold">${index + 1}. ${item.question || item.title || 'Actividad'}</label>
                    ${Array.isArray(item.options) && item.options.length
                        ? `<select class="form-select published-activity-answer" data-index="${index}"><option value="">Selecciona una respuesta</option>${item.options.map(option => `<option value="${escapeText(option)}">${option}</option>`).join('')}</select>`
                        : `<input class="form-control published-activity-answer" data-index="${index}" placeholder="Escribe tu respuesta">`}
                </div>
            `).join('')}
            <button type="button" class="btn btn-success" id="submit-published-activities-${topicId}">
                <i class="bi bi-send-check me-1"></i> Enviar actividades
            </button>
            <div class="mt-3" id="published-activities-result-${topicId}"></div>
        </section>` : '';

    container.innerHTML = (materialHtml || '<p class="text-muted">No hay materiales de archivo para este tema.</p>') + activitiesHtml;
    container.querySelectorAll('.mark-material-reviewed').forEach(button => {
        button.addEventListener('click', async () => {
            const sourceQuery = button.dataset.materialSource === 'presentation' ? '?source=presentation' : '';
            await fetch(`/student/api/materials/${button.dataset.materialId}/reviewed${sourceQuery}`, {method: 'POST'});
            loadMaterials(topicId);
        });
    });
    container.querySelectorAll('.open-material-link').forEach(link => {
        link.addEventListener('click', async (event) => {
            const materialId = link.dataset.materialId;
            if (!materialId) return;
            event.preventDefault();

            const openedMaterials = getOpenedMaterialsSession();
            const materialIds = openedMaterials.map(String);
            if (!materialIds.includes(String(materialId))) {
                materialIds.push(String(materialId));
                setOpenedMaterialsSession(materialIds);
            }

            const card = link.closest('.student-resource-card');
            if (card) {
                card.classList.add('reviewed');
                card.style.background = '#ebfff3';
                card.style.borderColor = '#7ad8a6';
                card.style.boxShadow = 'inset 0 0 0 1px rgba(40,167,69,0.16)';
                const badge = card.querySelector('.badge');
                if (badge) {
                    badge.className = 'badge bg-success';
                    badge.style.background = '#28a745';
                    badge.style.color = '#fff';
                    badge.textContent = 'Abierto';
                }
            }
            link.classList.remove('btn-outline-primary');
            link.classList.add('btn-success');
            link.textContent = 'Material abierto';
            const sourceQuery = link.dataset.materialSource === 'presentation' ? '?source=presentation' : '';
            await fetch(`/student/api/materials/${materialId}/reviewed${sourceQuery}`, {method: 'POST'});
            window.open(link.href, '_blank', 'noopener,noreferrer');
            loadMaterials(topicId);
        });
    });

    if (activities.length) {
        const activitySection = document.getElementById(`published-activities-${topicId}`);
        const submitButton = document.getElementById(`submit-published-activities-${topicId}`);
        const result = document.getElementById(`published-activities-result-${topicId}`);
        submitButton?.addEventListener('click', async () => {
            const answers = {};
            activitySection.querySelectorAll('.published-activity-answer').forEach(input => {
                answers[input.dataset.index] = input.value;
            });
            submitButton.disabled = true;
            try {
                const response = await fetch(`/student/api/topics/${topicId}/activity`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({answers, activity_type: 'actividades'}),
                });
                const data = await response.json();
                if (!response.ok || !data.success) throw new Error(data.error || 'No se pudieron enviar las actividades.');
                result.innerHTML = `<div class="alert alert-success mb-0">Puntaje: <strong>${data.result.score}%</strong><br>${data.result.feedback}</div>`;
            } catch (error) {
                result.innerHTML = `<div class="alert alert-danger mb-0">${error.message}</div>`;
            } finally {
                submitButton.disabled = false;
            }
        });
    }
}

function renderActivity(topicId, activities) {
    const activity = document.getElementById('lesson-activity');
    activity.hidden = false;
    activity.innerHTML = `<h6>Actividad práctica</h6>${activities.map((item, index) => `<div class="mb-3"><label class="form-label">${index + 1}. ${item.question}</label>${item.options ? `<select class="form-select activity-answer" data-index="${index}"><option value="">Selecciona una respuesta</option>${item.options.map(option => `<option value="${escapeText(option)}">${option}</option>`).join('')}</select>` : `<input class="form-control activity-answer" data-index="${index}" placeholder="Escribe tu respuesta">`}</div>`).join('')}<button class="btn btn-success" id="btn-submit-activity">Enviar respuestas</button><div id="activity-result" class="mt-3"></div>`;
    document.getElementById('btn-submit-activity').addEventListener('click', async () => {
        const answers = {};
        document.querySelectorAll('.activity-answer').forEach(input => { answers[input.dataset.index] = input.value; });
        const response = await fetch(`/student/api/topics/${topicId}/activity`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({answers}) });
        const data = await response.json();
        if (data.success) {
            document.getElementById('activity-result').innerHTML = `<div class="alert alert-success">Puntaje: <strong>${data.result.score}%</strong><br>${data.result.feedback}</div>`;
            loadProgress();
            loadRecommendations();
        }
    });
}

async function loadProgress() {
    const response = await fetch('/student/api/progress');
    const data = await response.json();
    if (!data.success) return;
    const progress = data.progress;
    const history = document.getElementById('progress-history');
    if (history) history.innerHTML = `<p>Actividades realizadas: <strong>${progress.activities}</strong></p><p>Evaluaciones realizadas: <strong>${progress.evaluations}</strong></p><p>Juegos realizados: <strong>${progress.games}</strong></p><p>Mejor puntaje: <strong>${progress.best_score}%</strong></p>`;
}

async function openOllamaGame(gameId) {
    const area = document.getElementById('evaluation-play-area');
    if (!area) return;
    area.innerHTML = '<div class="alert alert-info">Cargando juego generado con IA...</div>';
    try {
        const response = await fetch(`/ai/juego/${gameId}/json`);
        const data = await response.json();
        if (!data.success || !data.juego) {
            area.innerHTML = '<div class="alert alert-danger">No se pudo cargar el juego de IA.</div>';
            return;
        }
        const juego = data.juego;
        const niveles = juego.niveles?.length ? juego.niveles : [{nivel: 1, tipo: 'relacionar', titulo: 'Une las parejas', pares: juego.pares || []}];
        area.innerHTML = `<div class="panel-card border border-success"><div class="d-flex justify-content-between align-items-center mb-3"><div><h5 class="mb-1"><i class="bi bi-stars text-success"></i> ${juego.titulo}</h5><p class="text-muted mb-0">${juego.instrucciones}</p></div><button type="button" class="btn btn-outline-primary btn-sm" id="btn-back-to-materials"><i class="bi bi-arrow-left me-1"></i> Volver a Mis materiales</button></div><div class="d-flex gap-2 flex-wrap mb-3" id="ollama-levels"></div><div id="ollama-level-content"></div></div>`;
        document.getElementById('btn-back-to-materials')?.addEventListener('click', () => {
            area.innerHTML = '';
            switchToStudentSection('material');
        });
        const levelButtons = document.getElementById('ollama-levels');
        niveles.forEach((nivel, index) => {
            const button = document.createElement('button');
            button.className = `btn ${index === 0 ? 'btn-success' : 'btn-outline-success'} level-button`;
            button.textContent = `Nivel ${index + 1}: ${nivel.titulo}`;
            button.addEventListener('click', () => {
                levelButtons.querySelectorAll('button').forEach(item => item.className = 'btn btn-outline-success level-button');
                button.className = 'btn btn-success level-button';
                renderOllamaLevel(nivel);
            });
            levelButtons.appendChild(button);
        });
        renderOllamaLevel(niveles[0]);
        area.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        area.innerHTML = `<div class="alert alert-danger">Error al cargar el juego: ${error.message}</div>`;
    }
}

function renderOllamaLevel(level) {
    const content = document.getElementById('ollama-level-content');
    if (!content) return;
    if (level.tipo === 'opciones') {
        content.innerHTML = `<div class="d-grid gap-3">${(level.preguntas || []).map((item, index) => `<div><strong>${index + 1}. ${item.pregunta || item.question}</strong><div class="d-grid gap-2 mt-2">${(item.opciones || item.options || []).map(option => `<button class="btn btn-outline-primary text-start level-option" data-answer="${option}" data-correct="${item.respuesta || item.answer}">${option}</button>`).join('')}</div></div>`).join('')}</div><div id="ollama-level-feedback" class="mt-3"></div>`;
        content.querySelectorAll('.level-option').forEach(button => button.addEventListener('click', () => {
            const correct = button.dataset.answer === button.dataset.correct;
            button.classList.remove('btn-outline-primary');
            button.classList.add(correct ? 'btn-success' : 'btn-danger');
            document.getElementById('ollama-level-feedback').innerHTML = `<div class="alert alert-${correct ? 'success' : 'warning'} mb-0">${correct ? '¡Muy bien! Respuesta correcta.' : 'Revisa la explicación y vuelve a intentarlo.'}</div>`;
        }));
        return;
    }
    if (level.tipo === 'ordenar') {
        const steps = (level.pasos || []).slice().sort(() => Math.random() - 0.5);
        content.innerHTML = `<p class="text-muted">Pulsa los pasos en el orden correcto.</p><div class="d-grid gap-2">${steps.map(step => `<button class="btn btn-outline-primary text-start order-step" data-step="${step}">${step}</button>`).join('')}</div><div id="ollama-level-feedback" class="mt-3"></div>`;
        const expected = level.pasos || [];
        let next = 0;
        content.querySelectorAll('.order-step').forEach(button => button.addEventListener('click', () => {
            if (button.dataset.step === expected[next]) { button.className = 'btn btn-success text-start order-step'; button.disabled = true; next += 1; }
            else { button.className = 'btn btn-danger text-start order-step'; }
            if (next === expected.length) document.getElementById('ollama-level-feedback').innerHTML = '<div class="alert alert-success mb-0">¡Orden correcto! Nivel completado.</div>';
        }));
        return;
    }
    const pairs = (level.pares || []).slice().sort(() => Math.random() - 0.5);
    content.innerHTML = `<div class="row g-3"><div class="col-md-6"><small class="text-muted d-block mb-2">Términos</small><div id="ollama-drag-list" class="d-grid gap-2"></div></div><div class="col-md-6"><small class="text-muted d-block mb-2">Definiciones</small><div id="ollama-drop-list" class="d-grid gap-2"></div></div></div><button id="btn-check-ollama-game" class="btn btn-success mt-3">Verificar respuestas</button><div id="ollama-game-feedback" class="mt-2"></div>`;
    pairs.forEach(par => {
        const drag = document.createElement('div');
        drag.className = 'p-3 rounded bg-primary text-white fw-semibold'; drag.draggable = true; drag.textContent = par.termino;
        drag.addEventListener('dragstart', event => event.dataTransfer.setData('text/plain', par.termino));
        document.getElementById('ollama-drag-list').appendChild(drag);
        const drop = document.createElement('div');
        drop.className = 'p-3 rounded border border-2 border-dashed bg-light ollama-dropzone'; drop.dataset.correcta = par.definicion; drop.innerHTML = `<span>${par.definicion}</span>`;
        drop.addEventListener('dragover', event => { event.preventDefault(); drop.classList.add('border-success'); });
        drop.addEventListener('drop', event => { event.preventDefault(); drop.classList.remove('border-success'); drop.textContent = event.dataTransfer.getData('text/plain'); });
        document.getElementById('ollama-drop-list').appendChild(drop);
    });
    document.getElementById('btn-check-ollama-game').addEventListener('click', () => {
        let correctas = 0;
        document.querySelectorAll('.ollama-dropzone').forEach(zone => { const pair = pairs.find(item => item.termino === zone.textContent.trim()); const correct = pair && pair.definicion === zone.dataset.correcta; zone.classList.add(correct ? 'bg-success-subtle' : 'bg-danger-subtle'); if (correct) correctas += 1; });
        document.getElementById('ollama-game-feedback').innerHTML = `<div class="alert alert-${correctas === pairs.length ? 'success' : 'warning'} mb-0">Tuviste ${correctas} de ${pairs.length} correctas.</div>`;
    });
}

function openGame(game, topicId) {
    if (!topicId) return;
    const area = document.getElementById('evaluation-play-area');
    if (!area) return;
    area.innerHTML = `<div class="student-game-challenge"><h6><i class="bi bi-controller"></i> ${game}</h6><p>Escribe tu respuesta para completar el reto del tema.</p><input id="game-answer" class="form-control mb-2" placeholder="Mi respuesta"><button id="submit-game-answer" class="btn btn-success">Comprobar respuesta</button><div id="game-result" class="mt-2"></div></div>`;
    document.getElementById('submit-game-answer').addEventListener('click', async () => {
        const answer = document.getElementById('game-answer').value.trim();
        if (!answer) return;
        const response = await fetch(`/student/api/topics/${topicId}/activity`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({answers: {'0': answer}, activity_type: 'juegos'}) });
        const data = await response.json();
        if (data.success) {
            document.getElementById('game-result').innerHTML = `<div class="alert alert-success">Reto registrado. Puntaje: <strong>${data.result.score}%</strong></div>`;
            loadProgress();
            loadRecommendations();
        }
    });
}

async function loadEvaluation(topicId) {
    if (!topicId) return;
    renderSessionEvaluation(topicId);
}

// ==========================================
// GOAL 2 — Sistema de Materiales Educativos
// ==========================================

function loadMaterials(topicId) {
    if (!topicId) return;
    fetch(`/student/api/topics/${topicId}/materials`)
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('materials-container');
            if (!container) return;
            const items = data.materials || [];
            if (!items.length) {
                container.innerHTML = '<p class="text-muted small">No hay materiales adicionales para este tema.</p>';
                return;
            }
            container.innerHTML = items.map(m => `
                <div class="border rounded p-2 mb-2 bg-light d-flex justify-content-between align-items-center">
                    <div>
                        <strong class="d-block text-dark small">📖 ${m.title}</strong>
                        <small class="text-muted">${(m.content || m.description || '').substring(0, 80)}...</small>
                    </div>
                    <div class="d-flex gap-1">
                        <button class="btn btn-outline-primary btn-sm btn-leer-material" data-material-id="${m.id}" data-material-source="${m.source || 'material'}">Leer</button>
                        <button class="btn btn-primary btn-sm btn-practicar-material" data-material-id="${m.id}" data-material-source="${m.source || 'material'}">Practicar</button>
                    </div>
                </div>
            `).join('');
        })
        .catch(err => console.warn('Error al cargar materiales del tema:', err));
}

async function markMaterialAsReviewed(materialId, materialSource = 'material') {
    if (!materialId) return false;
    try {
        const sourceQuery = materialSource === 'presentation' ? '?source=presentation' : '';
        const resp = await fetch(`/student/api/materials/${materialId}/reviewed${sourceQuery}`, { method: 'POST' });
        const result = await resp.json();
        if (result && result.success) {
            const badge = document.getElementById(`badge-status-${materialId}`);
            if (badge) {
                badge.className = 'badge bg-success-subtle text-success rounded-pill small';
                badge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Leído';
            }

            const card = document.querySelector(`.material-card[data-material-id="${materialId}"]`);
            if (card) {
                card.classList.add('material-card--seen');
            }
            return true;
        }
    } catch (err) {
        console.warn('No se pudo actualizar el estado del material:', err);
    }
    return false;
}

function updateMaterialCardState(materialId, reviewed) {
    const badge = document.getElementById(`badge-status-${materialId}`);
    const card = document.querySelector(`.material-card[data-material-id="${materialId}"]`);

    if (badge) {
        if (reviewed) {
            badge.className = 'badge bg-success-subtle text-success rounded-pill small';
            badge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Leído';
        } else {
            badge.className = 'badge bg-warning-subtle text-warning-emphasis rounded-pill small';
            badge.innerHTML = '<i class="bi bi-book me-1"></i> Pendiente';
        }
    }

    if (card) {
        card.classList.toggle('material-card--seen', Boolean(reviewed));
    }
}

let currentReadMaterialId = null;

async function openReadMaterialModal(materialId, materialSource = 'material') {
    const modalEl = document.getElementById('modalReadMaterial');
    if (!modalEl) return;
    const titleEl = document.getElementById('modalReadMaterialTitle');
    const topicEl = document.getElementById('read-material-topic');
    const bodyEl = document.getElementById('read-material-body');
    const btnMark = document.getElementById('btn-modal-mark-reviewed');
    const btnPractice = document.getElementById('btn-modal-start-practice');

    currentReadMaterialId = materialId;
    bodyEl.textContent = 'Cargando contenido...';
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    if (btnMark) {
        btnMark.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Marcar como leído';
        btnMark.className = 'btn btn-outline-success btn-sm';
        btnMark.disabled = false;
    }

    try {
        const sourceQuery = materialSource === 'presentation' ? '?source=presentation' : '';
        const resp = await fetch(`/student/api/materials/${materialId}${sourceQuery}`);
        const data = await resp.json();
        if (!data.success || !data.material) {
            bodyEl.textContent = 'No se pudo cargar el material.';
            return;
        }
        const mat = data.material;

        titleEl.textContent = `📖 ${mat.title}`;
        topicEl.textContent = mat.topic_title ? `Tema: ${mat.topic_title}` : 'Clase';
        bodyEl.replaceChildren();
        const resourceUrl = mat.resource_url || '';
        const fileExtension = (mat.file_extension || resourceUrl.split('?')[0].split('.').pop() || '').toLowerCase();

        if (resourceUrl && fileExtension === 'pdf') {
            const viewer = document.createElement('iframe');
            viewer.src = resourceUrl;
            viewer.title = `Lectura: ${mat.title || 'material'}`;
            viewer.style.width = '100%';
            viewer.style.height = '60vh';
            viewer.style.border = '0';
            bodyEl.appendChild(viewer);
        } else if (resourceUrl && ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(fileExtension)) {
            const image = document.createElement('img');
            image.src = resourceUrl;
            image.alt = mat.title || 'Material de clase';
            image.style.maxWidth = '100%';
            image.style.height = 'auto';
            bodyEl.appendChild(image);
        } else if (resourceUrl && ['mp4', 'webm', 'ogg'].includes(fileExtension)) {
            const video = document.createElement('video');
            video.src = resourceUrl;
            video.controls = true;
            video.style.width = '100%';
            bodyEl.appendChild(video);
        } else if (mat.content) {
            bodyEl.textContent = mat.content;
        } else if (resourceUrl) {
            bodyEl.textContent = mat.read_error || 'Este archivo no se puede previsualizar. Puedes abrirlo aquí:';
            const link = document.createElement('a');
            link.href = resourceUrl;
            link.target = '_blank';
            link.rel = 'noopener';
            link.className = 'btn btn-outline-primary btn-sm mt-2';
            link.textContent = 'Abrir material';
            bodyEl.appendChild(document.createElement('br'));
            bodyEl.appendChild(link);
        } else {
            bodyEl.textContent = mat.description || 'Sin contenido disponible.';
        }

        if (mat.reviewed) {
            updateMaterialCardState(materialId, true);
            if (btnMark) {
                btnMark.innerHTML = '<i class="bi bi-check2-all me-1"></i> Ya leído';
                btnMark.className = 'btn btn-success btn-sm';
            }
        } else {
            updateMaterialCardState(materialId, false);
            if (btnMark) {
                btnMark.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Marcar como leído';
                btnMark.className = 'btn btn-outline-success btn-sm';
            }
        }

        if (btnMark) {
            btnMark.onclick = async () => {
                try {
                    const success = await markMaterialAsReviewed(materialId, materialSource);
                    if (success) {
                        btnMark.innerHTML = '<i class="bi bi-check2-all me-1"></i> ¡Marcado como leído!';
                        btnMark.className = 'btn btn-success btn-sm';
                    }
                } catch (err) {
                    console.error('Error al marcar leído:', err);
                }
            };
        }

        if (btnPractice) {
            btnPractice.onclick = () => {
                modal.hide();
                openPracticeArea(materialId, materialSource);
            };
        }
    } catch (e) {
        bodyEl.textContent = `Error al cargar lectura: ${e.message}`;
    }
}

async function renderPracticalActivity(topicId, container) {
    container.innerHTML = '<p class="text-muted">Cargando actividad práctica...</p>';
    try {
        const response = await fetch(`/student/api/topics/${topicId}/practical-activity`);
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'No se pudieron cargar los materiales y entregas.');
        }

        const materials = data.materials || [];
        const submissions = data.submissions || [];
        const materialsHtml = materials.length ? materials.map(material => {
            const reviewed = material.reviewed === true || material.reviewed === 1 || material.reviewed === '1';
            const source = material.source || 'material';
            const description = (material.description || '').trim() || 'El profesor no agregó una descripción para este material.';
            return `
                <article class="student-resource-card ${reviewed ? 'reviewed' : ''} mb-3">
                    <div class="d-flex justify-content-between align-items-start gap-3">
                        <div class="flex-grow-1">
                            <h6 class="fw-bold mb-2">${escapeText(material.title || 'Material de la clase')}</h6>
                            <div class="rounded-3 border bg-light p-3 small" style="white-space: pre-line">${escapeText(description)}</div>
                        </div>
                        <span class="badge ${reviewed ? 'bg-success' : 'bg-warning text-dark'}" data-practical-read-status="${source}-${material.id}">
                            ${reviewed ? 'Leído' : 'No leído'}
                        </span>
                    </div>
                    <div class="mt-3">
                        ${material.resource_url
                            ? `<button type="button" class="btn btn-outline-primary btn-sm btn-download-practical-material" data-material-id="${material.id}" data-material-source="${source}" data-resource-url="${escapeText(material.resource_url)}" data-file-name="${escapeText(material.file_name || material.title || 'material')}"><i class="bi bi-download me-1"></i> Descargar material</button>`
                            : `<button type="button" class="btn btn-outline-primary btn-sm btn-open-practical-material" data-material-id="${material.id}" data-material-source="${source}"><i class="bi bi-book me-1"></i> Leer material</button>`}
                    </div>
                </article>`;
        }).join('') : '<p class="text-muted">El profesor todavía no publicó materiales para esta actividad.</p>';

        const submissionsHtml = submissions.length ? submissions.map(submission => {
            const reviewed = submission.teacher_score !== null && submission.teacher_score !== undefined;
            return `<article class="border rounded-3 p-3 mb-2 bg-white">
                <div class="d-flex justify-content-between gap-2">
                    <strong>${escapeText(submission.title || submission.file_name || 'Trabajo')}</strong>
                    <span class="badge ${reviewed ? 'bg-success' : 'bg-warning text-dark'}">${reviewed ? 'Revisado' : escapeText(submission.status || 'Pendiente')}</span>
                </div>
                <div class="small text-muted mt-1">${escapeText(submission.file_name || '')}${submission.submitted_at ? ` · Enviado: ${escapeText(submission.submitted_at)}` : ''}</div>
                ${reviewed ? `<div class="mt-2"><strong>Nota: ${escapeText(submission.teacher_score)}</strong>${submission.teacher_feedback ? `<p class="mb-0 mt-1">${escapeText(submission.teacher_feedback)}</p>` : ''}</div>` : '<p class="small text-muted mb-0 mt-2">El profesor aún no revisa esta entrega.</p>'}
            </article>`;
        }).join('') : '<p class="small text-muted mb-0">Aún no has enviado un trabajo para esta clase.</p>';

        container.innerHTML = `
            <section class="student-resource-card mb-4">
                <div class="d-flex align-items-center gap-2 mb-3">
                    <i class="bi bi-file-earmark-text text-primary fs-5"></i>
                    <h5 class="fw-bold mb-0">Material e indicaciones del profesor</h5>
                </div>
                ${materialsHtml}
            </section>
            <section class="student-resource-card">
                <div class="d-flex align-items-center gap-2 mb-3">
                    <i class="bi bi-cloud-arrow-up text-primary fs-5"></i>
                    <h5 class="fw-bold mb-0">Presentación de tu trabajo</h5>
                </div>
                <form class="student-submission-form" data-topic-id="${topicId}">
                    <label class="form-label small fw-semibold" for="submission-title-${topicId}">Título del trabajo</label>
                    <input class="form-control mb-2" id="submission-title-${topicId}" name="title" maxlength="255" placeholder="Ej. Actividad de la sesión">
                    <label class="form-label small fw-semibold" for="submission-file-${topicId}">Subir archivo (máximo 20 MB)</label>
                    <input class="form-control mb-3" id="submission-file-${topicId}" name="file" type="file" accept=".pdf,.doc,.docx,.odt,.ppt,.pptx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg,.mp4,.mov,.webm,.mp3,.zip" required>
                    <button type="submit" class="btn btn-primary btn-sm"><i class="bi bi-send me-1"></i> Enviar al profesor</button>
                    <div class="student-submission-message small mt-2" role="status"></div>
                </form>
                <div class="mt-4">
                    <h6 class="fw-bold">Mis entregas y calificaciones</h6>
                    <div class="student-submission-history">${submissionsHtml}</div>
                </div>
            </section>`;

        container.querySelectorAll('.btn-download-practical-material').forEach(button => {
            button.addEventListener('click', () => downloadPracticalMaterial(button));
        });
        container.querySelectorAll('.btn-open-practical-material').forEach(button => {
            button.addEventListener('click', () => openReadMaterialModal(
                Number(button.dataset.materialId),
                button.dataset.materialSource || 'material'
            ));
        });
        container.querySelector('.student-submission-form')?.addEventListener('submit', event => {
            submitStudentWork(event, topicId, container);
        });
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger mb-0">${escapeText(error.message || 'No se pudo cargar la actividad.')}</div>`;
    }
}

async function downloadPracticalMaterial(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Preparando...';
    try {
        const link = document.createElement('a');
        link.href = button.dataset.resourceUrl;
        link.download = button.dataset.fileName || 'material';
        document.body.appendChild(link);
        link.click();
        link.remove();

        const materialId = Number(button.dataset.materialId);
        const source = button.dataset.materialSource || 'material';
        if (!await markMaterialAsReviewed(materialId, source)) {
            throw new Error('El archivo se descargó, pero no se pudo guardar el estado de lectura.');
        }
        const status = document.querySelector(`[data-practical-read-status="${source}-${materialId}"]`);
        if (status) {
            status.className = 'badge bg-success';
            status.textContent = 'Leído';
        }
        updateMaterialCardState(materialId, true);
        button.innerHTML = '<i class="bi bi-check-circle me-1"></i> Descarga iniciada · Leído';
    } catch (error) {
        const message = button.closest('article')?.querySelector('.download-error');
        if (message) message.remove();
        const alert = document.createElement('div');
        alert.className = 'small text-danger mt-2 download-error';
        alert.textContent = error.message;
        button.after(alert);
        button.innerHTML = originalText;
    } finally {
        button.disabled = false;
    }
}

async function submitStudentWork(event, topicId, container) {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.querySelector('input[type="file"]');
    const message = form.querySelector('.student-submission-message');
    const submitButton = form.querySelector('button[type="submit"]');
    if (!fileInput?.files?.length) {
        message.textContent = 'Selecciona el archivo que deseas entregar.';
        message.className = 'student-submission-message small mt-2 text-danger';
        return;
    }
    const formData = new FormData(form);
    submitButton.disabled = true;
    message.textContent = 'Enviando trabajo...';
    message.className = 'student-submission-message small mt-2 text-muted';
    try {
        const response = await fetch(`/student/api/topics/${topicId}/submission`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'No se pudo enviar el trabajo.');
        await renderPracticalActivity(topicId, container);
        const refreshedMessage = container.querySelector('.student-submission-message');
        if (refreshedMessage) {
            refreshedMessage.textContent = 'Trabajo enviado al profesor para su revisión.';
            refreshedMessage.className = 'student-submission-message small mt-2 text-success';
        }
    } catch (error) {
        message.textContent = error.message;
        message.className = 'student-submission-message small mt-2 text-danger';
    } finally {
        if (submitButton.isConnected) submitButton.disabled = false;
    }
}

let currentPracticeQuestions = [];
let currentPracticeMaterialId = null;
let currentPracticeSource = 'material';
let currentPracticeAttemptId = null;

async function openPracticeArea(materialId, materialSource = 'material') {
    currentPracticeSource = materialSource;
    currentPracticeAttemptId = null;
    const area = document.getElementById('material-practice-area');
    const titleEl = document.getElementById('practice-material-title');
    const subtitleEl = document.getElementById('practice-material-subtitle');
    const loading = document.getElementById('practice-loading');
    const formActions = document.getElementById('practice-form-actions');
    const questionsContainer = document.getElementById('practice-questions-container');
    const feedbackArea = document.getElementById('practice-feedback-area');

    if (!area) return;

    currentPracticeMaterialId = materialId;
    area.style.display = 'block';
    area.scrollIntoView({ behavior: 'smooth', block: 'start' });

    questionsContainer.innerHTML = '';
    feedbackArea.innerHTML = '';
    loading.style.display = 'block';
    if (formActions) formActions.style.setProperty('display', 'none', 'important');

    try {
        const sourceQuery = materialSource === 'presentation' ? '?source=presentation' : '';
        const resp = await fetch(`/student/api/materials/${materialId}/practice${sourceQuery}`);
        const data = await resp.json();
        loading.style.display = 'none';

        if (!data.success) {
            questionsContainer.innerHTML = `<div class="alert alert-danger">${data.error || 'Error al obtener preguntas.'}</div>`;
            return;
        }

        titleEl.textContent = `Práctica: ${data.material_title || 'Lectura'}`;
        if (subtitleEl) {
            subtitleEl.textContent = `Tema: ${data.topic_title || 'General'} · Preguntas extraídas estrictamente del texto del docente`;
        }

        currentPracticeQuestions = data.questions || [];
        currentPracticeAttemptId = data.attempt_id;
        if (!currentPracticeQuestions.length) {
            questionsContainer.innerHTML = '<div class="alert alert-warning">No se encontraron preguntas para este material.</div>';
            return;
        }

        questionsContainer.innerHTML = currentPracticeQuestions.map((q, idx) => {
            const options = q.options || [];
            return `
                <div class="p-3 rounded-4 border bg-white shadow-xs question-card" id="q-card-${idx}">
                    <div class="d-flex align-items-start gap-2 mb-2">
                        <span class="badge bg-primary text-white rounded-pill">${idx + 1}</span>
                        <div class="fw-bold text-dark fs-6">${escapeText(q.question)}</div>
                    </div>
                    <div class="ps-4">
                        ${options.map((opt, optIdx) => `
                            <div class="form-check my-2 p-2 rounded-2 hover-bg-light">
                                <input class="form-check-input" type="radio" name="answer_${idx}" id="opt_${idx}_${optIdx}" value="${escapeText(opt)}" required>
                                <label class="form-check-label text-dark w-100" for="opt_${idx}_${optIdx}" style="cursor: pointer;">
                                    ${escapeText(opt)}
                                </label>
                            </div>
                        `).join('')}
                    </div>
                    ${q.reference_fragment ? `
                        <div class="mt-2 pt-2 border-top small text-muted">
                            <i class="bi bi-quote text-primary"></i> <em>Basado en el texto: "${q.reference_fragment}"</em>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

        if (formActions) formActions.style.setProperty('display', 'flex', 'important');

    } catch (e) {
        loading.style.display = 'none';
        questionsContainer.innerHTML = `<div class="alert alert-danger">Error de conexión: ${e.message}</div>`;
    }
}

// Manejo de eventos para Materiales Educativos
document.addEventListener('click', (e) => {
    const readBtn = e.target.closest('.btn-leer-material');
    if (readBtn) {
        e.preventDefault();
        const matId = readBtn.dataset.materialId;
        if (matId) openReadMaterialModal(matId, readBtn.dataset.materialSource || 'material');
        return;
    }
    const practiceBtn = e.target.closest('.btn-practicar-material');
    if (practiceBtn) {
        e.preventDefault();
        const matId = practiceBtn.dataset.materialId;
        if (matId) openPracticeArea(matId, practiceBtn.dataset.materialSource || 'material');
        return;
    }
    if (e.target.closest('#btn-close-practice')) {
        const area = document.getElementById('material-practice-area');
        if (area) area.style.display = 'none';
    }
});

// Envío y calificación interactiva de la práctica
document.addEventListener('submit', async (e) => {
    if (e.target && e.target.id === 'practice-quiz-form') {
        e.preventDefault();
        if (!currentPracticeMaterialId) return;

        const answers = {};
        currentPracticeQuestions.forEach((_, idx) => {
            const selected = e.target.querySelector(`input[name="answer_${idx}"]:checked`);
            if (selected) {
                answers[idx] = selected.value;
            }
        });

        const feedbackArea = document.getElementById('practice-feedback-area');
        if (feedbackArea) {
            feedbackArea.innerHTML = '<div class="alert alert-info py-2"><div class="spinner-border spinner-border-sm me-2"></div>Calificando respuestas...</div>';
        }

        try {
            const resp = await fetch(`/student/api/materials/${currentPracticeMaterialId}/practice${currentPracticeSource === 'presentation' ? '?source=presentation' : ''}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers, attempt_id: currentPracticeAttemptId })
            });
            const result = await resp.json();

            if (!result.success) {
                if (feedbackArea) feedbackArea.innerHTML = `<div class="alert alert-danger">${result.error || 'Error al calificar.'}</div>`;
                return;
            }

            // Actualizar badge en tarjeta
            const badge = document.getElementById(`badge-status-${currentPracticeMaterialId}`);
            if (badge) {
                badge.className = 'badge bg-success-subtle text-success rounded-pill small';
                badge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Leído';
            }

            const graded = result.graded_questions || [];
            graded.forEach((g, idx) => {
                const card = document.getElementById(`q-card-${idx}`);
                if (card) {
                    if (g.correct) {
                        card.style.border = '2px solid #22c55e';
                        card.style.backgroundColor = '#f0fdf4';
                    } else {
                        card.style.border = '2px solid #ef4444';
                        card.style.backgroundColor = '#fef2f2';
                    }
                }
            });

            if (feedbackArea) {
                feedbackArea.innerHTML = `
                    <div class="alert ${result.score_20 >= 12 ? 'alert-success' : 'alert-warning'} border-0 shadow-sm rounded-4 p-3">
                        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                            <div>
                                <h5 class="fw-bold mb-1">
                                    ${result.score_20 >= 12 ? '🎉 ¡Excelente trabajo!' : '💪 ¡Buen intento, sigue practicando!'}
                                </h5>
                                <span>Obtuviste <strong>${result.correct_count} de ${result.total}</strong> aciertos (${result.percentage}% · Nota: <strong>${result.score_20}/20</strong>).</span>
                            </div>
                            <span class="badge ${result.score_20 >= 12 ? 'bg-success' : 'bg-warning text-dark'} fs-6 px-3 py-2 rounded-pill shadow-xs">
                                ${result.score_20} / 20
                            </span>
                        </div>
                        <div class="mt-2 small text-muted">
                            <i class="bi bi-info-circle-fill me-1"></i> Tu lectura y práctica quedaron registradas en el sistema.
                        </div>
                    </div>
                `;
                feedbackArea.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }

            // Actualizar progreso, recomendaciones adaptativas y riesgo IA en tiempo real
            loadProgress();
            loadRecommendations();
            loadStudentRiskPrediction();
        } catch (err) {
            if (feedbackArea) feedbackArea.innerHTML = `<div class="alert alert-danger">Error al calificar: ${err.message}</div>`;
        }
    }

});

    // =========================================================================
    // GOAL: Juegos Educativos Mágicos Generados por IA con UX Infantil
    // =========================================================================
    let currentAiGamesList = [];

    async function loadAiPublishedGames(topicId = null) {
        const grid = document.getElementById('ai-published-games-grid');
        if (!grid) return;

        try {
            const resp = await fetch('/student/api/topics');
            let topics = [];
            if (resp.ok) {
                const tData = await resp.json();
                topics = tData.topics || [];
            }
            const selectedTopics = topicId ? topics.filter(topic => Number(topic.id) === Number(topicId)) : topics;
            const results = await Promise.all(selectedTopics.map(async topic => {
                const response = await fetch(`/student/api/topics/${topic.id}/ai-games`);
                if (!response.ok) throw new Error('No se pudieron cargar los juegos del tema.');
                const data = await response.json();
                return (data.games || []).map(game => ({ ...game, topic_title: topic.title }));
            }));
            const allPublishedGames = results.flat();

            currentAiGamesList = allPublishedGames;

            if (allPublishedGames.length === 0) {
                grid.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-light border text-center p-4 rounded-4 shadow-xs">
                            <div class="fs-1 mb-2">🎮✨</div>
                            <h6 class="fw-bold text-dark">Aún no hay juegos mágicos publicados</h6>
                            <p class="text-muted small mb-0">Tu profesor publicará retos interactivos generados con IA basados en las clases muy pronto.</p>
                        </div>
                    </div>
                `;
                return;
            }

            const typeMeta = {
                'multiple_choice': { icon: '🎯', badge: 'bg-primary-subtle text-primary', label: 'Opción Múltiple' },
                'true_false': { icon: '⚖️', badge: 'bg-success-subtle text-success', label: 'Verdadero o Falso' },
                'fill_blank': { icon: '✏️', badge: 'bg-warning-subtle text-warning-emphasis', label: 'Completar Espacio' },
                'matching': { icon: '🧩', badge: 'bg-info-subtle text-info-emphasis', label: 'Unir Parejas' },
                'memory': { icon: '🃏', badge: 'bg-danger-subtle text-danger-emphasis', label: 'Cartas de Memoria' },
                'ordering': { icon: '🔢', badge: 'bg-primary-subtle text-primary', label: 'Ordenar Pasos' },
                'drag_drop': { icon: '🧲', badge: 'bg-success-subtle text-success', label: 'Clasificar' },
                'challenge': { icon: '🚀', badge: 'bg-warning-subtle text-warning-emphasis', label: 'Aventura por Niveles' }
            };

            grid.innerHTML = allPublishedGames.map(game => {
                const meta = typeMeta[game.game_type] || { icon: '⭐', badge: 'bg-light text-dark', label: 'Juego IA' };
                return `
                    <div class="col-md-6 col-lg-4">
                        <div class="card h-100 border-0 shadow-sm rounded-4 p-3 bg-white border border-2 border-warning-subtle position-relative d-flex flex-column hover-shadow transition">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge ${meta.badge} rounded-pill px-3 py-1 font-weight-bold">
                                    ${meta.icon} ${meta.label}
                                </span>
                                <span class="badge bg-warning-subtle text-warning-emphasis rounded-pill fw-bold small">
                                    <i class="bi bi-star-fill text-warning me-1"></i>+10 pts
                                </span>
                            </div>
                            <h5 class="fw-bold text-dark mb-1" style="font-size: 1.1rem;">${escapeText(game.title)}</h5>
                            <small class="text-primary fw-semibold mb-2 d-block"><i class="bi bi-bookmark-check me-1"></i>${game.topic_title || 'Clase de Computación'}</small>
                            <p class="small text-muted mb-3 flex-grow-1" style="line-height: 1.4;">${game.instruction || '¡Demuestra lo que aprendiste respondiendo este divertido reto!'}</p>
                            <button class="btn btn-warning w-100 rounded-3 fw-bold py-2 shadow-xs text-dark btn-open-ai-game" data-game-id="${game.id}" style="font-size: 1rem; border-radius: 14px;">
                                <i class="bi bi-play-circle-fill me-1"></i> ¡Jugar Ahora! 🚀
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            grid.querySelectorAll('.btn-open-ai-game').forEach(btn => {
                btn.addEventListener('click', () => {
                    const gId = parseInt(btn.dataset.gameId, 10);
                    openAiGame(gId);
                });
            });

        } catch (err) {
            console.error('Error al cargar juegos mágicos de IA:', err);
            grid.innerHTML = `<div class="col-12"><div class="alert alert-danger small">No se pudieron cargar los juegos de IA: ${err.message}</div></div>`;
        }
    }

    function openAiGame(gameId) {
        const game = currentAiGamesList.find(g => g.id === gameId);
        const arena = document.getElementById('ai-game-play-arena');
        if (!game || !arena) return;

        const missionByType = {
            multiple_choice: { icon: '<i class="bi bi-bullseye"></i>', name: 'Detective de respuestas', rule: 'Elige una respuesta y descubre la pista correcta.', reward: '+10 estrellas' },
            true_false: { icon: '<i class="bi bi-search"></i>', name: 'Explorador de pistas', rule: 'Lee la pista y decide si es verdadera o falsa.', reward: '+10 estrellas' },
            fill_blank: { icon: '<i class="bi bi-pencil-fill"></i>', name: 'Constructor de frases', rule: 'Completa la idea usando una palabra de ayuda.', reward: '+10 estrellas' },
            matching: { icon: '<i class="bi bi-puzzle-fill"></i>', name: 'Conector de ideas', rule: 'Une cada idea con su pareja correcta.', reward: '+10 estrellas' },
            memory: { icon: '<i class="bi bi-suit-spade-fill"></i>', name: 'Guardián de la memoria', rule: 'Voltea dos cartas y encuentra las parejas mágicas.', reward: '+10 estrellas' },
            ordering: { icon: '<i class="bi bi-signpost-split-fill"></i>', name: 'Ordenador de aventuras', rule: 'Mueve las piezas hasta contar la historia en orden.', reward: '+10 estrellas' },
            drag_drop: { icon: '<i class="bi bi-arrows-move"></i>', name: 'Clasificador experto', rule: 'Arrastra cada tarjeta al lugar donde pertenece.', reward: '+10 estrellas' },
            challenge: { icon: '<i class="bi bi-rocket-takeoff-fill"></i>', name: 'Capitán de la misión', rule: 'Supera los tres niveles para llegar a la meta.', reward: '+10 estrellas' }
        };
        const mission = missionByType[game.game_type] || { icon: '<i class="bi bi-stars"></i>', name: 'Explorador del saber', rule: 'Completa este reto a tu ritmo.', reward: '+10 estrellas' };
        arena.style.display = 'block';
        arena.scrollIntoView({ behavior: 'smooth', block: 'start' });
        arena.innerHTML = `
            <section class="mission-screen" aria-label="Inicio de misión">
                <div class="mission-mascot" aria-hidden="true">${mission.icon}</div>
                <div>
                    <span class="mission-eyebrow"><i class="bi bi-stars"></i> Misión lista</span>
                    <h2>${escapeText(game.title)}</h2>
                    <p>¡Hola, explorador! ${escapeText(game.instruction || 'Hoy tendrás un reto corto y divertido.')}</p>
                    <div class="mission-rules" aria-label="Reglas de la misión">
                        <span class="mission-rule"><i class="bi bi-compass-fill"></i>${mission.name}</span>
                        <span class="mission-rule"><i class="bi bi-lightbulb-fill"></i>${mission.rule}</span>
                        <span class="mission-rule"><i class="bi bi-star-fill"></i>${mission.reward}</span>
                    </div>
                    <button type="button" class="mission-start-btn" id="btn-start-ai-mission"><i class="bi bi-play-fill me-1"></i> ¡Comenzar mi misión!</button>
                </div>
            </section>`;
        arena.querySelector('#btn-start-ai-mission')?.addEventListener('click', () => renderAiGameRound(gameId));
    }

    function renderAiGameRound(gameId) {
        const game = currentAiGamesList.find(g => g.id === gameId);
        const arena = document.getElementById('ai-game-play-arena');
        if (!game || !arena) return;

        arena.style.display = 'block';
        arena.scrollIntoView({ behavior: 'smooth', block: 'start' });

        const content = game.content_json || {};
        let interactionHtml = '';

        if (game.game_type === 'multiple_choice') {
            const question = content.question || 'Selecciona la respuesta correcta:';
            const options = content.options || [];
            const optButtons = options.map((opt, idx) => `
                <button class="game-choice btn-ai-mc-option" data-answer="${escapeText(opt)}">
                    <span class="choice-key">${idx + 1}</span>
                    ${escapeText(opt)}
                </button>
            `).join('');

            interactionHtml = `
                <div class="mb-4">
                    <div>
                        <span class="game-kicker">Pista de la misión</span>
                        <h3 class="game-prompt">${escapeText(question)}</h3>
                    </div>
                    <div class="d-grid gap-1" id="ai-mc-options-container">
                        ${optButtons}
                    </div>
                </div>
            `;
        } else if (game.game_type === 'true_false') {
            const statement = content.statement || content.question || '¿Esta afirmación es verdadera o falsa?';
            interactionHtml = `
                <div class="mb-4 text-center">
                    <div>
                        <span class="game-kicker">Pista secreta</span>
                        <h3 class="game-prompt">${escapeText(statement)}</h3>
                    </div>
                    <div class="row g-3 justify-content-center">
                        <div class="col-sm-6">
                            <button class="game-choice justify-content-center btn-ai-tf-option" data-answer="true">
                                <i class="bi bi-check-circle-fill me-2 fs-4"></i> ¡Verdadero! 👍
                            </button>
                        </div>
                        <div class="col-sm-6">
                            <button class="game-choice justify-content-center btn-ai-tf-option" data-answer="false">
                                <i class="bi bi-x-circle-fill me-2 fs-4"></i> Falso 👎
                            </button>
                        </div>
                    </div>
                </div>
            `;
        } else if (game.game_type === 'fill_blank') {
            const sentence = content.sentence || content.question || 'Completa la frase: ______';
            const options = content.options || [];
            const optChips = options.length > 0
                ? options.map(opt => `<button type="button" class="btn btn-outline-primary btn-sm rounded-pill fw-bold btn-fill-chip" data-word="${escapeText(opt)}">${escapeText(opt)}</button>`).join(' ')
                : '';

            interactionHtml = `
                <div class="mb-4">
                    <div class="text-center">
                        <span class="game-kicker">Completa la pista</span>
                        <h3 class="game-prompt">${escapeText(sentence)}</h3>
                    </div>
                    ${optChips ? `<div class="mb-3 text-center"><small class="text-muted d-block mb-1">Palabras de ayuda:</small><div class="d-flex justify-content-center flex-wrap gap-2">${optChips}</div></div>` : ''}
                    <div class="row justify-content-center">
                        <div class="col-md-8">
                            <div class="input-group input-group-lg shadow-xs">
                                <input type="text" id="ai-fill-input" class="form-control rounded-start-4 fw-bold text-center" placeholder="Escribe tu respuesta aquí...">
                                <button type="button" class="btn btn-warning rounded-end-4 fw-bold px-4" id="btn-submit-fill-ai">
                                    Responder 🚀
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (game.game_type === 'matching') {
            const pairs = content.pairs || [];
            const leftItems = content.left_items || pairs.map(p => p.left);
            const rightItems = content.right_items || [...pairs.map(p => p.right)].sort(() => Math.random() - 0.5);

            interactionHtml = `
                <section class="matching-game mb-2">
                    <span class="game-kicker"><i class="bi bi-puzzle-fill"></i> Conecta las pistas</span>
                    <p class="game-help">Elige la pista que completa cada concepto. Todas salen de la clase.</p>
                    <div class="matching-board">
                        ${leftItems.map((left, idx) => `
                            <article class="matching-row">
                                <div class="matching-concept"><span class="matching-index">${idx + 1}</span><strong>${escapeText(left)}</strong></div>
                                <span class="matching-link" aria-hidden="true"><i class="bi bi-arrow-right"></i></span>
                                <div class="matching-answer">
                                    <label class="visually-hidden" for="matching-answer-${idx}">Pareja para ${escapeText(left)}</label>
                                    <select id="matching-answer-${idx}" class="matching-select matching-select-control" data-left="${escapeText(left)}" aria-label="Pareja para ${escapeText(left)}">
                                        <option value="">— Elige su pareja —</option>
                                        ${rightItems.map(r => `<option value="${escapeText(r)}">${escapeText(r)}</option>`).join('')}
                                    </select>
                                </div>
                            </article>
                        `).join('')}
                    </div>
                    <button type="button" class="game-primary-btn matching-submit" id="btn-submit-matching-ai"><i class="bi bi-check2-circle me-1"></i> Comprobar parejas</button>
                </section>
            `;
        } else if (game.game_type === 'memory') {
            const cards = [...(content.cards || [])].sort(() => Math.random() - 0.5);
            interactionHtml = `
                <div class="mb-2 text-center">
                    <span class="game-kicker">Dos cartas, una pareja</span>
                    <p class="game-help">Voltea dos cartas. Si van juntas, ¡ganas una estrella!</p>
                    <div class="memory-cards-grid" id="memory-cards-board">
                        ${cards.map(card => `<button type="button" class="memory-card" data-pair="${card.pair_id}" data-side="${card.side}" data-text="${escapeText(card.text || '')}" aria-label="Carta boca abajo"><i class="bi bi-suit-spade-fill memory-card-icon"></i><span class="memory-card-text d-none">${escapeText(card.text || '')}</span></button>`).join('')}
                    </div>
                    <small class="game-help d-block mt-3">Parejas encontradas: <span id="memory-pairs-count">0</span></small>
                </div>
            `;
        } else if (game.game_type === 'ordering') {
            const items = content.items || [];
            interactionHtml = `
                <div class="mb-4"><span class="game-kicker">Arma la historia</span><p class="game-help">Toma una pieza y colócala donde debe ir.</p>
                    <div id="ordering-board" class="d-grid gap-2">${items.map(item => `<div class="ordering-item p-3 rounded-4 bg-white border border-2 border-primary-subtle fw-bold" draggable="true" data-item="${escapeText(item)}"><i class="bi bi-grip-vertical text-primary me-2"></i>${escapeText(item)}</div>`).join('')}</div>
                    <button type="button" class="game-primary-btn mt-3" id="btn-submit-ordering-ai"><i class="bi bi-check2-circle me-1"></i> Revisar orden</button>
                </div>
            `;
        } else if (game.game_type === 'drag_drop') {
            const items = content.items || [];
            const categories = content.categories || [];
            interactionHtml = `
                <div class="mb-4"><span class="game-kicker">Cada cosa en su lugar</span><p class="game-help">Arrastra las tarjetas a su grupo, o pulsa una tarjeta y luego su grupo.</p>
                    <div class="d-flex flex-wrap gap-2 justify-content-center mb-3" id="drag-items-source">${items.map(item => `<button type="button" draggable="true" class="btn btn-outline-success fw-bold drag-item" data-item="${escapeText(item)}">${escapeText(item)}</button>`).join('')}</div>
                    <div class="row g-3">${categories.map(category => `<div class="col-md"><div class="drag-category h-100 p-3 rounded-4 border border-2 border-success-subtle bg-white" data-category="${escapeText(category)}"><strong class="d-block text-success mb-2">${escapeText(category)}</strong><div class="drop-items small text-muted">Suelta aquí</div></div></div>`).join('')}</div></div>
                    <button type="button" class="game-primary-btn mt-3" id="btn-submit-drag-ai"><i class="bi bi-check2-circle me-1"></i> Comprobar clasificación</button>
                </div>
            `;
        } else if (game.game_type === 'challenge') {
            const levels = content.levels || [];
            interactionHtml = `
                <div class="mb-4"><div class="challenge-route">${levels.map((_, index) => `<span class="challenge-route-step ${index === 0 ? 'is-active' : ''}" data-route-step="${index}">${index + 1}</span>`).join('')}</div>
                    <div id="challenge-levels">${levels.map((level, index) => `<section class="challenge-level ${index ? 'd-none' : ''}" data-level="${index}"><span class="game-kicker"><i class="bi bi-rocket-takeoff-fill"></i> Nivel ${index + 1}</span><h3 class="game-prompt">${escapeText(level.question || '')}</h3><div class="d-grid gap-2 mt-3">${(level.options || []).map((option, optionIndex) => `<button type="button" class="game-choice challenge-option" data-answer="${escapeText(option)}"><span class="choice-key">${String.fromCharCode(65 + optionIndex)}</span>${escapeText(option)}</button>`).join('')}</div></section>`).join('')}</div>
                    <button type="button" class="game-primary-btn mt-3" id="btn-next-challenge-ai" disabled>Siguiente nivel</button>
                </div>
            `;
        }

        const totalStages = game.game_type === 'challenge' ? Math.max(1, (content.levels || []).length) : game.game_type === 'memory' ? Math.max(1, (content.cards || []).length / 2) : 1;
        const levelName = game.game_type === 'challenge' ? 'Nivel 1' : 'Reto 1';
        arena.innerHTML = `
            <header class="game-header">
                <div>
                    <span class="game-kicker"><i class="bi bi-rocket-takeoff-fill"></i>${levelName} de ${totalStages}</span>
                    <h2>${escapeText(game.title)}</h2>
                </div>
                <button type="button" class="game-exit-btn" onclick="document.getElementById('ai-game-play-arena').style.display='none'" aria-label="Salir de la misión"><i class="bi bi-x-lg"></i> <span>Salir</span></button>
            </header>
            <div class="mission-progress" aria-label="Progreso de la misión">
                <span id="game-progress-label">Tu misión comienza</span>
                <div class="mission-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="mission-progress-value" id="game-progress-value" style="--progress: 0%"></div></div>
                <span class="mission-reward"><i class="bi bi-star-fill"></i> +${game.game_type === 'challenge' ? '30' : '10'}</span>
            </div>
            <div class="game-stage">${interactionHtml}</div>
            <div id="ai-game-feedback-box" class="mt-3" style="display: none;"></div>`;

        const startTime = Date.now();
        const setMissionProgress = (completed, total, label) => {
            const percentage = Math.round((completed / Math.max(1, total)) * 100);
            const value = arena.querySelector('#game-progress-value');
            const progress = arena.querySelector('[role="progressbar"]');
            const text = arena.querySelector('#game-progress-label');
            if (value) value.style.setProperty('--progress', `${percentage}%`);
            if (progress) progress.setAttribute('aria-valuenow', String(percentage));
            if (text) text.textContent = label || `${completed} de ${total} superados`;
        };

        if (game.game_type === 'multiple_choice') {
            arena.querySelectorAll('.btn-ai-mc-option').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const answer = btn.dataset.answer;
                    arena.querySelectorAll('.btn-ai-mc-option').forEach(b => b.disabled = true);
                    const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                    await submitAiGamePlay(game.id, answer, timeSpent);
                });
            });
        } else if (game.game_type === 'true_false') {
            arena.querySelectorAll('.btn-ai-tf-option').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const answer = btn.dataset.answer === 'true';
                    arena.querySelectorAll('.btn-ai-tf-option').forEach(b => b.disabled = true);
                    const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                    await submitAiGamePlay(game.id, answer, timeSpent);
                });
            });
        } else if (game.game_type === 'fill_blank') {
            const input = arena.querySelector('#ai-fill-input');
            arena.querySelectorAll('.btn-fill-chip').forEach(chip => {
                chip.addEventListener('click', () => {
                    if (input) input.value = chip.dataset.word;
                });
            });
            arena.querySelector('#btn-submit-fill-ai')?.addEventListener('click', async () => {
                const ans = (input?.value || '').trim();
                if (!ans) {
                    alert('Por favor escribe tu respuesta antes de continuar.');
                    return;
                }
                const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                await submitAiGamePlay(game.id, ans, timeSpent);
            });
        } else if (game.game_type === 'matching') {
            arena.querySelector('#btn-submit-matching-ai')?.addEventListener('click', async () => {
                const selects = arena.querySelectorAll('.matching-select');
                const studentPairs = [];
                let allFilled = true;
                selects.forEach(sel => {
                    const l = sel.dataset.left;
                    const r = sel.value;
                    if (!r) allFilled = false;
                    studentPairs.push({ left: l, right: r });
                });
                if (!allFilled) {
                    alert('Por favor selecciona la pareja de cada uno de los elementos.');
                    return;
                }
                const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                await submitAiGamePlay(game.id, studentPairs, timeSpent);
            });
        } else if (game.game_type === 'memory') {
            let firstCard = null;
            let checkingPair = false;
            const foundPairs = [];
            arena.querySelectorAll('.memory-card').forEach(card => {
                card.addEventListener('click', () => {
                    if (checkingPair || card.disabled || card === firstCard) return;
                    card.querySelector('.memory-card-text')?.classList.remove('d-none');
                    card.querySelector('.memory-card-icon')?.classList.add('d-none');
                    card.classList.add('is-revealed');
                    if (!firstCard) { firstCard = card; return; }
                    const samePair = firstCard.dataset.pair === card.dataset.pair && firstCard.dataset.side !== card.dataset.side;
                    if (samePair) {
                        const left = firstCard.dataset.side === 'left' ? firstCard.dataset.text : card.dataset.text;
                        const right = firstCard.dataset.side === 'right' ? firstCard.dataset.text : card.dataset.text;
                        foundPairs.push({ left, right });
                        firstCard.disabled = card.disabled = true;
                        firstCard.classList.add('is-paired');
                        card.classList.add('is-paired');
                        arena.querySelector('#memory-pairs-count').textContent = foundPairs.length;
                        setMissionProgress(foundPairs.length, Math.max(1, arena.querySelectorAll('.memory-card').length / 2), `${foundPairs.length} parejas encontradas`);
                        firstCard = null;
                        if (foundPairs.length * 2 === arena.querySelectorAll('.memory-card').length) {
                            const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                            submitAiGamePlay(game.id, null, timeSpent, { matches: foundPairs });
                        }
                    } else {
                        const previous = firstCard;
                        checkingPair = true;
                        firstCard = null;
                        window.setTimeout(() => {
                            checkingPair = false;
                            [previous, card].forEach(item => {
                                item.querySelector('.memory-card-text')?.classList.add('d-none');
                                item.querySelector('.memory-card-icon')?.classList.remove('d-none');
                                item.classList.remove('is-revealed');
                            });
                        }, 650);
                    }
                });
            });
        } else if (game.game_type === 'ordering') {
            let dragged = null;
            const board = arena.querySelector('#ordering-board');
            board?.querySelectorAll('.ordering-item').forEach(item => {
                item.addEventListener('dragstart', () => { dragged = item; });
                item.addEventListener('dragover', event => event.preventDefault());
                item.addEventListener('drop', event => {
                    event.preventDefault();
                    if (dragged && dragged !== item) board.insertBefore(dragged, item);
                });
            });
            arena.querySelector('#btn-submit-ordering-ai')?.addEventListener('click', async () => {
                const order = [...board.querySelectorAll('.ordering-item')].map(item => item.dataset.item);
                const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                await submitAiGamePlay(game.id, null, timeSpent, { order });
            });
        } else if (game.game_type === 'drag_drop') {
            let dragged = null;
            const selectCard = item => {
                dragged = item;
                arena.querySelectorAll('.drag-item').forEach(card => {
                    card.classList.toggle('active', card === item);
                    card.setAttribute('aria-pressed', String(card === item));
                });
            };
            const placeCard = zone => {
                if (!dragged) return;
                zone.querySelector('.drop-items')?.append(dragged);
                dragged.classList.remove('active');
                dragged.setAttribute('aria-pressed', 'false');
                dragged = null;
            };
            arena.querySelectorAll('.drag-item').forEach(item => {
                item.setAttribute('aria-pressed', 'false');
                item.addEventListener('click', () => selectCard(item));
                item.addEventListener('dragstart', event => {
                    selectCard(item);
                    event.dataTransfer.setData('text/plain', item.dataset.item);
                    event.dataTransfer.effectAllowed = 'move';
                });
            });
            arena.querySelectorAll('.drag-category').forEach(zone => {
                zone.tabIndex = 0;
                zone.setAttribute('role', 'button');
                zone.setAttribute('aria-label', `Colocar tarjeta en ${zone.dataset.category}`);
                zone.addEventListener('click', event => {
                    if (!event.target.closest('.drag-item')) placeCard(zone);
                });
                zone.addEventListener('keydown', event => {
                    if (event.target === zone && ['Enter', ' '].includes(event.key)) {
                        event.preventDefault();
                        placeCard(zone);
                    }
                });
                zone.addEventListener('dragover', event => event.preventDefault());
                zone.addEventListener('drop', event => {
                    event.preventDefault();
                    placeCard(zone);
                });
            });
            arena.querySelector('#btn-submit-drag-ai')?.addEventListener('click', async () => {
                const placements = [...arena.querySelectorAll('.drag-category')].flatMap(zone => [...zone.querySelectorAll('.drag-item')].map(item => ({ item: item.dataset.item, category: zone.dataset.category })));
                if (placements.length !== arena.querySelectorAll('.drag-item').length) { alert('Arrastra todas las tarjetas a un grupo antes de continuar.'); return; }
                const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                await submitAiGamePlay(game.id, null, timeSpent, { placements });
            });
        } else if (game.game_type === 'challenge') {
            const answers = [];
            let selected = null;
            let level = 0;
            const next = arena.querySelector('#btn-next-challenge-ai');
            const levels = [...arena.querySelectorAll('.challenge-level')];
            arena.querySelectorAll('.challenge-option').forEach(button => {
                button.addEventListener('click', () => {
                    const parent = button.closest('.challenge-level');
                    parent.querySelectorAll('.challenge-option').forEach(item => item.classList.remove('active'));
                    button.classList.add('active'); selected = button.dataset.answer; next.disabled = false;
                });
            });
            next?.addEventListener('click', async () => {
                if (selected === null) return;
                answers[level] = selected; selected = null; next.disabled = true; levels[level].classList.add('d-none'); level += 1;
                setMissionProgress(level, levels.length, `${level} de ${levels.length} niveles superados`);
                arena.querySelectorAll('[data-route-step]').forEach((step, index) => step.classList.toggle('is-active', index === level));
                if (level < levels.length) { levels[level].classList.remove('d-none'); next.textContent = level === levels.length - 1 ? 'Terminar misión' : 'Siguiente nivel'; return; }
                const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
                await submitAiGamePlay(game.id, null, timeSpent, { answers });
            });
        }
    }

    async function submitAiGamePlay(gameId, answer, timeSpent, extraPayload = {}) {
        const feedbackBox = document.getElementById('ai-game-feedback-box');
        if (!feedbackBox) return;

        feedbackBox.style.display = 'block';
        feedbackBox.innerHTML = `
            <div class="game-feedback">
                <div class="spinner-border spinner-border-sm text-warning me-2" role="status"></div>
                Comprobando tu pista...
            </div>
        `;

        try {
            const resp = await fetch(`/student/api/ai-games/${gameId}/play`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer, time_spent: timeSpent, ...extraPayload })
            });
            const data = await resp.json();

            if (!resp.ok || !data.success) {
                feedbackBox.innerHTML = `
                    <div class="alert alert-danger rounded-4 p-3 text-center">
                        ${data.error || 'No se pudo registrar la respuesta.'}
                    </div>
                `;
                return;
            }

            const isCorrect = data.is_correct;
            const headline = data.feedback_headline || (isCorrect ? '¡Correcto! 🎉 +10 puntos' : '¡Casi! Inténtalo de nuevo 💪');
            const explanation = data.explanation || (isCorrect ? '¡Excelente razonamiento! Has sumado puntos a tu progreso.' : '¡Buen intento! Cada error es una oportunidad para aprender.');
            const progressValue = document.getElementById('game-progress-value');
            const progressBar = document.querySelector('#ai-game-play-arena [role="progressbar"]');
            const progressLabel = document.getElementById('game-progress-label');
            if (progressValue) progressValue.style.setProperty('--progress', isCorrect ? '100%' : '45%');
            if (progressBar) progressBar.setAttribute('aria-valuenow', isCorrect ? '100' : '45');
            if (progressLabel) progressLabel.textContent = isCorrect ? '¡Misión completada!' : '¡Ya encontraste una pista!';

            feedbackBox.innerHTML = `
                <div class="game-feedback ${isCorrect ? 'is-correct' : 'is-try-again'}">
                    ${isCorrect ? '<div class="celebration-stars" aria-hidden="true"><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i></div>' : ''}
                    <span class="game-feedback-icon" aria-hidden="true"><i class="bi ${isCorrect ? 'bi-balloon-heart-fill' : 'bi-lightbulb-fill'}"></i></span>
                    <h3>${headline}</h3>
                    <p>${escapeText(explanation)}</p>
                    ${isCorrect ? '<p><strong>¡Ganaste estrellas para tu próxima aventura!</strong></p>' : '<p>Lee la pista y prueba otra vez. Cada intento te hace mejor.</p>'}
                    <div class="d-flex justify-content-center gap-2 mt-2">
                        <button type="button" class="game-primary-btn" id="btn-replay-ai-game">
                            <i class="bi bi-arrow-repeat me-1"></i> ${isCorrect ? 'Otra misión' : 'Intentarlo otra vez'}
                        </button>
                        <button type="button" class="game-exit-btn px-3" onclick="document.getElementById('ai-game-play-arena').style.display='none'">
                            Ver Más Juegos
                        </button>
                    </div>
                </div>
            `;

            feedbackBox.querySelector('#btn-replay-ai-game')?.addEventListener('click', () => openAiGame(gameId));
            feedbackBox.scrollIntoView({ behavior: 'smooth', block: 'center' });

            if (typeof loadProgress === 'function') loadProgress();
            if (typeof loadRecommendations === 'function') loadRecommendations();
            if (typeof loadStudentRiskPrediction === 'function') loadStudentRiskPrediction();

        } catch (err) {
            feedbackBox.innerHTML = `
                <div class="alert alert-danger rounded-4 p-3 text-center">
                    Error de conexión: ${err.message}
                </div>
            `;
        }
    }


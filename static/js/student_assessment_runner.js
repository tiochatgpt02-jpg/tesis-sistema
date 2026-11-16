/* Published practices and exams. The server freezes questions when Start is pressed. */
(() => {
    'use strict';
    let timer = null;
    let loadId = 0;
    const element = (tag, text, className) => {
        const item = document.createElement(tag);
        if (text !== undefined) item.textContent = text;
        if (className) item.className = className;
        return item;
    };
    const button = (text, action, className = 'btn btn-primary') => {
        const item = element('button', text, className);
        item.type = 'button'; item.addEventListener('click', action); return item;
    };
    async function call(url, options) {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'No se pudo completar la solicitud.');
        return data;
    }
    function message(container, text, error = false) {
        const box = element('p', text, `alert alert-${error ? 'danger' : 'info'}`);
        box.setAttribute('role', error ? 'alert' : 'status');
        container.replaceChildren(box);
    }
    async function load(topicId, targetId = 'evaluation-container-box') {
        if (timer) clearInterval(timer);
        const token = ++loadId;
        const container = document.getElementById(targetId);
        if (!container) return;
        message(container, 'Buscando prácticas y exámenes publicados...');
        try {
            const data = await call(`/student/api/topics/${topicId}/assessments`);
            if (token !== loadId) return;
            container.replaceChildren();
            container.append(element('h5', 'Prácticas y exámenes', 'fw-bold mb-3'));
            if (!data.assessments.length) {
                container.append(element('p', 'El docente todavía no ha publicado una evaluación para esta clase.', 'text-muted'));
                return;
            }
            for (const assessment of data.assessments) {
                const card = element('article', undefined, 'panel-card border rounded p-3 mb-3');
                card.dataset.assessmentId = String(assessment.id);
                card.append(element('span', assessment.kind === 'practice' ? 'Práctica calificada' : 'Examen bimestral', 'badge bg-primary mb-2'));
                card.append(element('h6', assessment.title, 'fw-bold'));
                card.append(element('p', assessment.kind === 'practice'
                    ? 'Puedes repetirla para practicar. Se conserva tu último intento.'
                    : 'Tienes 30 minutos desde que comienzas. Otro intento requiere autorización del docente.', 'small'));
                card.append(button('Abrir evaluación', () => preview(assessment.id, topicId, targetId)));
                container.append(card);
            }
        } catch (error) {
            if (token === loadId) message(container, error.message, true);
        }
    }
    async function preview(identity, topicId, targetId) {
        const token = ++loadId;
        const container = document.getElementById(targetId);
        message(container, 'Preparando la evaluación...');
        try {
            const data = await call(`/student/api/assessments/${identity}`);
            if (token !== loadId) return;
            const assessment = data.assessment;
            const card = element('section', undefined, 'panel-card border rounded p-4');
            card.append(element('h5', assessment.title, 'fw-bold'));
            card.append(element('p', assessment.rule));
            card.append(element('p', `${assessment.question_count} preguntas. El tiempo del examen empieza al pulsar Comenzar.`, 'text-muted'));
            const actions = element('div', undefined, 'd-flex flex-wrap gap-2');
            actions.append(button('Comenzar o reanudar', async event => {
                const control = event.currentTarget; control.disabled = true;
                try {
                    const started = await call(`/student/api/assessments/${identity}/start`, { method: 'POST' });
                    if (token !== loadId) return;
                    renderAttempt(container, started, topicId, targetId);
                } catch (error) {
                    control.disabled = false;
                    const feedback = element('p', error.message, 'alert alert-warning mt-3');
                    feedback.setAttribute('role', 'alert'); card.append(feedback);
                }
            }), button('Volver', () => load(topicId, targetId), 'btn btn-outline-secondary'));
            card.append(actions); container.replaceChildren(card);
        } catch (error) { message(container, error.message, true); }
    }
    function renderAttempt(container, data, topicId, targetId) {
        if (timer) clearInterval(timer);
        const token = loadId;
        const card = element('section', undefined, 'panel-card border rounded p-4');
        card.append(element('h5', data.title, 'fw-bold'));
        const clock = element('p', '', 'fw-bold text-primary');
        card.append(clock);
        const form = element('form');
        form.setAttribute('aria-label', data.title);
        const draftKey = `assessment-draft:${data.student_id}:${data.attempt.attempt_id}`;
        let draft = {};
        try { draft = JSON.parse(sessionStorage.getItem(draftKey) || '{}'); } catch { draft = {}; }
        data.attempt.questions.forEach((question, index) => {
            const fieldset = element('fieldset', undefined, 'border rounded p-3 mb-3');
            fieldset.append(element('legend', `${index + 1}. ${question.question}`, 'h6 fw-bold'));
            question.options.forEach((option, optionIndex) => {
                const row = element('div', undefined, 'form-check mb-2');
                const input = document.createElement('input');
                input.type = 'radio'; input.name = `question_${index}`; input.value = option;
                input.id = `assessment-${data.attempt.attempt_id}-${index}-${optionIndex}`;
                input.className = 'form-check-input'; input.required = true;
                input.checked = draft[index] === option;
                const label = element('label', option, 'form-check-label'); label.htmlFor = input.id;
                input.addEventListener('change', () => {
                    draft[index] = option;
                    try { sessionStorage.setItem(draftKey, JSON.stringify(draft)); } catch { /* Optional draft storage. */ }
                });
                row.append(input, label); fieldset.append(row);
            });
            form.append(fieldset);
        });
        const feedback = element('div', undefined, 'mb-3'); feedback.setAttribute('role', 'status');
        const submit = element('button', 'Finalizar y guardar nota', 'btn btn-primary'); submit.type = 'submit';
        form.append(feedback, submit); card.append(form); container.replaceChildren(card);
        let submitted = false;
        const finish = async automatic => {
            if (submitted || (!automatic && !form.reportValidity())) return;
            submitted = true; submit.disabled = true;
            const answers = {};
            data.attempt.questions.forEach((_, index) => { answers[index] = form.querySelector(`input[name="question_${index}"]:checked`)?.value || ''; });
            try {
                const response = await call(`/student/api/assessments/${data.assessment_id}/attempt`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ attempt_id: data.attempt.attempt_id, answers }),
                });
                if (timer) clearInterval(timer);
                try { sessionStorage.removeItem(draftKey); } catch { /* Optional draft storage. */ }
                const result = response.result;
                const summary = element('section', undefined, 'panel-card border rounded p-4');
                summary.setAttribute('role', 'status');
                summary.append(element('h5', 'Evaluación guardada', 'fw-bold'));
                summary.append(element('p', `Tu nota: ${result.score} / 20`, 'h3'));
                summary.append(element('p', `Respuestas correctas: ${result.correct_count} de ${result.total}.`));
                summary.append(button('Volver a las evaluaciones', () => load(topicId, targetId)));
                if (token === loadId) container.replaceChildren(summary);
                if (typeof window.loadProgress === 'function') window.loadProgress();
                if (typeof window.loadStudentRiskPrediction === 'function') window.loadStudentRiskPrediction();
            } catch (error) {
                submitted = false; submit.disabled = false;
                feedback.textContent = error.message;
                feedback.className = 'alert alert-danger';
            }
        };
        form.addEventListener('submit', event => { event.preventDefault(); finish(false); });
        if (data.kind === 'exam') {
            const startedAt = performance.now();
            const initial = data.remaining_seconds;
            const tick = () => {
                const remaining = Math.max(0, initial - Math.floor((performance.now()-startedAt)/1000));
                clock.textContent = `Tiempo restante: ${String(Math.floor(remaining/60)).padStart(2,'0')}:${String(remaining%60).padStart(2,'0')}`;
                if (remaining === 0 && !submitted) { clearInterval(timer); finish(true); }
            };
            tick();
            if (initial > 0) timer = setInterval(tick, 1000);
        } else clock.textContent = 'Práctica: puedes volver a intentarla cuando termines.';
    }
    window.StudentAssessmentRunner = { load };
})();

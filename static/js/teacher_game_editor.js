/* Structured game editing. Content is assigned through DOM values, never raw HTML. */
(() => {
    'use strict';
    let sequence = 0;
    const labels = {
        multiple_choice: 'Opción múltiple', true_false: 'Verdadero o falso', fill_blank: 'Completar',
        matching: 'Unir conceptos', memory: 'Memoria', ordering: 'Ordenar',
        drag_drop: 'Clasificar', challenge: 'Aventura por niveles',
    };

    function create(type, content = {}) {
        if (!labels[type]) throw new Error('Este tipo de juego no está disponible para edición.');
        const root = document.createElement('div');
        root.className = 'teacher-game-editor';
        root.dataset.gameType = type;
        const changed = () => root.dispatchEvent(new Event('input', { bubbles: true }));
        const node = (tag, text, className) => {
            const element = document.createElement(tag);
            if (text !== undefined) element.textContent = text;
            if (className) element.className = className;
            return element;
        };
        const field = (parent, label, value = '', kind = 'input', required = true) => {
            const wrapper = node('div', undefined, 'mb-3');
            const id = `game-editor-field-${++sequence}`;
            const caption = node('label', label, 'form-label small fw-bold');
            caption.htmlFor = id;
            const input = document.createElement(kind);
            input.id = id;
            input.name = id;
            input.className = kind === 'select' ? 'form-select' : 'form-control';
            input.required = required;
            if (kind === 'textarea') input.rows = 3;
            if (kind === 'input') input.type = 'text';
            if (kind !== 'select') input.value = String(value ?? '');
            input.maxLength = 1500;
            wrapper.append(caption, input);
            parent.append(wrapper);
            return input;
        };
        const button = (parent, label, handler) => {
            const control = node('button', label, 'btn btn-outline-secondary btn-sm');
            control.type = 'button';
            control.addEventListener('click', () => { handler(); changed(); });
            parent.append(control);
            return control;
        };
        const list = (parent, label, values, minimum, maximum, render) => {
            const group = node('fieldset', undefined, 'mb-3');
            group.append(node('legend', label, 'h6'));
            const rows = node('div');
            const actions = node('div', undefined, 'd-flex flex-wrap gap-2');
            group.append(rows, actions);
            parent.append(group);
            const add = value => {
                const row = node('div', undefined, 'game-editor-row border rounded p-3 mb-2');
                const reader = render(row, value);
                const rowActions = node('div', undefined, 'd-flex flex-wrap gap-2');
                row.append(rowActions);
                button(rowActions, 'Quitar', () => {
                    if (rows.children.length <= minimum) {
                        notice.textContent = `Se necesitan al menos ${minimum} elementos.`;
                        return;
                    }
                    row.remove();
                    notice.textContent = '';
                    changed();
                });
                row.readValue = reader;
                rows.append(row);
                return row;
            };
            const notice = node('p', '', 'small text-danger mt-2');
            notice.setAttribute('role', 'status');
            button(actions, 'Añadir elemento', () => {
                if (rows.children.length >= maximum) {
                    notice.textContent = `Puedes usar hasta ${maximum} elementos.`;
                    return;
                }
                const row = add(undefined);
                row.querySelector('input,textarea,select')?.focus();
            });
            group.append(notice);
            const initial = values.length ? values.slice(0, maximum) : Array(minimum).fill(undefined);
            initial.forEach(add);
            return { read: () => [...rows.children].map(row => row.readValue()), rows };
        };
        const choice = (parent, question, options, answer) => {
            const prompt = field(parent, 'Pregunta', question);
            const correct = field(parent, 'Respuesta correcta', '', 'select');
            const optionsList = list(parent, 'Alternativas', options || [], 2, 4, (row, value) => {
                row.dataset.optionId = String(++sequence);
                const input = field(row, 'Alternativa', value);
                return () => input.value.trim();
            });
            const sync = () => {
                const selected = correct.value;
                correct.replaceChildren();
                const placeholder = node('option', 'Selecciona la respuesta correcta'); placeholder.value = ''; correct.append(placeholder);
                [...optionsList.rows.children].forEach((row, index) => {
                    const text = row.readValue();
                    const option = node('option', text || `Alternativa ${index + 1}`);
                    option.value = row.dataset.optionId;
                    correct.append(option);
                });
                if ([...correct.options].some(option => option.value === selected)) correct.value = selected;
            };
            sync();
            const answerIndex = (options || []).findIndex(value => String(value).trim() === String(answer).trim());
            correct.value = optionsList.rows.children[answerIndex]?.dataset.optionId || '';
            optionsList.rows.addEventListener('input', sync);
            optionsList.rows.parentElement.addEventListener('click', event => { if (event.target.closest('button')) sync(); });
            return () => ({ question: prompt.value.trim(), options: optionsList.read(),
                           answer: [...optionsList.rows.children].find(row => row.dataset.optionId === correct.value)?.readValue() });
        };

        let read;
        if (type === 'multiple_choice') {
            read = choice(root, content.question, content.options, content.answer);
        } else if (type === 'true_false') {
            const statement = field(root, 'Afirmación', content.statement);
            const answer = field(root, 'Respuesta correcta', '', 'select');
            for (const [value, text] of [['true', 'Verdadero'], ['false', 'Falso']]) {
                const option = node('option', text); option.value = value; answer.append(option);
            }
            answer.value = content.correct_answer === false ? 'false' : 'true';
            read = () => ({ statement: statement.value.trim(), correct_answer: answer.value === 'true' });
        } else if (type === 'fill_blank') {
            const sentence = field(root, 'Oración con un espacio en blanco (______) ', content.sentence);
            const word = field(root, 'Palabra que completa la oración', content.blank_word || content.answers?.[0]);
            const options = field(root, 'Alternativas, una por línea', (content.options || []).join('\n'), 'textarea', false);
            read = () => ({ sentence: sentence.value.trim(), blank_word: word.value.trim(), answers: [word.value.trim()],
                           options: options.value.split(/\r?\n/).map(text => text.trim()).filter(Boolean) });
        } else if (type === 'matching' || type === 'memory') {
            const pairs = list(root, 'Parejas', content.pairs || [], 2, 6, (row, value = {}) => {
                const left = field(row, 'Concepto o primera tarjeta', value.left);
                const right = field(row, 'Significado o pareja', value.right);
                return () => ({ left: left.value.trim(), right: right.value.trim() });
            });
            read = () => ({ pairs: pairs.read() });
        } else if (type === 'ordering') {
            const items = list(root, 'Elementos en su orden correcto', content.items || [], 3, 8, (row, value) => {
                const input = field(row, 'Paso o elemento', value);
                const controls = node('div', undefined, 'd-flex flex-wrap gap-2 mb-2');
                row.append(controls);
                button(controls, 'Subir', () => { if (row.previousElementSibling) row.parentElement.insertBefore(row, row.previousElementSibling); });
                button(controls, 'Bajar', () => { if (row.nextElementSibling) row.parentElement.insertBefore(row.nextElementSibling, row); });
                return () => input.value.trim();
            });
            read = () => ({ items: items.read() });
        } else if (type === 'drag_drop') {
            let categoryId = 0;
            const categories = list(root, 'Grupos o categorías', content.categories || [], 2, 6, (row, value) => {
                row.dataset.categoryId = String(++categoryId);
                const input = field(row, 'Nombre del grupo', value);
                return () => input.value.trim();
            });
            const items = list(root, 'Elementos para clasificar', content.items || [], 2, 10, (row, value = {}) => {
                const text = field(row, 'Elemento', value.item);
                const target = field(row, 'Grupo correcto', '', 'select');
                target.dataset.initialCategory = value.category || '';
                return () => ({ item: text.value.trim(), category: [...categories.rows.children]
                    .find(category => category.dataset.categoryId === target.value)?.readValue() || '' });
            });
            const sync = () => [...items.rows.children].forEach(row => {
                const select = row.querySelector('select');
                const selected = select.value;
                select.replaceChildren();
                const placeholder = node('option', 'Selecciona un grupo'); placeholder.value = ''; select.append(placeholder);
                [...categories.rows.children].forEach(category => {
                    const text = category.readValue();
                    const option = node('option', text || 'Grupo sin nombre'); option.value = category.dataset.categoryId; select.append(option);
                    if (!selected && select.dataset.initialCategory === text) select.value = option.value;
                });
                if ([...select.options].some(option => option.value === selected) && selected) select.value = selected;
                delete select.dataset.initialCategory;
            });
            categories.rows.parentElement.addEventListener('input', sync);
            categories.rows.parentElement.addEventListener('click', event => { if (event.target.closest('button')) sync(); });
            items.rows.parentElement.addEventListener('click', event => { if (event.target.closest('button')) sync(); });
            sync();
            read = () => ({ categories: categories.read(), items: items.read() });
        } else if (type === 'challenge') {
            const levels = [];
            for (let index = 0; index < 3; index++) {
                const group = node('fieldset', undefined, 'border rounded p-3 mb-3');
                group.append(node('legend', `Nivel ${index + 1}`, 'h6'));
                root.append(group);
                const level = content.levels?.[index] || {};
                const reader = choice(group, level.question, level.options, level.answer);
                levels.push(() => ({ level: index + 1, ...reader() }));
            }
            read = () => ({ levels: levels.map(reader => reader()) });
        }
        const explanation = field(root, 'Explicación para el alumno', content.explanation, 'textarea', false);
        return {
            element: root,
            read: () => ({ ...read(), explanation: explanation.value.trim() }),
            reportValidity: () => {
                for (const control of root.querySelectorAll('input,textarea,select')) {
                    if (!control.reportValidity()) return false;
                }
                return true;
            },
        };
    }
    window.TeacherGameEditor = { create, labels };
})();

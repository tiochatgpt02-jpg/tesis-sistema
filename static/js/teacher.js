let selectedNotesRow = null;
let notesStudentName = null;
let selectedStudentScore = null;
let selectedStudentGrade = null;
let selectedStudentNotes = null;
let activityType = null;
let notesDateFrom = null;
let notesDateTo = null;
let notesResultsTable = null;
let selectedStudentImage = null;
let selectedStudentStatus = null;
let selectedStudentStatusDesc = null;

window.selectedNotesRow = selectedNotesRow;


document.addEventListener('DOMContentLoaded', () => {
    const panels = document.querySelectorAll('.section-panel');
    const navBtns = document.querySelectorAll('.sidebar-btn[data-section]');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.dataset.section;
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            panels.forEach(p => p.classList.remove('active'));
            const target = document.getElementById('section-' + section);
            if (target) target.classList.add('active');
            if (section === 'entregas') loadTeacherSubmissions();
            if (section === 'reportes' && typeof loadAcademicReport === 'function') loadAcademicReport();
        });
    });

    document.querySelectorAll('.teacher-action-card[data-section-target]').forEach(action => {
        action.addEventListener('click', () => {
            const target = document.querySelector(`.sidebar-btn[data-section="${action.dataset.sectionTarget}"]`);
            if (target) target.click();
        });
    });

    async function loadTeacherSubmissions() {
        const container = document.getElementById('teacher-submissions-list');
        if (!container) return;
        try {
            const response = await fetch('/teacher/api/submissions');
            const data = await response.json();
            const submissions = data.success ? (data.submissions || []) : [];
            const studentRows = Array.from(document.querySelectorAll('#student-table-body .student-row'));
            const allStudents = studentRows.map(row => ({
                id: String(row.dataset.id || ''),
                name: row.dataset.name || row.textContent.trim() || 'Alumno',
                grade: String(row.dataset.grade || ''),
            })).filter(student => student.id);

            const submissionMap = new Map();
            submissions.forEach(item => {
                const key = String(item.student_id ?? item.studentId ?? '');
                if (key) submissionMap.set(key, item);
            });

            const topicOptions = [...new Set([
                ...(window.teacherTopics || []).map(topic => topic.title).filter(Boolean),
                ...submissions.map(item => item.topic_title).filter(Boolean),
            ])];
            const gradeOptions = [...new Set(allStudents.map(student => student.grade).filter(Boolean))];
            const fallbackGrades = ['4', '5', '6'];
            const availableGrades = gradeOptions.length ? gradeOptions : fallbackGrades;
            const gradeSelect = `<div class="row g-3 align-items-end mb-3">
                <div class="col-md-3">
                    <label class="form-label small fw-semibold">Grado</label>
                    <select id="submission-grade-filter" class="form-select form-select-sm">
                        <option value="all">Todos</option>
                        ${availableGrades.map(grade => `<option value="${grade}">${grade}°</option>`).join('')}
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label small fw-semibold">Tema</label>
                    <select id="submission-topic-filter" class="form-select form-select-sm">
                        <option value="all">Todos los temas</option>
                        ${topicOptions.map(topic => `<option value="${topic}">${topic}</option>`).join('')}
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label small fw-semibold">Buscar por nombre y apellido</label>
                    <input id="submission-search-input" type="text" class="form-control form-control-sm" placeholder="Ej.: Ana López o Perez">
                </div>
            </div>`;

            const renderRows = (rows) => rows.map(student => {
                const submission = submissionMap.get(student.id);
                const hasSubmission = !!submission;
                const scoreValue = hasSubmission ? (submission.teacher_score ?? '') : '';
                const commentValue = hasSubmission ? (submission.teacher_feedback || '') : '';
                const fileLink = hasSubmission && submission.file_path ? `<a href="${submission.file_path}" target="_blank" rel="noopener"><i class="bi bi-file-earmark-arrow-down"></i> ${submission.file_name || 'Archivo'}</a>` : '<span class="text-muted">Sin entrega</span>';
                return `
                    <tr data-grade="${student.grade}">
                        <td><strong>${student.name}</strong><br><small class="text-muted">${student.grade ? `${student.grade}°` : ''}</small></td>
                        <td>${submission?.topic_title || '—'}</td>
                        <td>${fileLink}</td>
                        <td><span class="status-pill ${hasSubmission ? 'status-excellent' : 'status-progress'}">${hasSubmission ? 'Enviado' : 'No enviado'}</span></td>
                        <td><input type="number" min="0" max="20" class="form-control form-control-sm review-score-input" data-id="${submission?.id || ''}" data-student-id="${student.id}" value="${scoreValue}" placeholder="0" /></td>
                        <td><textarea class="form-control form-control-sm review-comment-input" rows="2" data-id="${submission?.id || ''}" data-student-id="${student.id}" placeholder="Comentario...">${commentValue}</textarea></td>
                        <td><button class="btn btn-sm btn-outline-primary btn-review-submission" data-id="${submission?.id || ''}" data-student-id="${student.id}" data-score="${scoreValue}" data-feedback="${commentValue}"><i class="bi bi-pencil"></i> Revisar</button></td>
                    </tr>
                `;
            }).join('');

            const applyFilters = () => {
                const gradeFilter = document.getElementById('submission-grade-filter');
                const topicFilter = document.getElementById('submission-topic-filter');
                const searchInput = document.getElementById('submission-search-input');
                const selectedGrade = gradeFilter ? gradeFilter.value : 'all';
                const selectedTopic = topicFilter ? topicFilter.value : 'all';
                const query = (searchInput ? searchInput.value : '').trim().toLowerCase();

                const filtered = allStudents.filter(student => {
                    const submission = submissionMap.get(student.id);
                    const submissionTopic = submission?.topic_title || '';
                    const matchesGrade = selectedGrade === 'all' || student.grade === String(selectedGrade);
                    const matchesTopic = selectedTopic === 'all' || submissionTopic === selectedTopic;
                    const matchesQuery = !query || student.name.toLowerCase().includes(query) || student.name.toLowerCase().replace(/\s+/g, '').includes(query.replace(/\s+/g, ''));
                    return matchesGrade && matchesTopic && matchesQuery;
                });

                const tableBody = document.getElementById('teacher-submissions-table-body');
                tableBody.innerHTML = renderRows(filtered);
                if (!filtered.length) {
                    tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">No hay alumnos para los filtros actuales.</td></tr>';
                }

                tableBody.querySelectorAll('.btn-review-submission').forEach(button => {
                    button.addEventListener('click', async () => {
                        const row = button.closest('tr');
                        const scoreInput = row?.querySelector('.review-score-input');
                        const commentInput = row?.querySelector('.review-comment-input');
                        const score = scoreInput ? scoreInput.value : (button.dataset.score || '');
                        const feedback = commentInput ? commentInput.value : (button.dataset.feedback || '');
                        const submissionId = button.dataset.id;
                        const studentId = button.dataset.studentId;
                        const numericScore = Number(score);

                        if (score === '' || score === null || Number.isNaN(numericScore) || numericScore < 0 || numericScore > 100) {
                            window.alert('Primero agrega una nota válida entre 0 y 20 antes de revisar.');
                            return;
                        }

                        const endpoint = submissionId ? `/teacher/api/submissions/${submissionId}/review` : '/teacher/api/submissions/review';
                        const payloadBody = submissionId ? {score, feedback} : {student_id: studentId, score, feedback};
                        const result = await fetch(endpoint, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payloadBody) });
                        const payload = await result.json();
                        if (!payload.success) {
                            window.alert(payload.error || 'No se pudo guardar la revisión.');
                            return;
                        }
                        if (typeof loadAcademicReport === 'function') loadAcademicReport();
                        await loadTeacherSubmissions();
                    });
                });
            };

            container.innerHTML = `
                ${gradeSelect}
                <div class="table-responsive">
                    <table class="teacher-overview-table">
                        <thead><tr><th>Alumno</th><th>Tema</th><th>Trabajo</th><th>Estado</th><th>Nota</th><th>Comentario</th><th>Revisión</th></tr></thead>
                        <tbody id="teacher-submissions-table-body"></tbody>
                    </table>
                </div>
            `;

            const gradeFilter = document.getElementById('submission-grade-filter');
            const topicFilter = document.getElementById('submission-topic-filter');
            const searchInput = document.getElementById('submission-search-input');
            gradeFilter?.addEventListener('change', applyFilters);
            topicFilter?.addEventListener('change', applyFilters);
            searchInput?.addEventListener('input', applyFilters);
            applyFilters();
        } catch (error) {
            container.innerHTML = '<p class="text-danger">No se pudieron cargar las entregas.</p>';
        }
    }

    const obsBox = document.getElementById('observations');
    const gradeField = document.getElementById('student-grade');
    const selectedStudentName = document.getElementById('selected-student-name');
    const gradeFilter = document.getElementById('student-grade-filter');
    const addStudentBtn = document.getElementById('btn-add-student');
    const deleteStudentBtn = document.getElementById('btn-delete-student');
    const saveObservationsBtn = document.getElementById('btn-save-observations');
    const newFirstName = document.getElementById('new-first-name');
    const newLastName = document.getElementById('new-last-name');
    const studentTableBody = document.getElementById('student-table-body');
    selectedStudentImage = document.getElementById('selected-student-image');
    selectedStudentStatus = document.getElementById('selected-student-status');
    selectedStudentStatusDesc = document.getElementById('selected-student-status-desc');

    let selectedRow = null;
    let selectedNotesRow = null;

    function updateSelection(row) {
        if (!row) return;
        selectedStudentName.value = row.dataset.name || '';
        gradeField.value = row.dataset.grade ? `${row.dataset.grade}°` : '';
        obsBox.value = row.dataset.observations || '';
        selectedRow = row;

        const progress = parseInt(row.dataset.progress || '0', 10);
        updateStatusAvatar(progress, true);
    }

    function clearSelection() {
        selectedStudentName.value = '';
        gradeField.value = '';
        obsBox.value = '';
        if (selectedRow) {
            selectedRow.classList.remove('selected');
        }
        selectedRow = null;
        resetStatusAvatar();
    }

    function filterStudents() {
        const grade = gradeFilter.value;
        document.querySelectorAll('.student-row').forEach(row => {
            row.style.display = row.dataset.grade === grade ? '' : 'none';
        });
        clearSelection();
    }

    function attachStudentRowListeners(row) {
        if (!row) return;
        const selectBtn = row.querySelector('.btn-select-student');
        const selectHandler = () => {
            updateSelection(row);
            document.querySelectorAll('.student-row').forEach(r => r.classList.remove('selected'));
            row.classList.add('selected');
        };
        row.addEventListener('click', event => {
            if (event.target.closest('.btn-select-student')) return;
            selectHandler();
        });
        if (selectBtn) {
            selectBtn.addEventListener('click', event => {
                event.stopPropagation();
                selectHandler();
            });
        }
    }

    function getStatusImage(progress) {
        if (progress >= 80) {
            return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%2334d399'/%3E%3Cpath d='M20 30l6 6 12-18 8 12 10-6' fill='none' stroke='%23fff' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E";
        }
        if (progress >= 50) {
            return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23facc15'/%3E%3Cpath d='M22 24c2-2 4-2 6 0m16 0c2-2 4-2 6 0' fill='none' stroke='%23000' stroke-width='4' stroke-linecap='round'/%3E%3Cpath d='M22 42a10 10 0 0 0 20 0' fill='none' stroke='%23000' stroke-width='4' stroke-linecap='round'/%3E%3C/svg%3E";
        }
        return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23f87171'/%3E%3Cpath d='M32 18v20' stroke='%23fff' stroke-width='4' stroke-linecap='round'/%3E%3Ccircle cx='32' cy='44' r='3' fill='%23fff'/%3E%3C/svg%3E";
    }

    function getScoreStatusImage(score) {
        if (score >= 16) {
            return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%2334d399'/%3E%3Cpath d='M20 30l6 6 12-18 8 12 10-6' fill='none' stroke='%23fff' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E";
        }
        if (score >= 10) {
            return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23facc15'/%3E%3Cpath d='M22 24c2-2 4-2 6 0m16 0c2-2 4-2 6 0' fill='none' stroke='%23000' stroke-width='4' stroke-linecap='round'/%3E%3Cpath d='M22 42a10 10 0 0 0 20 0' fill='none' stroke='%23000' stroke-width='4' stroke-linecap='round'/%3E%3C/svg%3E";
        }
        return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23f87171'/%3E%3Cpath d='M32 18v20' stroke='%23fff' stroke-width='4' stroke-linecap='round'/%3E%3Ccircle cx='32' cy='44' r='3' fill='%23fff'/%3E%3C/svg%3E";
    }

    function getScoreStatusLabel(score) {
        if (score >= 16) {
            return 'Desempeño excelente';
        }
        if (score >= 10) {
            return 'Desempeño moderado';
        }
        return 'Desempeño bajo';
    }

    function getStatusLabel(progress) {
        if (progress >= 80) {
            return 'Progreso excelente';
        }
        if (progress >= 50) {
            return 'Progreso moderado';
        }
        return 'Progreso bajo';
    }

    if (studentTableBody) {
        studentTableBody.querySelectorAll('.student-row').forEach(row => {
            attachStudentRowListeners(row);
        });
    }

    gradeFilter.addEventListener('change', filterStudents);
    filterStudents();

    function appendStudentRow(student) {
        const newRow = document.createElement('tr');
        newRow.classList.add('student-row');
        newRow.dataset.id = String(student.id);
        newRow.dataset.grade = String(student.grade);
        newRow.dataset.name = `${student.first_name} ${student.last_name}`;
        newRow.dataset.progress = String(student.progress || 0);
        newRow.dataset.observations = student.observations || '';
        newRow.innerHTML = `
            <td><strong>${student.first_name} ${student.last_name}</strong></td>
            <td>${student.grade}°</td>
            <td style="min-width:120px">
                <div class="d-flex align-items-center gap-2">
                    <div class="progress-bar-mini flex-grow-1">
                        <div class="fill" style="width:${student.progress || 0}%"></div>
                    </div>
                    <small>${student.progress || 0}%</small>
                </div>
            </td>
            <td>${student.observations || ''}</td>
            <td>
                <button class="btn btn-sm btn-outline-secondary btn-select-student" type="button">Seleccionar</button>
            </td>
        `;
        studentTableBody.appendChild(newRow);
        attachStudentRowListeners(newRow);
        addStudentToMessageSelect(student);
        return newRow;
    }

    function addStudentToMessageSelect(student) {
        const select = document.getElementById('message-student-select');
        const gradeSelect = document.getElementById('message-grade-select');
        if (!select) return;
        const fullName = `${student.first_name} ${student.last_name}`;
        if (Array.from(select.options).some(option => option.value === String(student.id))) {
            return;
        }
        const option = document.createElement('option');
        option.value = String(student.id);
        option.dataset.name = fullName;
        option.dataset.grade = String(student.grade);
        option.textContent = `${fullName} (${student.grade}°)`;
        select.appendChild(option);
        if (gradeSelect && gradeSelect.value !== 'all' && String(student.grade) !== String(gradeSelect.value)) {
            option.hidden = true;
        }
    }

    if (addStudentBtn) {
        addStudentBtn.addEventListener('click', async () => {
            const firstName = newFirstName.value.trim();
            const lastName = newLastName.value.trim();
            const grade = gradeFilter.value;
            if (!firstName || !lastName) {
                alert('Ingresa nombre y apellido para agregar el estudiante.');
                return;
            }

            addStudentBtn.disabled = true;
            try {
                const response = await fetch('/teacher/api/students', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({first_name: firstName, last_name: lastName, grade: parseInt(grade, 10)}),
                });
                const data = await response.json();
                if (!response.ok || !data.success) {
                    alert(data.error || 'No se pudo agregar el estudiante.');
                    return;
                }
                appendStudentRow(data.student);
                newFirstName.value = '';
                newLastName.value = '';
                filterStudents();
                alert('Estudiante agregado y guardado en la base de datos.');
            } catch (error) {
                alert(`Error al agregar estudiante: ${error.message}`);
            } finally {
                addStudentBtn.disabled = false;
            }
        });
    }

    if (deleteStudentBtn) {
        deleteStudentBtn.addEventListener('click', async () => {
            if (!selectedRow) {
                alert('Selecciona un estudiante para eliminar.');
                return;
            }
            if (!confirm('¿Eliminar este estudiante? Esta acción no se puede deshacer.')) {
                return;
            }

            const studentId = selectedRow.dataset.id;
            deleteStudentBtn.disabled = true;
            try {
                const response = await fetch(`/teacher/api/students/${studentId}`, {method: 'DELETE'});
                const data = await response.json();
                if (!response.ok || !data.success) {
                    alert(data.error || 'No se pudo eliminar el estudiante.');
                    return;
                }
                selectedRow.remove();
                if (messageStudentSelect) {
                    const option = messageStudentSelect.querySelector(`option[value="${studentId}"]`);
                    option?.remove();
                }
                clearSelection();
                alert('Estudiante eliminado de la base de datos.');
            } catch (error) {
                alert(`Error al eliminar estudiante: ${error.message}`);
            } finally {
                deleteStudentBtn.disabled = false;
            }
        });
    }

    if (saveObservationsBtn) {
        saveObservationsBtn.addEventListener('click', async () => {
            if (!selectedRow) {
                alert('Selecciona un estudiante para guardar sus observaciones.');
                return;
            }

            const studentId = selectedRow.dataset.id;
            const observations = obsBox.value.trim();
            saveObservationsBtn.disabled = true;
            try {
                const response = await fetch(`/teacher/api/students/${studentId}/observations`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({observations}),
                });
                const data = await response.json();
                if (!response.ok || !data.success) {
                    alert(data.error || 'No se pudieron guardar las observaciones.');
                    return;
                }
                selectedRow.dataset.observations = observations;
                selectedRow.querySelector('td:nth-child(4)').textContent = observations;
                const selectedNotesObservations = document.getElementById('selected-student-notes');
                if (selectedNotesObservations) {
                    selectedNotesObservations.textContent = observations || '—';
                }
                alert('Observaciones guardadas en la base de datos.');
            } catch (error) {
                alert(`Error al guardar observaciones: ${error.message}`);
            } finally {
                saveObservationsBtn.disabled = false;
            }
        });
    }

    const notesGrade = document.getElementById('notes-grade');
    notesStudentName = document.getElementById('notes-student-name');
    selectedStudentScore = document.getElementById('selected-student-score');
    selectedStudentGrade = document.getElementById('selected-student-grade');
    selectedStudentNotes = document.getElementById('selected-student-notes');
    const notesStudentsTable = document.getElementById('notes-students-table');
    activityType = document.getElementById('activity-type');
    notesDateFrom = document.getElementById('notes-date-from');
    notesDateTo = document.getElementById('notes-date-to');
    const filterNotesBtn = document.getElementById('btn-filter-notes');
    notesResultsTable = document.getElementById('notes-results-table');

    async function loadNotesResults() {
        if (!notesResultsTable) return;
        if (!selectedNotesRow) {
            notesResultsTable.innerHTML = '<tr><td colspan="5" class="text-muted">Selecciona un alumno y consulta sus notas.</td></tr>';
            return;
        }
        notesResultsTable.innerHTML = '<tr><td colspan="5" class="text-muted">Cargando notas...</td></tr>';
        const response = await fetch('/teacher/api/notes/summary', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                student_id: selectedNotesRow.dataset.id,
                activity_type: activityType?.value || '',
                date_from: notesDateFrom?.value || '',
                date_to: notesDateTo?.value || '',
            }),
        });
        const data = await response.json();
        const results = data.results || [];
        const average = results.length
            ? results.reduce((total, result) => total + Number(result.score || 0), 0) / results.length
            : 0;
        const score = Math.round(average * 100) / 100;
        selectedNotesRow.dataset.score = String(score);
        if (selectedStudentScore) selectedStudentScore.textContent = String(score);
        const noteCell = selectedNotesRow.querySelector('.student-note-cell span');
        if (noteCell) noteCell.textContent = String(score);
        updateStatusDisplay(score);
        updatePrediction(selectedNotesRow.dataset.name || '', score);
        if (!results.length) {
            notesResultsTable.innerHTML = '<tr><td colspan="5" class="text-muted">No hay resultados en el rango seleccionado.</td></tr>';
            return;
        }
        notesResultsTable.innerHTML = results.map(result => `
            <tr>
                <td>${result.created_at ? new Date(result.created_at).toLocaleString('es-PE') : 'Sin fecha'}</td>
                <td>${result.topic || 'General'}</td>
                <td>${result.activity_type || ''}</td>
                <td><strong>${result.score}/20</strong></td>
                <td>${result.correct_answers || 0} correctas, ${result.wrong_answers || 0} incorrectas</td>
            </tr>
        `).join('');
    }

    function refreshNotesTable() {
        const grade = notesGrade ? notesGrade.value : '5';
        document.querySelectorAll('.notes-student-row').forEach(row => {
            row.style.display = row.dataset.grade === grade ? '' : 'none';
        });
        selectedNotesRow = null;
        if (notesStudentName) notesStudentName.value = '';
        if (selectedStudentScore) selectedStudentScore.textContent = '0';
        if (selectedStudentGrade) selectedStudentGrade.textContent = `${grade}°`;
        if (selectedStudentNotes) selectedStudentNotes.textContent = '—';
        const aiBox = document.getElementById('ai-prediction');
        if (aiBox) {
            aiBox.querySelector('.prediction-text').textContent = 'Selecciona un alumno para generar la predicción.';
        }
    }

    if (notesGrade) {
        notesGrade.addEventListener('change', () => {
            refreshNotesTable();
        });
    }

    function selectNotesStudent(row) {
        if (!row) return;
        if (notesStudentName) notesStudentName.value = row.dataset.name || '';
        selectedNotesRow = row;
        document.querySelectorAll('.notes-student-row').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');

        const score = parseFloat(row.dataset.score || '0');

        if (selectedStudentScore) selectedStudentScore.textContent = `${score}`;
        if (selectedStudentGrade) selectedStudentGrade.textContent = `${row.dataset.grade || '0'}°`;
        if (selectedStudentNotes) selectedStudentNotes.textContent = row.dataset.observations || '—';
        const noteCell = row.querySelector('.student-note-cell span');
        if (noteCell) {
            noteCell.textContent = `${score}`;
        }
        updateStatusDisplay(score);
        updatePrediction(row.dataset.name || '', score);
        loadNotesResults();
        console.log('selectNotesStudent', row.dataset.name, score, activityType ? activityType.value : null);
    }

    function updateStatusDisplay(score) {
        updateStatusAvatar(score, false);
    }

    function updateStatusAvatar(value, isPercent) {
        if (!selectedStudentImage) return;
        const status = isPercent ? getStatusAvatarForProgress(value) : getStatusAvatarForScore(value);
        selectedStudentImage.textContent = status.icon;
        selectedStudentImage.style.background = status.bg;
        selectedStudentImage.style.color = status.color;
        if (selectedStudentStatus) {
            selectedStudentStatus.textContent = status.label;
        }
        if (selectedStudentStatusDesc) {
            selectedStudentStatusDesc.textContent = isPercent ? `Progreso actual: ${value}%` : `Nota actual: ${value} / 20`;
        }
    }

    function resetStatusAvatar() {
        if (!selectedStudentImage) return;
        selectedStudentImage.textContent = '?';
        selectedStudentImage.style.background = '#e2e8f0';
        selectedStudentImage.style.color = '#717d7d';
        if (selectedStudentStatus) {
            selectedStudentStatus.textContent = 'Selecciona un alumno';
        }
        if (selectedStudentStatusDesc) {
            selectedStudentStatusDesc.textContent = 'Aquí verás una imagen según su progreso.';
        }
    }

    function getStatusAvatarForProgress(progress) {
        if (progress >= 80) {
            return { icon: '✓', bg: '#34d399', color: '#fff', label: 'Progreso excelente' };
        }
        if (progress >= 50) {
            return { icon: '!', bg: '#facc15', color: '#000', label: 'Progreso moderado' };
        }
        return { icon: '!', bg: '#f87171', color: '#fff', label: 'Progreso bajo' };
    }

    function getStatusAvatarForScore(score) {
        if (score >= 16) {
            return { icon: '✓', bg: '#34d399', color: '#fff', label: 'Desempeño excelente' };
        }
        if (score >= 10) {
            return { icon: '!', bg: '#facc15', color: '#000', label: 'Desempeño moderado' };
        }
        return { icon: '!', bg: '#f87171', color: '#fff', label: 'Desempeño bajo' };
    }

    function calculateScoreFromActivity(baseScore) {
        if (!activityType) return baseScore;
        switch (activityType.value) {
            case 'actividades':
                return Math.min(20, baseScore + 1);
            case 'juegos':
                return Math.min(20, baseScore + 1);
            case 'evaluaciones':
                return Math.min(20, baseScore + 2);
            default:
                return baseScore;
        }
    }

    if (notesStudentsTable) {
        notesStudentsTable.querySelectorAll('.notes-student-row').forEach(row => {
            row.addEventListener('click', event => {
                if (event.target.closest('.btn-select-notes-student')) return;
                selectNotesStudent(row);
            });
            const btn = row.querySelector('.btn-select-notes-student');
            if (btn) {
                btn.addEventListener('click', event => {
                    event.stopPropagation();
                    selectNotesStudent(row);
                });
            }
        });
    }

    if (activityType) {
        activityType.addEventListener('change', () => {
            if (selectedNotesRow) {
                selectNotesStudent(selectedNotesRow);
            } else {
                const aiBox = document.getElementById('ai-prediction');
                if (aiBox) {
                    aiBox.querySelector('.prediction-text').textContent = 'Selecciona un alumno antes de escoger el tipo de actividad.';
                    const levelBadge = document.getElementById('prediction-level');
                    if (levelBadge) {
                        levelBadge.textContent = 'Pendiente';
                        levelBadge.style.background = '#dbeafe';
                        levelBadge.style.color = '#1d4ed8';
                    }
                }
            }
        });
    }

    const generateAiPredictionBtn = document.getElementById('btn-generate-ai-prediction');
    if (generateAiPredictionBtn) {
        generateAiPredictionBtn.addEventListener('click', async () => {
            if (selectedNotesRow) {
                const score = Number(selectedNotesRow.dataset.score || 0);
                await updatePrediction(selectedNotesRow.dataset.name || '', score);
            } else {
                const aiBox = document.getElementById('ai-prediction');
                if (aiBox) {
                    aiBox.querySelector('.prediction-text').textContent = 'Primero selecciona un alumno para generar la predicción.';
                }
            }
        });
    }

    if (filterNotesBtn) filterNotesBtn.addEventListener('click', loadNotesResults);
    [notesDateFrom, notesDateTo].forEach(input => input?.addEventListener('change', loadNotesResults));

    window.updatePrediction = updatePrediction;
    window.loadNotesResults = loadNotesResults;
    window.updateStatusDisplay = updateStatusDisplay;
    window.selectedNotesRow = selectedNotesRow;

    const messageStudentSelect = document.getElementById('message-student-select');
    const messageGradeSelect = document.getElementById('message-grade-select');
    const messageComposeBox = document.getElementById('message-compose-box');
    const messageStudentInfo = document.getElementById('message-student-info');
    const messageText = document.getElementById('message-text');
    const btnSendMessage = document.getElementById('btn-send-message');
    const btnClearMessage = document.getElementById('btn-clear-message');
    const charCount = document.getElementById('char-count');
    const messagesHistory = document.getElementById('messages-history');
    const messageFeedback = document.getElementById('message-feedback');

    const registeredMessageStudents = messageStudentSelect
        ? Array.from(messageStudentSelect.querySelectorAll('option[data-grade]')).map(option => ({
            id: option.value,
            name: option.dataset.name || '',
            grade: String(option.dataset.grade || ''),
            label: option.textContent.trim(),
        }))
        : [];

    function refreshMessageStudentOptions() {
        if (!messageStudentSelect) return;
        const selectedGrade = messageGradeSelect ? String(messageGradeSelect.value) : 'all';
        const currentValue = messageStudentSelect.value;
        const visibleStudents = registeredMessageStudents.filter(student =>
            selectedGrade === 'all' || student.grade === selectedGrade
        );

        messageStudentSelect.replaceChildren();
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = visibleStudents.length
            ? '\u2014 Seleccionar un estudiante \u2014'
            : (selectedGrade === 'all'
                ? 'No hay alumnos registrados'
                : 'No hay alumnos registrados en este grado');
        messageStudentSelect.appendChild(placeholder);

        visibleStudents.forEach(student => {
            const option = document.createElement('option');
            option.value = student.id;
            option.dataset.name = student.name;
            option.dataset.grade = student.grade;
            option.textContent = student.label;
            messageStudentSelect.appendChild(option);
        });

        const selectionStillVisible = currentValue
            && visibleStudents.some(student => student.id === currentValue);
        messageStudentSelect.value = selectionStillVisible ? currentValue : '';

        if (messageStudentSelect.value) {
            messageStudentSelect.dispatchEvent(new Event('change'));
        } else {
            if (messageComposeBox) messageComposeBox.style.display = 'none';
            if (messageStudentInfo) messageStudentInfo.style.display = 'none';
            if (messagesHistory) {
                messagesHistory.innerHTML = '<p class="text-muted text-center">Selecciona un estudiante para ver el historial de mensajes</p>';
            }
        }
    }

    if (messageGradeSelect) {
        messageGradeSelect.addEventListener('change', refreshMessageStudentOptions);
    }

    if (messageStudentSelect) {
        messageStudentSelect.addEventListener('change', () => {
            if (messageStudentSelect.value) {
                messageComposeBox.style.display = 'block';
                messageStudentInfo.style.display = 'block';
                const selectedOption = messageStudentSelect.options[messageStudentSelect.selectedIndex];
                document.getElementById('message-student-name').textContent = selectedOption.dataset.name || 'Estudiante';
                document.getElementById('message-student-grade').textContent = `Grado: ${selectedOption.dataset.grade || '—'}`;
                messagesHistory.innerHTML = '<p class="text-muted text-center">Cargando historial...</p>';
                loadMessagesHistory();
            } else {
                messageComposeBox.style.display = 'none';
                messageStudentInfo.style.display = 'none';
                messagesHistory.innerHTML = '<p class="text-muted text-center">Selecciona un estudiante para ver el historial de mensajes</p>';
            }
        });
    }

    if (messageGradeSelect) {
        refreshMessageStudentOptions();
    }

    if (messageText) {
        messageText.addEventListener('input', () => {
            charCount.textContent = messageText.value.length;
        });
    }

    if (btnClearMessage) {
        btnClearMessage.addEventListener('click', () => {
            messageText.value = '';
            charCount.textContent = '0';
            messageFeedback.style.display = 'none';
        });
    }

    if (btnSendMessage) {
        btnSendMessage.addEventListener('click', async () => {
            const studentId = messageStudentSelect.value;
            const message = messageText.value.trim();

            if (!studentId) {
                alert('Por favor selecciona un estudiante');
                return;
            }

            if (!message) {
                alert('Por favor escribe un mensaje');
                return;
            }

            try {
                btnSendMessage.disabled = true;
                btnSendMessage.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';

                const response = await fetch('/teacher/api/send-message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ student_id: studentId, message: message })
                });

                const data = await response.json();

                if (data.success) {
                    messageFeedback.style.display = 'block';
                    messageFeedback.innerHTML = '<div class="alert alert-success alert-dismissible fade show"><i class="bi bi-check-circle"></i> Mensaje enviado correctamente</div>';
                    messageText.value = '';
                    charCount.textContent = '0';
                    loadMessagesHistory();
                    setTimeout(() => {
                        messageFeedback.style.display = 'none';
                    }, 3000);
                } else {
                    messageFeedback.style.display = 'block';
                    messageFeedback.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> ${data.error}</div>`;
                }
            } catch (error) {
                messageFeedback.style.display = 'block';
                messageFeedback.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> Error: ${error.message}</div>`;
            } finally {
                btnSendMessage.disabled = false;
                btnSendMessage.innerHTML = '<i class="bi bi-send"></i> Enviar mensaje';
            }
        });
    }

    async function loadMessagesHistory() {
        const studentId = messageStudentSelect.value;
        if (!studentId) return;

        try {
            const response = await fetch(`/teacher/api/messages/${studentId}`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });
            const data = await response.json();

            if (data.success && data.messages && data.messages.length > 0) {
                messagesHistory.innerHTML = data.messages.map(msg => `
                    <div class="message-item alert ${msg.is_read ? 'alert-success' : 'alert-info'} mb-2">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <p class="mb-1"><strong>${msg.message}</strong></p>
                                <small class="text-muted">${new Date(msg.created_at).toLocaleString('es-ES')}</small>
                            </div>
                            <div class="d-flex align-items-center gap-2">
                                <span class="badge ${msg.is_read ? 'bg-success' : 'bg-warning'}">
                                    ${msg.is_read ? 'Leído' : 'No leído'}
                                </span>
                                <button type="button" class="btn btn-sm btn-outline-danger btn-delete-message" data-message-id="${msg.id}" title="Eliminar mensaje"><i class="bi bi-trash"></i> Eliminar</button>
                            </div>
                        </div>
                    </div>
                `).join('');
                messagesHistory.querySelectorAll('.btn-delete-message').forEach(button => {
                    button.addEventListener('click', async () => {
                        if (!window.confirm('¿Eliminar este mensaje del historial?')) return;
                        const response = await fetch(`/teacher/api/messages/${button.dataset.messageId}`, { method: 'DELETE' });
                        const result = await response.json();
                        if (result.success) loadMessagesHistory();
                        else alert(result.error || 'No se pudo eliminar el mensaje');
                    });
                });
            } else {
                messagesHistory.innerHTML = '<p class="text-muted text-center">No hay mensajes registrados para este estudiante</p>';
            }
        } catch (error) {
            messagesHistory.innerHTML = '<p class="text-danger text-center">Error al cargar mensajes</p>';
        }
    }

    const alertsModal = document.getElementById('alertsModal');
    if (alertsModal) {
        alertsModal.addEventListener('show.bs.modal', loadAllAlerts);
    }

    async function loadAllAlerts() {
        const listAll = document.getElementById('alerts-list-all');
        const listUnread = document.getElementById('alerts-list-unread');
        const listRead = document.getElementById('alerts-list-read');

        try {
            const [responseAll, responseUnread, responseReadMessages] = await Promise.all([
                fetch('/teacher/api/alerts?unread_only=false'),
                fetch('/teacher/api/alerts?unread_only=true'),
                fetch('/teacher/api/read-messages')
            ]);

            const dataAll = await responseAll.json();
            const dataUnread = await responseUnread.json();
            const dataReadMessages = await responseReadMessages.json();
            const allAlerts = [
                ...(dataAll.alerts || []),
                ...(dataReadMessages.alerts || [])
            ].sort((left, right) => new Date(right.created_at) - new Date(left.created_at));

            if (dataAll.success && dataReadMessages.success) {
                listAll.innerHTML = renderAlerts(allAlerts);
            } else {
                listAll.innerHTML = '<p class="text-muted text-center">No hay alertas</p>';
            }

            if (dataUnread.success && dataUnread.alerts) {
                listUnread.innerHTML = renderAlerts(dataUnread.alerts);
            } else {
                listUnread.innerHTML = '<p class="text-muted text-center">No hay alertas no leídas</p>';
            }
            if (listRead) {
                listRead.innerHTML = renderAlerts(dataReadMessages.alerts || [], true);
                listRead.querySelectorAll('.btn-delete-read-message').forEach(button => {
                    button.addEventListener('click', async () => {
                        if (!window.confirm('¿Eliminar este mensaje leído?')) return;
                        const response = await fetch(`/teacher/api/messages/${button.dataset.messageId}`, {method: 'DELETE'});
                        const result = await response.json();
                        if (result.success) loadAllAlerts();
                        else window.alert(result.error || 'No se pudo eliminar el mensaje');
                    });
                });
            }
        } catch (error) {
            listAll.innerHTML = '<p class="text-danger">Error al cargar alertas</p>';
            listUnread.innerHTML = '<p class="text-danger">Error al cargar alertas</p>';
        }
    }

    function renderAlerts(alerts, allowMessageDelete = false) {
        if (!alerts || alerts.length === 0) {
            return '<p class="text-muted text-center">No hay alertas</p>';
        }

        return alerts.map(alert => {
            const icon = {
                'success': '<i class="bi bi-check-circle text-success"></i>',
                'warning': '<i class="bi bi-exclamation-circle text-warning"></i>',
                'error': '<i class="bi bi-x-circle text-danger"></i>',
                'info': '<i class="bi bi-info-circle text-info"></i>'
            }[alert.alert_type] || '<i class="bi bi-info-circle"></i>';

            const alertClass = alert.source === 'message'
                ? 'alert-success'
                : (alert.is_read ? 'alert-light' : 'alert-' + (alert.alert_type === 'error' ? 'danger' : alert.alert_type));
            return `
                <div class="alert ${alertClass} alert-dismissible fade show mb-2">
                    <div class="d-flex align-items-start gap-2">
                        ${icon}
                        <div class="flex-grow-1">
                            <strong>${alert.title}</strong>
                            <p class="mb-1">${alert.description}</p>
                            <small class="text-muted">${new Date(alert.created_at).toLocaleString('es-ES')}</small>
                        </div>
                        ${allowMessageDelete && alert.source === 'message' ? `<button type="button" class="btn btn-sm btn-outline-danger btn-delete-read-message" data-message-id="${alert.id}" title="Eliminar mensaje leído"><i class="bi bi-trash"></i> Eliminar</button>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    refreshNotesTable();

    const gradeChips = document.querySelectorAll('.grade-chip[data-grade]');
    let selectedSessionFilter = null;

    function materialFilterParams() {
        const params = new URLSearchParams();
        const grade = document.querySelector('.grade-chip[data-grade].active')?.dataset.grade;
        const unit = document.querySelector('.btn-unit-chip.active')?.dataset.unit;
        if (grade) params.set('grade', grade);
        if (unit && unit !== 'all') params.set('unit', unit);
        if (selectedSessionFilter) params.set('session_number', String(selectedSessionFilter));
        return params;
    }

    function applyTopicFilters() {
        const grade = document.querySelector('.grade-chip[data-grade].active')?.dataset.grade || '5';
        const unit = document.querySelector('.btn-unit-chip.active')?.dataset.unit || 'all';
        document.querySelectorAll('.topic-item').forEach(item => {
            const session = Number(item.dataset.session || 0);
            const itemUnit = Number(item.dataset.unit || (session ? Math.ceil(session / 4) : 0));
            const matchesUnit = unit === 'all' || itemUnit === Number(unit);
            const matchesSession = !selectedSessionFilter || session === selectedSessionFilter;
            item.style.display = item.dataset.grade === String(grade)
                && matchesUnit && matchesSession ? '' : 'none';
        });
        attachTopicPreviewHandlers();
    }

    function refreshFilteredResourceLists() {
        if (typeof loadTeacherAssessments === 'function') loadTeacherAssessments();
        if (typeof loadTeacherAiGames === 'function') loadTeacherAiGames();
    }

    gradeChips.forEach(chip => {
        chip.addEventListener('click', () => {
            gradeChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const selectedGrade = Number(chip.dataset.grade || 5);
            const activeUnit = document.querySelector('.btn-unit-chip.active')?.dataset.unit || 'all';
            renderSessionWeeksForUnit(activeUnit, selectedGrade);
            applyTopicFilters();
            refreshFilteredResourceLists();
        });
    });

    function attachTopicPreviewHandlers() {
        document.querySelectorAll('.btn-preview').forEach(btn => {
            if (btn._previewHandler) {
                btn.removeEventListener('click', btn._previewHandler);
            }
            const handler = async () => {
                const title = btn.dataset.title;
                const grade = btn.dataset.grade || 5;
                const previewArea = btn.closest('.topic-card').querySelector('.topic-preview');
                if (!previewArea) return;
                previewArea.style.display = 'block';
                previewArea.textContent = 'Generando previsualización...';
                try {
                    const res = await fetch('/teacher/api/generate-preview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ topic: title, grade: grade })
                    });
                    const data = await res.json();
                    previewArea.innerHTML = `<div class="panel-card p-2"><strong>Previsualización (${data.grade}°):</strong>${renderMarkdownText(data.description || '')}<h6 class="mt-2">Preguntas del tema</h6>${renderGeneratedQuestions(data.preguntas)}<small class="text-muted">Generado con IA a partir del título escrito</small></div>`;
                } catch (err) {
                    previewArea.textContent = 'Error al generar la previsualización.';
                }
            };
            btn._previewHandler = handler;
            btn.addEventListener('click', handler);
        });

        document.querySelectorAll('.btn-delete-topic').forEach(btn => {
            if (btn._deleteTopicHandler) {
                btn.removeEventListener('click', btn._deleteTopicHandler);
            }
            const handler = async () => {
                const card = btn.closest('.topic-card');
                const topicId = card?.dataset.topicId;
                if (!topicId) return;
                const confirmed = confirm('¿Deseas eliminar este tema?');
                if (!confirmed) return;
                try {
                    await fetch(`/teacher/api/topic/${topicId}`, { method: 'DELETE' });
                    if (card) card.remove();
                } catch (err) {
                    alert('No se pudo eliminar el tema.');
                }
            };
            btn._deleteTopicHandler = handler;
            btn.addEventListener('click', handler);
        });

        document.querySelectorAll('.public-toggle').forEach(toggle => {
            if (toggle._publicToggleHandler) {
                toggle.removeEventListener('change', toggle._publicToggleHandler);
            }
            const handler = async () => {
                const card = toggle.closest('.topic-card');
                const topicId = card?.dataset.topicId;
                const badge = card?.querySelector('.badge-status');
                const label = toggle.closest('.topic-visibility-toggle')?.querySelector('span');
                if (!topicId) return;
                const nextStatus = toggle.checked ? 'Publicado' : 'Privado';
                try {
                    const resp = await fetch(`/teacher/api/topic/${topicId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: nextStatus })
                    });
                    const data = await resp.json();
                    if (badge && data.topic) {
                        badge.textContent = data.topic.status === 'Publicado' ? 'Publicado' : 'Privado';
                        badge.className = data.topic.status === 'Publicado' ? 'badge-status badge-completado' : 'badge-status badge-pendiente';
                    }
                    if (label) label.textContent = toggle.checked ? 'Público' : 'Privado';
                } catch (err) {
                    toggle.checked = !toggle.checked;
                    if (label) label.textContent = toggle.checked ? 'Público' : 'Privado';
                    alert('No se pudo cambiar el estado público.');
                }
            };
            toggle._publicToggleHandler = handler;
            toggle.addEventListener('change', handler);
        });

        document.querySelectorAll('.btn-edit-topic').forEach(btn => {
            if (btn._editTopicHandler) {
                btn.removeEventListener('click', btn._editTopicHandler);
            }
            const handler = async () => {
                const card = btn.closest('.topic-card');
                const topicId = card?.dataset.topicId;
                const title = card?.querySelector('.topic-info h5');
                if (!topicId || !title) return;
                const input = prompt('Editar título del tema:', title.textContent.trim());
                if (!input) return;
                try {
                    const resp = await fetch(`/teacher/api/topic/${topicId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title: input.trim() })
                    });
                    const data = await resp.json();
                    if (data.topic && title) {
                        title.textContent = data.topic.title || input.trim();
                    }
                } catch (err) {
                    title.textContent = input.trim();
                }
            };
            btn._editTopicHandler = handler;
            btn.addEventListener('click', handler);
        });
    }

    const activeChip = document.querySelector('.grade-chip[data-grade].active');
    if (activeChip) applyTopicFilters();

    document.querySelectorAll('.btn-add-material').forEach(button => {
        button.addEventListener('click', async () => {
            const topicId = button.dataset.topicId;
            const title = prompt('Título del material:');
            if (!title) return;
            const materialType = prompt('Tipo: texto, imagen, video, presentacion o documento', 'texto');
            const content = prompt('Contenido o explicación (opcional):', '') || '';
            const response = await fetch(`/teacher/api/topic/${topicId}/materials`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, material_type: materialType, content})
            });
            const data = await response.json();
            if (!data.success) alert(data.error || 'No se pudo guardar el material.');
            else {
                alert('Material guardado correctamente.');
                loadTopicResources(document.querySelector(`.topic-resources[data-topic-id="${topicId}"]`));
            }
        });
    });

    const uploadModalElement = document.getElementById('uploadPptModal');
    const uploadModal = uploadModalElement && bootstrap.Modal.getOrCreateInstance(uploadModalElement);
    const topicDetailBackdrop = document.getElementById('topic-detail-backdrop');
    const topicDetailTitle = document.getElementById('topic-detail-title');
    const topicDetailClose = document.getElementById('topic-detail-close');
    const topicDetailUpload = document.getElementById('topic-detail-upload');
    const topicDetailEvaluation = document.getElementById('topic-detail-evaluation');
    const topicDetailGame = document.getElementById('topic-detail-game');
    const topicDetailPresentations = document.getElementById('topic-detail-presentations');
    const topicDetailEvaluationContent = document.getElementById('topic-detail-evaluation-content');
    const topicDetailGameContent = document.getElementById('topic-detail-game-content');
    let activeTopicDetailId = null;

    function openTopicDetailPanel(topicId, topicTitle) {
        activeTopicDetailId = topicId;
        if (topicDetailTitle) topicDetailTitle.textContent = topicTitle || 'Detalle del tema';
        if (topicDetailBackdrop) {
            topicDetailBackdrop.classList.add('is-open');
            topicDetailBackdrop.classList.remove('d-none');
            topicDetailBackdrop.setAttribute('aria-hidden', 'false');
            topicDetailBackdrop.style.display = 'flex';
        }
        if (topicDetailPresentations) {
            topicDetailPresentations.dataset.topicId = topicId;
            loadTopicPresentations(topicDetailPresentations);
        }
        if (topicDetailEvaluationContent) {
            topicDetailEvaluationContent.innerHTML = '<p class="topic-detail-empty">Cargando evaluación...</p>';
        }
        if (topicDetailGameContent) {
            topicDetailGameContent.innerHTML = '<p class="topic-detail-empty">Cargando juego...</p>';
        }
        if (topicId) {
            fetch(`/teacher/api/topic/${topicId}/learning-items`)
                .then(response => response.json())
                .then(data => {
                    const items = data.items || {};
                    const questions = items.evaluations?.flatMap((item) => item.questions || []) || [];
                    const game = items.games?.[0];
                    if (topicDetailEvaluationContent) {
                        if (questions.length) {
                            topicDetailEvaluationContent.innerHTML = renderGeneratedQuestions(questions);
                        } else {
                            topicDetailEvaluationContent.innerHTML = '<p class="topic-detail-empty">Todavía no hay evaluación generada para este tema.</p>';
                        }
                    }
                    if (topicDetailGameContent) {
                        if (game) {
                            topicDetailGameContent.innerHTML = `<div class="auto-content-box"><strong>${escapeText(game.name || 'Juego generado')}</strong><p class="small mb-2">${escapeText(game.description || game.rules || 'Juego generado para este tema.')}</p><p class="small text-muted mb-0">${escapeText(game.rules || 'Sin reglas adicionales.')}</p></div>`;
                        } else {
                            topicDetailGameContent.innerHTML = '<p class="topic-detail-empty">Todavía no hay un juego generado para este tema.</p>';
                        }
                    }
                })
                .catch(() => {
                    if (topicDetailEvaluationContent) topicDetailEvaluationContent.innerHTML = '<p class="topic-detail-empty">No se pudo cargar la evaluación.</p>';
                    if (topicDetailGameContent) topicDetailGameContent.innerHTML = '<p class="topic-detail-empty">No se pudo cargar el juego.</p>';
                });
        }
    }

    function closeTopicDetailPanel() {
        if (topicDetailBackdrop) {
            topicDetailBackdrop.classList.remove('is-open');
            topicDetailBackdrop.classList.add('d-none');
            topicDetailBackdrop.setAttribute('aria-hidden', 'true');
            topicDetailBackdrop.style.display = 'none';
        }
        activeTopicDetailId = null;
    }

    if (topicDetailClose) {
        topicDetailClose.addEventListener('click', closeTopicDetailPanel);
    }

    if (topicDetailBackdrop) {
        topicDetailBackdrop.addEventListener('click', event => {
            if (event.target === topicDetailBackdrop) closeTopicDetailPanel();
        });
    }

    document.querySelectorAll('.btn-open-topic-detail').forEach(button => {
        button.addEventListener('click', () => {
            openTopicDetailPanel(button.dataset.topicId, button.dataset.topicTitle);
        });
    });

    if (topicDetailUpload) {
        topicDetailUpload.addEventListener('click', () => {
            if (!activeTopicDetailId) return;
            const topic = (window.teacherTopics || []).find(item => String(item.id) === String(activeTopicDetailId)) || {};
            closeTopicDetailPanel();
            preparePresentationUpload({
                topicId: activeTopicDetailId,
                topicTitle: topicDetailTitle?.textContent || 'Tema',
                grade: topic.grade,
                sessionNumber: topic.session_number,
                section: topic.section,
            });
        });
    }

    if (topicDetailEvaluation) {
        topicDetailEvaluation.addEventListener('click', async () => {
            if (!activeTopicDetailId) return;
            if (topicDetailEvaluationContent) {
                topicDetailEvaluationContent.innerHTML = '<p class="topic-detail-empty">Generando evaluación...</p>';
            }
            try {
                const response = await fetch(`/teacher/api/topic/${activeTopicDetailId}/auto-content`, { method: 'POST' });
                const data = await response.json();
                const questions = data.preguntas || [];
                if (topicDetailEvaluationContent) {
                    topicDetailEvaluationContent.innerHTML = questions.length ? renderGeneratedQuestions(questions) : '<p class="topic-detail-empty">No se generó ninguna evaluación en este momento.</p>';
                }
            } catch (error) {
                if (topicDetailEvaluationContent) topicDetailEvaluationContent.innerHTML = '<p class="topic-detail-empty">No se pudo generar la evaluación.</p>';
            }
        });
    }

    if (topicDetailGame) {
        topicDetailGame.addEventListener('click', async () => {
            if (!activeTopicDetailId) return;
            if (topicDetailGameContent) {
                topicDetailGameContent.innerHTML = '<p class="topic-detail-empty">Generando juego...</p>';
            }
            try {
                const response = await fetch(`/ai/generar-juego/${activeTopicDetailId}`, { method: 'POST' });
                const data = await response.json();
                if (data.success && (data.juego || data.preguntas)) {
                    const game = data.juego || {};
                    if (topicDetailGameContent) {
                        topicDetailGameContent.innerHTML = `<div class="auto-content-box"><strong>${escapeText(game.titulo || 'Juego generado')}</strong><p class="small mb-2">${escapeText(game.instrucciones || 'Juego creado para este tema.')}</p><p class="small text-muted mb-0">${(game.pares || []).length} pares · ${(data.preguntas || []).length} preguntas</p></div>`;
                    }
                } else {
                    if (topicDetailGameContent) topicDetailGameContent.innerHTML = '<p class="topic-detail-empty">No se pudo generar el juego en este momento.</p>';
                }
            } catch (error) {
                if (topicDetailGameContent) topicDetailGameContent.innerHTML = '<p class="topic-detail-empty">No se pudo generar el juego.</p>';
            }
        });
    }

    function preparePresentationUpload({topicId, topicTitle, grade, sessionNumber, section}) {
        document.getElementById('upload-topic-id').value = topicId;
        document.getElementById('upload-grade').value = grade || '5';
        document.getElementById('upload-section').value = section || '';
        document.getElementById('upload-ppt-title').value = `Material - ${topicTitle || 'Sesión'}`;
        document.getElementById('upload-session-number').value = sessionNumber || '1';
        document.getElementById('upload-ppt-file').value = '';
        document.getElementById('selected-upload-file').textContent = 'Ningún archivo seleccionado';
        document.getElementById('upload-workflow-status').textContent = '';
        if (referenceEditorInput) {
            referenceEditorInput.textContent = '';
            updateReferenceWordCount();
        }
        uploadModal?.show();
    }

    document.querySelectorAll('.btn-upload-ppt').forEach(button => button.addEventListener('click', () => {
        preparePresentationUpload({
            topicId: button.dataset.topicId,
            topicTitle: button.dataset.topicTitle,
            grade: button.dataset.topicGrade,
            sessionNumber: button.dataset.sessionNumber,
            section: button.dataset.topicSection,
        });
    }));

    const uploadFile = document.getElementById('upload-ppt-file');
    const uploadZone = document.getElementById('drop-upload-zone');
    if (uploadFile && uploadZone) {
        const showFile = () => { document.getElementById('selected-upload-file').textContent = uploadFile.files[0] ? `Archivo seleccionado: ${uploadFile.files[0].name}` : 'Ningún archivo seleccionado'; };
        uploadFile.addEventListener('change', showFile);
        ['dragenter', 'dragover'].forEach(name => uploadZone.addEventListener(name, event => { event.preventDefault(); uploadZone.classList.add('border-primary', 'bg-light'); }));
        ['dragleave', 'drop'].forEach(name => uploadZone.addEventListener(name, event => { event.preventDefault(); uploadZone.classList.remove('border-primary', 'bg-light'); }));
        uploadZone.addEventListener('drop', event => { uploadFile.files = event.dataTransfer.files; showFile(); });
    }

    const referenceEditorInput = document.querySelector('.reference-editor-input');
    const referenceWordCount = document.getElementById('reference-word-count');
    function updateReferenceWordCount() {
        if (!referenceEditorInput || !referenceWordCount) return;
        const text = referenceEditorInput.textContent.replace(/\s+/g, ' ').trim();
        const count = text ? text.split(/\s+/).length : 0;
        referenceWordCount.textContent = `Recuento de palabras: ${count}`;
    }
    if (referenceEditorInput) {
        referenceEditorInput.addEventListener('input', updateReferenceWordCount);
        referenceEditorInput.addEventListener('focus', () => {
            referenceEditorInput.classList.add('is-focused');
        });
        referenceEditorInput.addEventListener('blur', () => {
            referenceEditorInput.classList.remove('is-focused');
        });
        updateReferenceWordCount();
    }

    const submitUpload = document.getElementById('btn-submit-upload');

    if (submitUpload) submitUpload.addEventListener('click', async () => {
        const file = uploadFile?.files[0];
        if (!file) return alert('Selecciona o arrastra un archivo.');
        const description = (referenceEditorInput?.textContent || '').replace(/\s+/g, ' ').trim();
        const topicId = document.getElementById('upload-topic-id').value;
        const grade = document.getElementById('upload-grade').value || '5';
        const sessionNumber = document.getElementById('upload-session-number').value || '1';
        const status = document.getElementById('upload-workflow-status');
        const formData = new FormData();
        formData.append('topic_id', topicId);
        formData.append('grade', String(grade));
        formData.append('section', document.getElementById('upload-section').value);
        formData.append('publish_to_students', String(document.getElementById('upload-publish-to-students').checked));
        formData.append('title', document.getElementById('upload-ppt-title').value);
        formData.append('session_number', sessionNumber);
        formData.append('description', description);
        formData.append('file', file);
        document.getElementById('upload-progress').style.display = 'block';
        submitUpload.disabled = true;
        if (status) status.textContent = 'Subiendo PPT para la sesión seleccionada...';
        try {
            const response = await fetch('/teacher/api/upload-presentation', {method: 'POST', body: formData});
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'No se pudo subir el archivo.');
            }

            await loadTopicPresentations(document.querySelector(`.topic-presentations[data-topic-id="${data.topic_id || topicId}"]`));
            if (status) {
                const publicationMessage = data.status === 'PUBLISHED'
                    ? 'El material y su descripción ya están publicados para los alumnos.'
                    : 'El material quedó como borrador. Publícalo desde la lista para que los alumnos puedan verlo.';
                const evaluationMessage = data.invalidated_assessments
                    ? ' La evaluación anterior quedó en revisión; genera una nueva basada en este PPT y publícala para tus alumnos.'
                    : '';
                status.innerHTML = `<div class="alert ${data.status === 'PUBLISHED' ? 'alert-success' : 'alert-warning'} py-2 mb-0">PPT cargado para grado ${escapeText(grade)}, sesión ${escapeText(sessionNumber)}. ${escapeText(publicationMessage + evaluationMessage)}</div>`;
            }
        } catch (error) {
            if (status) status.innerHTML = `<div class="alert alert-danger py-2 mb-0">${escapeText(error.message)}</div>`;
        } finally {
            document.getElementById('upload-progress').style.display = 'none';
            submitUpload.disabled = false;
        }
    });

    document.querySelectorAll('.btn-add-learning-item').forEach(button => {
        button.addEventListener('click', async () => {
            const topicId = button.dataset.topicId;
            const itemType = prompt('Tipo de contenido: activity, game o evaluation', 'activity');
            if (!itemType || !['activity', 'game', 'evaluation'].includes(itemType)) return;
            const payload = { item_type: itemType };
            if (itemType === 'activity') {
                payload.title = prompt('Título de la actividad:', 'Actividad práctica');
                payload.activity_type = prompt('Tipo: selección múltiple, verdadero/falso o práctica', 'práctica');
                payload.question = prompt('Pregunta:');
                payload.correct_answer = prompt('Respuesta correcta:');
                payload.options = [];
            } else if (itemType === 'game') {
                payload.name = prompt('Nombre del juego:');
                payload.description = prompt('Descripción:', '') || '';
                payload.rules = prompt('Reglas:', '') || '';
            } else {
                payload.difficulty = prompt('Dificultad: básica, media o alta', 'media');
                payload.questions = [{question: prompt('Pregunta de evaluación:'), answer: prompt('Respuesta esperada:')}];
            }
            if (!payload.title && !payload.name && !payload.questions?.[0]?.question) return;
            const response = await fetch(`/teacher/api/topic/${topicId}/learning-items`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
            });
            const data = await response.json();
            alert(data.success ? 'Contenido guardado correctamente.' : (data.error || 'No se pudo guardar.'));
        });
    });

    document.querySelectorAll('.topic-materials').forEach(container => loadTopicLearningItems(container));
    document.querySelectorAll('.topic-resources').forEach(container => loadTopicResources(container));

    async function loadTopicResources(container) {
        if (!container) return;
        const response = await fetch(`/teacher/api/topic/${container.dataset.topicId}/materials`);
        const data = await response.json();
        if (!data.success) return;
        const materials = data.materials || [];
        container.innerHTML = materials.length ? `<small class="text-muted d-block">Materiales del tema</small>${materials.map(material => `<div class="d-flex justify-content-between align-items-center border-top py-1 gap-2"><span class="small text-truncate"><i class="bi bi-file-text"></i> ${escapeText(material.title)}</span><button class="btn btn-sm btn-outline-primary prepare-practice" data-source="materials" data-id="${material.id}" type="button">Preparar práctica</button><button class="btn btn-sm btn-outline-danger delete-material" data-id="${material.id}">Eliminar</button></div>`).join('')}` : '<small class="text-muted">Sin materiales creados.</small>';
        container.querySelectorAll('.delete-material').forEach(button => button.addEventListener('click', async () => {
            if (!confirm('¿Eliminar este material?')) return;
            await fetch(`/teacher/api/materials/${button.dataset.id}`, {method: 'DELETE'});
            loadTopicResources(container);
        }));
    }

    function renderGeneratedQuestions(questions) {
        if (!questions || !questions.length) {
            return '<p class="text-muted small">Aún no hay preguntas generadas para este tema.</p>';
        }
        return `<div class="small mb-0">${questions.map(question => `
            <div class="generated-question-item">
                <strong>${escapeText(question.question || question.q || '')}</strong>
                <span class="text-muted">Respuesta: ${escapeText(question.answer || question.correct_answer || '')}</span>
            </div>
        `).join('')}</div>`;
    }

    function escapeText(value) {
        return String(value).replace(/[&<>'"]/g, character => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[character]));
    }

    function renderMarkdownText(markdown) {
        if (!markdown) return '<p class="text-muted mb-0">Sin contenido generado.</p>';
        const normalized = String(markdown).replace(/\r\n/g, '\n');
        const withEscapes = escapeText(normalized);
        const html = withEscapes
            .replace(/^### (.*)$/gm, '<h6>$1</h6>')
            .replace(/^## (.*)$/gm, '<h5>$1</h5>')
            .replace(/^# (.*)$/gm, '<h4>$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/^- (.*)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
            .replace(/\n/g, '<br>');
        return html;
    }

    document.querySelectorAll('.topic-presentations').forEach(container => loadTopicPresentations(container));

    async function loadTopicPresentations(container) {
        if (!container) return;
        const response = await fetch(`/teacher/api/presentations/${container.dataset.topicId}`);
        const data = await response.json();
        const files = data.presentations || [];
        const summary = container.closest('.topic-card')?.querySelector('.compact-file-box span');
        if (summary) {
            summary.innerHTML = `<i class="bi bi-file-earmark-text"></i> ${files.length ? `${files.length} archivo${files.length === 1 ? '' : 's'}` : 'Sin archivos'}`;
        }

        if (!files.length) {
            container.innerHTML = '<small class="text-muted">Sin PPT o documentos cargados.</small>';
            return;
        }

        const visibleFiles = files.slice(0, 2);
        const hiddenFiles = files.slice(2);

        const listHtml = files.map(file => `
            <div class="topic-material-row">
                <div class="material-name-wrap">
                    <span class="material-name"><i class="bi bi-file-earmark-text"></i> ${escapeText(file.title)}</span>
                    <span class="badge ${file.status === 'PUBLISHED' ? 'bg-success' : 'bg-warning text-dark'}">${file.status === 'PUBLISHED' ? 'Publicado para alumnos' : 'Borrador · Solo docente'}</span>
                    <div class="material-comment mt-1">
                        <span class="fw-semibold small text-secondary">Comentario:</span>
                        <span class="small text-dark">${escapeText(file.description || 'Sin comentario para esta sesión.')}</span>
                    </div>
                </div>
                <span class="material-actions">
                    <a class="btn-link-mini" href="/teacher/api/presentations/${file.id}/file" target="_blank" rel="noopener">Abrir</a>
                    <a class="btn-link-mini" href="/teacher/api/presentations/${file.id}/file" download>Descargar</a>
                    ${file.status !== 'PUBLISHED' ? `<button class="btn-link-mini btn-publish-mini publish-presentation" data-id="${file.id}" type="button"><i class="bi bi-send-check me-1"></i>Publicar a alumnos</button>` : ''}
                    <button class="btn-link-mini replace-presentation" data-topic-id="${file.topic_id}" data-session-number="${file.session_number}" type="button">Reemplazar</button>
                    <button class="btn-link-mini prepare-practice" data-source="presentations" data-id="${file.id}" type="button">Preparar práctica</button>
                    <button class="btn-danger-mini delete-presentation" data-id="${file.id}">Eliminar</button>
                </span>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="topic-material-summary">
                <span><i class="bi bi-folder2-open"></i> ${files.length} archivo${files.length > 1 ? 's' : ''} subido${files.length > 1 ? 's' : ''}</span>
                ${hiddenFiles.length ? `<button class="btn btn-sm btn-outline-secondary toggle-presentations" type="button">Más</button>` : ''}
            </div>
            <div class="topic-material-list" ${hiddenFiles.length ? 'style="display:none;"' : ''}>${listHtml}</div>
        `;

        const toggleButton = container.querySelector('.toggle-presentations');
        const materialsList = container.querySelector('.topic-material-list');
        if (toggleButton && materialsList) {
            toggleButton.addEventListener('click', () => {
                const isVisible = materialsList.style.display !== 'none';
                materialsList.style.display = isVisible ? 'none' : 'flex';
                toggleButton.textContent = isVisible ? 'Más' : 'Cerrar';
            });
        }

        container.querySelectorAll('.publish-presentation').forEach(button => button.addEventListener('click', async () => {
            button.disabled = true;
            try {
                const response = await fetch(`/teacher/api/presentations/${button.dataset.id}/publish`, {method: 'POST'});
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'No se pudo publicar la presentación.');
                await loadTopicPresentations(container);
            } catch (error) {
                button.disabled = false;
                alert(error.message);
            }
        }));

        container.querySelectorAll('.replace-presentation').forEach(button => button.addEventListener('click', () => {
            const topicId = button.dataset.topicId;
            const sessionNumber = button.dataset.sessionNumber;
            const uploadTopicInput = document.getElementById('upload-topic-id');
            const uploadSessionInput = document.getElementById('upload-session-number');
            const uploadTitleInput = document.getElementById('upload-ppt-title');
            if (uploadTopicInput) uploadTopicInput.value = topicId;
            if (uploadSessionInput) uploadSessionInput.value = sessionNumber;
            if (uploadTitleInput) uploadTitleInput.value = `Presentación - Sesión ${sessionNumber}`;
            const fileInput = document.getElementById('upload-ppt-file');
            if (fileInput) fileInput.value = '';
            document.getElementById('selected-upload-file').textContent = 'Selecciona el archivo nuevo para reemplazar esta sesión';
            uploadModal?.show();
        }));

        container.querySelectorAll('.delete-presentation').forEach(button => button.addEventListener('click', async () => {
            if (!confirm('¿Eliminar este archivo?')) return;
            await fetch(`/teacher/api/delete-presentation/${button.dataset.id}`, {method: 'DELETE'});
            loadTopicPresentations(container);
        }));
    }

    async function loadTopicLearningItems(container) {
        const response = await fetch(`/teacher/api/topic/${container.dataset.topicId}/learning-items`);
        const data = await response.json();
        if (!data.success) return;
        const items = data.items;
        const rows = [
            ...(items.activities || []).map(item => ({type: 'activity', id: item.id, label: `Actividad: ${item.title || item.question}`})),
            ...(items.games || []).map(item => ({type: 'game', id: item.id, label: `Juego: ${item.name}`})),
            ...(items.evaluations || []).map(item => ({type: 'evaluation', id: item.id, label: `Evaluación (${item.difficulty})`})),
        ];
        container.innerHTML = rows.length ? `<small class="text-muted">Contenido asignado</small>${rows.map(row => `<div class="d-flex justify-content-between align-items-center border-top py-1"><span>${row.label}</span><button class="btn btn-sm btn-outline-danger delete-learning-item" data-type="${row.type}" data-id="${row.id}">Eliminar</button></div>`).join('')}` : '<small class="text-muted">Sin actividades, juegos o evaluaciones asignados.</small>';
        container.querySelectorAll('.delete-learning-item').forEach(button => button.addEventListener('click', async () => {
            if (!confirm('¿Eliminar este contenido?')) return;
            await fetch(`/teacher/api/learning-items/${button.dataset.type}/${button.dataset.id}`, {method: 'DELETE'});
            loadTopicLearningItems(container);
        }));
    }

    async function updatePrediction(studentName, score) {
        const aiBox = document.getElementById('ai-prediction');
        if (!aiBox) return;
        const levelBadge = document.getElementById('prediction-level');
        const riskBadge = document.getElementById('prediction-risk');
        const recommendation = document.getElementById('prediction-recommendation');
        const type = activityType ? activityType.value : 'actividades';
        const resolvedStudentName = studentName || selectedNotesRow?.dataset?.name || 'Estudiante';
        const resolvedScore = Number.isFinite(Number(score)) ? Number(score) : Number(selectedNotesRow?.dataset?.score || 0);

        if (!selectedNotesRow && !studentName) {
            aiBox.querySelector('.prediction-text').textContent = 'Selecciona un alumno para generar la predicción.';
            if (riskBadge) riskBadge.textContent = 'Sin datos';
            if (recommendation) recommendation.textContent = 'El sistema mostrará una recomendación personalizada según el desempeño del estudiante.';
            if (levelBadge) {
                levelBadge.textContent = 'Sin datos';
                levelBadge.style.background = '#e2e8f0';
                levelBadge.style.color = '#334155';
            }
            return;
        }
        if (!type) {
            aiBox.querySelector('.prediction-text').textContent = 'Selecciona el tipo de actividad para ver la predicción.';
            if (riskBadge) riskBadge.textContent = 'Pendiente';
            if (recommendation) recommendation.textContent = 'Debes elegir una actividad para generar la recomendación de apoyo académico.';
            if (levelBadge) {
                levelBadge.textContent = 'Pendiente';
                levelBadge.style.background = '#dbeafe';
                levelBadge.style.color = '#1d4ed8';
            }
            return;
        }

        try {
            const rawStudentId = selectedNotesRow?.dataset?.id || selectedNotesRow?.dataset?.studentId;
            const studentId = rawStudentId ? Number(rawStudentId) : null;
            const response = await fetch('/teacher/api/predict-student', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: studentId,
                    student_name: resolvedStudentName,
                    score: resolvedScore,
                    activity_type: type,
                }),
            });
            const data = await response.json();
            const payload = data.payload || data;

            if (!payload.success || payload.code === 'MODEL_NOT_AVAILABLE' || payload.status === 'MODEL_NOT_AVAILABLE') {
                aiBox.querySelector('.prediction-text').textContent =
                    'Modelo predictivo aún no disponible — Requiere datos de entrenamiento del colegio.';
                if (recommendation) {
                    recommendation.textContent =
                        payload.message || 'El sistema está preparado para entrenar un modelo supervisado real en cuanto se cargue el dataset institucional.';
                }
                if (levelBadge) {
                    levelBadge.textContent = 'No disponible';
                    levelBadge.style.background = '#f1f5f9';
                    levelBadge.style.color = '#475569';
                }
                if (riskBadge) {
                    riskBadge.textContent = 'Sin modelo';
                    riskBadge.style.color = '#475569';
                }
                return;
            }

            const summary = payload.summary || payload.recommendation || `Predicción supervisada para ${resolvedStudentName}.`;
            aiBox.querySelector('.prediction-text').textContent = summary;
            if (recommendation) recommendation.textContent = payload.recommendation || 'Predicción generada por modelo supervisado.';

            const studentNameEl = document.getElementById('prediction-student-name');
            if (studentNameEl) studentNameEl.textContent = resolvedStudentName;

            const probEl = document.getElementById('prediction-prob');
            if (probEl) {
                probEl.textContent = (payload.risk_probability !== null && payload.risk_probability !== undefined)
                    ? `${Math.round(payload.risk_probability * 100)}%`
                    : '--%';
            }

            const factorsListEl = document.getElementById('prediction-factors-list');
            if (factorsListEl) {
                const factors = payload.main_factors || [];
                if (factors.length > 0) {
                    factorsListEl.innerHTML = factors.map(f => `<li class="mb-1 text-dark"><span class="text-danger fw-bold me-1">↓</span>${f}</li>`).join('');
                } else {
                    factorsListEl.innerHTML = '<li class="text-muted">• Desempeño académico estable dentro de los parámetros esperados.</li>';
                }
            }

            const modelNameEl = document.getElementById('prediction-model-name');
            if (modelNameEl && payload.model && payload.model.name) {
                modelNameEl.textContent = payload.model.name;
            }

            const isInst = payload.model && payload.model.dataset === 'institutional';
            const datasetBadgeEl = document.getElementById('prediction-dataset-badge');
            if (datasetBadgeEl) {
                datasetBadgeEl.textContent = isInst ? 'Institucional' : 'Benchmark';
                datasetBadgeEl.className = isInst ? 'badge bg-success' : 'badge bg-secondary';
            }

            const noticeTextEl = document.getElementById('prediction-notice-text');
            if (noticeTextEl) {
                noticeTextEl.textContent = isInst
                    ? 'Modelo institucional entrenado con datos históricos del colegio.'
                    : 'Este modelo actualmente usa dataset público. Para uso institucional requiere entrenamiento con datos históricos del colegio.';
            }

            const level = (payload.level || 'medio').toLowerCase();
            const levelStyles = {
                excelente: ['Bajo', '#dcfce7', '#166534'],
                bueno: ['Medio', '#fef3c7', '#92400e'],
                'necesita apoyo': ['Alto', '#fee2e2', '#991b1b'],
                bajo: ['Bajo', '#dcfce7', '#166534'],
                medio: ['Medio', '#fef3c7', '#92400e'],
                alto: ['Alto', '#fee2e2', '#991b1b'],
            };
            const chosen = levelStyles[level] || levelStyles.medio;
            if (levelBadge) {
                levelBadge.textContent = chosen[0];
                levelBadge.style.background = chosen[1];
                levelBadge.style.color = chosen[2];
            }
            if (riskBadge) {
                const risk = payload.risk_level || 'Medio';
                riskBadge.textContent = risk;
                riskBadge.style.color = risk === 'Bajo' ? '#166534' : risk === 'Medio' ? '#92400e' : '#991b1b';
            }
        } catch (error) {
            console.warn('No fue posible consultar el servicio de predicción de riesgo:', error);
            aiBox.querySelector('.prediction-text').textContent = 'Servicio de predicción no disponible temporalmente.';
            if (recommendation) recommendation.textContent = 'Verifique la conexión o contacte al administrador.';
            if (levelBadge) {
                levelBadge.textContent = 'Error';
                levelBadge.style.background = '#fee2e2';
                levelBadge.style.color = '#991b1b';
            }
            if (riskBadge) {
                riskBadge.textContent = 'Error';
                riskBadge.style.color = '#991b1b';
            }
        }
    }

    const generateBtn = document.getElementById('btn-generate-topic');
    const generatedPanelBackdrop = document.getElementById('generated-panel-backdrop');
    const generatedPanelClose = document.getElementById('generated-panel-close');

    function openGeneratedPanel() {
        if (generatedPanelBackdrop) {
            generatedPanelBackdrop.classList.add('is-open');
            generatedPanelBackdrop.classList.remove('d-none');
            generatedPanelBackdrop.setAttribute('aria-hidden', 'false');
            generatedPanelBackdrop.style.display = 'flex';
        }
    }

    function closeGeneratedPanel() {
        if (generatedPanelBackdrop) {
            generatedPanelBackdrop.classList.remove('is-open');
            generatedPanelBackdrop.classList.add('d-none');
            generatedPanelBackdrop.setAttribute('aria-hidden', 'true');
            generatedPanelBackdrop.style.display = 'none';
        }
    }

    if (generatedPanelClose) {
        generatedPanelClose.addEventListener('click', closeGeneratedPanel);
    }

    if (generatedPanelBackdrop) {
        generatedPanelBackdrop.addEventListener('click', (event) => {
            if (event.target === generatedPanelBackdrop) {
                closeGeneratedPanel();
            }
        });
    }

    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const topicInput = document.getElementById('topic-search');
            const gradeChip = document.querySelector('.grade-chip[data-grade].active');
            const grade = gradeChip ? gradeChip.dataset.grade : '5';
            const topic = topicInput ? topicInput.value.trim() : '';
            if (!topic) {
                alert('Ingresa un tema para generar contenido.');
                return;
            }
            const resultBox = document.getElementById('generated-content');
            if (resultBox) {
                openGeneratedPanel();
                resultBox.innerHTML = '<p class="text-muted"><i class="bi bi-hourglass-split"></i> Generando juego y preguntas del tema escrito. Puede tardar 30 a 90 segundos...</p>';
                try {
                    const resp = await fetch('/teacher/api/generate-topic', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ topic, grade: parseInt(grade) }),
                    });
                    const data = await resp.json();
                    const generatedTitle = data.title || topic;
                    const generatedDescription = data.description || data.content || 'Contenido generado.';
                    const generated = data.generated_content || {};
                    const questions = generated.questions || data.preguntas || [];
                    const generatedStatus = `${generated.activities || 0} actividades · ${generated.game ? '1 juego' : 'sin juego'} · ${questions.length} preguntas`;
                    resultBox.innerHTML = `<div class="d-flex justify-content-between align-items-center mb-2"><h6 class="mb-0">Contenido generado con IA</h6><span class="badge-status badge-completado">Hecho</span></div><p class="small text-success mb-2"><i class="bi bi-check-circle"></i> Generado: ${generatedStatus}</p><label class="form-label">Título editable</label><input id="generated-topic-title" class="form-control mb-2" value="${escapeHtml(generatedTitle)}"><label class="form-label">Descripción editable</label><textarea id="generated-topic-description" class="form-control mb-2" rows="4">${escapeHtml(generatedDescription)}</textarea><h6>Preguntas del tema</h6>${renderGeneratedQuestions(questions)}<button class="btn btn-success mt-3" id="btn-save-generated-topic" data-topic-id="${data.id || ''}"><i class="bi bi-check2"></i> Guardar cambios</button>`;
                    const saveButton = document.getElementById('btn-save-generated-topic');
                    if (saveButton) saveButton.addEventListener('click', () => saveGeneratedTopic(saveButton.dataset.topicId));
                } catch {
                    resultBox.innerHTML = `<div class="alert alert-danger">No se pudo generar el contenido.</div>`;
                }
            }
        });
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>'"]/g, character => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[character]));
    }

    async function saveGeneratedTopic(topicId) {
        const title = document.getElementById('generated-topic-title')?.value.trim();
        const description = document.getElementById('generated-topic-description')?.value.trim();
        if (!topicId || !title || !description) {
            alert('El título y la descripción son obligatorios.');
            return;
        }

        const response = await fetch(`/teacher/api/topic/${topicId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title, description, status: 'Completado'})
        });
        const data = await response.json();
        if (!data.success) {
            alert(data.error || 'No se pudieron guardar los cambios.');
            return;
        }

        const existingCard = document.querySelector(`.topic-item[data-topic-id="${topicId}"]`);
        if (existingCard) {
            const titleNode = existingCard.querySelector('.topic-info h5');
            const descNode = existingCard.querySelector('.topic-info p');
            if (titleNode) titleNode.textContent = title;
            if (descNode) descNode.textContent = description;
        }

        if (typeof closeGeneratedPanel === 'function') {
            closeGeneratedPanel();
        }

        alert('Tema guardado correctamente. Las demás tarjetas no se modificaron.');
    }

    // Manejador de Carga de PPT por Sesión (1 a 32)
    const pptForm = document.getElementById('ppt-upload-form');
    if (pptForm) {
        pptForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const sessionNum = document.getElementById('ppt-session-number').value;
            const title = document.getElementById('ppt-title-input').value.trim();
            const description = document.getElementById('ppt-activity-description').value.trim();
            const fileInput = document.getElementById('ppt-file-input');
            const alertBox = document.getElementById('ppt-upload-alert');
            const submitButton = document.getElementById('btn-submit-ppt');
            const selectedGrade = Number(document.querySelector('.grade-chip[data-grade].active')?.dataset.grade || 5);
            const selectedUnit = document.querySelector('.btn-unit-chip.active')?.dataset.unit || 'all';

            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Selecciona un archivo PPT/PDF.');
                return;
            }

            const formData = new FormData();
            formData.append('grade', String(selectedGrade));
            formData.append('unit', String(selectedUnit));
            formData.append('session_number', sessionNum);
            formData.append('section', document.getElementById('topic-section-filter')?.value || '');
            formData.append('publish_to_students', 'true');
            formData.append('title', title || `Presentación PPT - Sesión ${sessionNum}`);
            formData.append('description', description);
            formData.append('file', fileInput.files[0]);

            if (alertBox) {
                alertBox.hidden = false;
                alertBox.innerHTML = '<div class="alert alert-info py-2"><i class="bi bi-hourglass-split me-1"></i> Subiendo presentación PPT...</div>';
            }
            if (submitButton) submitButton.disabled = true;

            try {
                const response = await fetch('/teacher/api/upload-presentation', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json().catch(() => ({}));

                if (response.ok && data.success) {
                    if (alertBox) {
                        const evaluationMessage = data.invalidated_assessments
                            ? ' La evaluación anterior quedó en revisión; genera una nueva basada en este PPT y publícala.'
                            : '';
                        alertBox.innerHTML = `<div class="alert alert-success py-2"><i class="bi bi-check-circle-fill me-1"></i> PPT cargado y publicado para los alumnos en la Sesión ${sessionNum}.${escapeText(evaluationMessage)}</div>`;
                    }
                    pptForm.reset();
                    await loadTopicPresentations(document.querySelector(`.topic-presentations[data-topic-id="${data.topic_id}"]`));
                } else {
                    if (alertBox) {
                        alertBox.innerHTML = `<div class="alert alert-danger py-2"><i class="bi bi-exclamation-triangle-fill me-1"></i> ${data.error || 'Error al subir la presentación. Verifica el tipo de archivo y tu sesión.'}</div>`;
                    }
                }
            } catch (err) {
                if (alertBox) {
                    alertBox.innerHTML = '<div class="alert alert-danger py-2"><i class="bi bi-exclamation-triangle-fill me-1"></i> Error de conexión al subir la presentación.</div>';
                }
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });
    }

    // Manejador de Filtro de Unidades (Unidades 1 a 8)
    const unitChips = document.querySelectorAll('#unit-filter-chips .btn-unit-chip');
    const unitPanel = document.getElementById('session-week-panel');
    const unitLabel = document.getElementById('selected-unit-label');
    const sessionWeekGrid = document.getElementById('session-week-grid');
    const sessionSelect = document.getElementById('ppt-session-number');

    function applySessionSelection(sessionNumber) {
        const selectedSession = Number(sessionNumber) || 1;
        if (sessionSelect) sessionSelect.value = String(selectedSession);

        const titleInput = document.getElementById('ppt-title-input');
        if (titleInput) {
            const current = titleInput.value.trim();
            const isDefault = !current || /^Sesión\s*\d+:\s*material de la semana$/i.test(current);
            if (isDefault || current.startsWith('Sesión ')) {
                titleInput.value = `Sesión ${selectedSession}: material de la semana`;
            }
        }

        if (sessionWeekGrid) {
            sessionWeekGrid.querySelectorAll('.session-week-btn').forEach(button => {
                button.classList.toggle('active', Number(button.dataset.session) === selectedSession);
            });
        }
    }

    function renderSessionWeeksForUnit(unit, grade = Number(document.querySelector('.grade-chip[data-grade].active')?.dataset.grade || 5)) {
        const sessionNumbers = unit === 'all'
            ? Array.from({length: 32}, (_, index) => index + 1)
            : Array.from({length: 4}, (_, index) => ((Number(unit) - 1) * 4) + index + 1);

        if (sessionWeekGrid) {
            sessionWeekGrid.innerHTML = sessionNumbers.map((sessionNumber) => `
                <button class="grade-chip session-week-btn ${sessionSelect && Number(sessionSelect.value) === sessionNumber ? 'active' : ''}" data-session="${sessionNumber}" type="button">
                    <i class="bi bi-calendar4-week me-1"></i> Sesión ${sessionNumber}
                </button>
            `).join('');

            sessionWeekGrid.querySelectorAll('.session-week-btn').forEach(button => {
                button.addEventListener('click', () => {
                    const sessionNumber = Number(button.dataset.session);
                    applySessionSelection(sessionNumber);
                    selectedSessionFilter = sessionNumber;
                    applyTopicFilters();
                    refreshFilteredResourceLists();
                });
            });
        }

        if (unitPanel) {
            unitPanel.classList.toggle('d-none', unit === 'all');
        }
        if (unitLabel) {
            unitLabel.textContent = unit === 'all' ? 'Unidad activa: Todas' : `Unidad activa: ${unit}`;
        }
    }

    unitChips.forEach(chip => {
        chip.addEventListener('click', () => {
            unitChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const unit = chip.dataset.unit;
            const selectedGrade = Number(document.querySelector('.grade-chip[data-grade].active')?.dataset.grade || 5);
            renderSessionWeeksForUnit(unit, selectedGrade);
            selectedSessionFilter = null;
            filterTopicsByUnit(unit);
            if (unit !== 'all') {
                const sessionFrom = ((Number(unit) - 1) * 4) + 1;
                applySessionSelection(sessionFrom);
            }
            refreshFilteredResourceLists();
        });
    });

    if (sessionSelect) {
        sessionSelect.addEventListener('change', () => {
            const selectedSession = Number(sessionSelect.value);
            applySessionSelection(selectedSession);
            selectedSessionFilter = selectedSession;
            applyTopicFilters();
            refreshFilteredResourceLists();
        });
    }

    function filterTopicsByUnit(unit) {
        applyTopicFilters();
    }

    renderSessionWeeksForUnit('all');
    const defaultSession = document.getElementById('ppt-session-number');
    if (defaultSession) {
        defaultSession.value = '1';
    }

    // =========================================================
    // GOAL 3: Gestor de Evaluaciones IA y Aprobación Docente
    // =========================================================
    const assessmentsListContainer = document.getElementById('teacher-assessments-list-container');
    const assessmentsCountBadge = document.getElementById('assessments-count-badge');
    const formGenerateAssessment = document.getElementById('form-generate-assessment');
    const btnRefreshAssessments = document.getElementById('btn-refresh-assessments-list');
    const assessmentGenFeedback = document.getElementById('assessment-gen-feedback');

    const reviewModalEl = document.getElementById('assessmentReviewModal');
    let reviewModalInstance = null;
    if (reviewModalEl && typeof bootstrap !== 'undefined') {
        reviewModalInstance = new bootstrap.Modal(reviewModalEl);
    }

    function showAssessmentGenFeedback(message, type = 'info') {
        if (!assessmentGenFeedback) return;
        assessmentGenFeedback.style.display = 'block';
        assessmentGenFeedback.className = `alert alert-${type} py-2 px-3 small mt-2`;
        assessmentGenFeedback.innerHTML = message;
    }

    function showModalAssessmentFeedback(message, type = 'info') {
        const fb = document.getElementById('modal-assessment-feedback');
        if (!fb) return;
        fb.style.display = 'block';
        fb.className = `alert alert-${type} py-2 px-3 small mt-2`;
        fb.innerHTML = message;
        setTimeout(() => { if (fb) fb.style.display = 'none'; }, 4000);
    }

    async function loadTeacherAssessments() {
        if (!assessmentsListContainer) return;
        assessmentsListContainer.innerHTML = '<p class="text-muted small mb-0"><span class="spinner-border spinner-border-sm me-1"></span> Cargando evaluaciones...</p>';

        try {
            const resp = await fetch(`/teacher/api/assessments?${materialFilterParams().toString()}`);
            const data = await resp.json();
            if (!resp.ok || !data.success) {
                assessmentsListContainer.innerHTML = `<div class="alert alert-danger py-2 small mb-0">${data.error || 'No se pudieron cargar las evaluaciones.'}</div>`;
                return;
            }

            const list = data.assessments || [];
            if (assessmentsCountBadge) assessmentsCountBadge.textContent = `${list.length} evaluaciones`;

            if (list.length === 0) {
                assessmentsListContainer.innerHTML = `
                    <div class="p-3 text-center bg-white rounded-3 border text-muted small">
                        <i class="bi bi-clipboard-x fs-4 d-block mb-1 text-secondary"></i>
                        No hay evaluaciones registradas aún. Selecciona un tema arriba y presiona <strong>Generar con IA</strong>.
                    </div>`;
                return;
            }

            let html = '<div class="table-responsive"><table class="table table-hover align-middle mb-0 small"><thead class="table-light"><tr>';
            html += '<th>Tema / Título</th><th>Estado</th><th>Preguntas</th><th>Fecha</th><th class="text-end">Acciones Docente</th></tr></thead><tbody>';

            list.forEach(item => {
                const st = item.status || 'GENERATED';
                let badgeClass = 'bg-secondary text-white';
                let statusLabel = st;
                if (st === 'GENERATED') {
                    badgeClass = 'bg-secondary text-white';
                    statusLabel = '1. GENERATED';
                } else if (st === 'PENDING_REVIEW') {
                    badgeClass = 'bg-warning text-dark';
                    statusLabel = '2. PENDING_REVIEW (Revisión docente)';
                } else if (st === 'APPROVED') {
                    badgeClass = 'bg-info text-dark';
                    statusLabel = '3. APPROVED (Aprobada)';
                } else if (st === 'PUBLISHED') {
                    badgeClass = 'bg-success text-white';
                    statusLabel = '4. PUBLISHED (Visible para alumnos)';
                }

                const totalQ = Number(item.total_questions ?? item.question_count ?? item.questions?.length ?? 0);
                const approvedQ = Number(item.approved_questions ?? item.approved_count ?? 0);
                const questionCountText = totalQ + (totalQ === 1 ? ' pregunta' : ' preguntas');
                const approvedCountText = approvedQ + (approvedQ === 1 ? ' aprobada' : ' aprobadas');

                html += `<tr>
                    <td>
                        <strong class="d-block text-dark">${item.title}</strong>
                        <small class="text-muted">Tema ID: ${item.topic_id}${item.topic_title ? ' · ' + item.topic_title : ''}</small>
                    </td>
                    <td><span class="badge ${badgeClass} px-2 py-1 rounded-pill">${statusLabel}</span></td>
                    <td>
                        <span class="fw-semibold">${questionCountText}</span>
                        <small class="d-block text-muted">${approvedCountText}</small>
                    </td>
                    <td><small class="text-muted">${(item.created_at || '').substring(0, 10)}</small></td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-primary btn-review-assessment" data-id="${item.id}" title="Revisar y editar preguntas">
                                <i class="bi bi-pencil-square me-1"></i> Revisar
                            </button>
                            ${st !== 'PUBLISHED' ? `
                                <button type="button" class="btn btn-success btn-quick-publish" data-id="${item.id}" title="Aprobar y publicar directamente">
                                    <i class="bi bi-send-check"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                </tr>`;
            });

            html += '</tbody></table></div>';
            assessmentsListContainer.innerHTML = html;

            // Enlazar botones
            assessmentsListContainer.querySelectorAll('.btn-review-assessment').forEach(btn => {
                btn.addEventListener('click', () => openAssessmentReviewModal(btn.dataset.id));
            });

            assessmentsListContainer.querySelectorAll('.btn-quick-publish').forEach(btn => {
                btn.addEventListener('click', async () => {
                    if (!confirm('¿Deseas validar y publicar esta evaluación para que los alumnos puedan rendirla?')) return;
                    await publishAssessment(btn.dataset.id);
                    loadTeacherAssessments();
                });
            });

        } catch (err) {
            assessmentsListContainer.innerHTML = `<div class="alert alert-danger py-2 small mb-0">Error de conexión: ${err.message}</div>`;
        }
    }

    async function openAssessmentReviewModal(assessmentId) {
        if (!reviewModalInstance) return;
        const modalIdInput = document.getElementById('modal-assessment-id');
        const modalStatusBadge = document.getElementById('modal-assessment-status-badge');
        const modalSubtitle = document.getElementById('modal-assessment-subtitle');
        const modalQuestionsList = document.getElementById('modal-questions-list');
        const modalTopActions = document.getElementById('modal-assessment-top-actions');

        if (modalIdInput) modalIdInput.value = assessmentId;
        if (modalQuestionsList) modalQuestionsList.innerHTML = '<p class="text-muted small"><span class="spinner-border spinner-border-sm me-1"></span> Cargando preguntas de la evaluación...</p>';

        reviewModalInstance.show();

        try {
            const resp = await fetch(`/teacher/api/assessments/${assessmentId}`);
            const data = await resp.json();
            if (!resp.ok || !data.success) {
                if (modalQuestionsList) modalQuestionsList.innerHTML = `<div class="alert alert-danger">${data.error || 'Error al obtener la evaluación.'}</div>`;
                return;
            }

            const assessment = data.assessment || {};
            const questions = assessment.questions || [];
            const st = assessment.status || 'PENDING_REVIEW';

            if (modalSubtitle) modalSubtitle.textContent = `Evaluación: ${assessment.title} (Tema #${assessment.topic_id})`;
            if (modalStatusBadge) {
                modalStatusBadge.textContent = st;
                modalStatusBadge.className = `badge ${st === 'PUBLISHED' ? 'bg-success text-white' : (st === 'APPROVED' ? 'bg-info text-dark' : 'bg-warning text-dark')} fs-6 px-3 py-2 rounded-pill`;
            }

            renderModalQuestions(assessmentId, questions, st);

        } catch (err) {
            if (modalQuestionsList) modalQuestionsList.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
        }
    }

    function renderModalQuestions(assessmentId, questions, assessmentStatus) {
        const modalQuestionsList = document.getElementById('modal-questions-list');
        if (!modalQuestionsList) return;

        if (questions.length === 0) {
            modalQuestionsList.innerHTML = `
                <div class="p-3 bg-white border rounded-3 text-center text-muted small">
                    Esta evaluación aún no tiene preguntas. Agrega una con el formulario inferior.
                </div>`;
            return;
        }

        let html = '';
        questions.forEach((q, idx) => {
            const isApproved = !!q.approved;
            html += `
                <div class="card border rounded-3 p-3 shadow-xs ${isApproved ? 'border-success-subtle bg-white' : 'border-warning-subtle bg-light'}" id="card-q-${q.id}">
                    <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge ${isApproved ? 'bg-success' : 'bg-secondary'} rounded-pill">Pregunta ${idx + 1}</span>
                            <span class="badge ${isApproved ? 'bg-success-subtle text-success border border-success' : 'bg-warning-subtle text-warning border border-warning'}" id="badge-q-approved-${q.id}">
                                <i class="bi ${isApproved ? 'bi-check-circle-fill' : 'bi-clock'} me-1"></i> ${isApproved ? 'Aprobada por Docente' : 'Pendiente de Revisión'}
                            </span>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn ${isApproved ? 'btn-outline-warning' : 'btn-outline-success'} btn-toggle-approve-q" data-id="${q.id}" data-current="${isApproved ? '1' : '0'}" title="${isApproved ? 'Desaprobar' : 'Aprobar pregunta'}">
                                <i class="bi ${isApproved ? 'bi-x-circle' : 'bi-check-circle'} me-1"></i> ${isApproved ? 'Desaprobar' : 'Aprobar'}
                            </button>
                            <button type="button" class="btn btn-outline-primary btn-toggle-edit-q" data-id="${q.id}" title="Editar texto y alternativas">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button type="button" class="btn btn-outline-danger btn-delete-q" data-id="${q.id}" title="Eliminar pregunta">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Vista Estática de la Pregunta -->
                    <div id="view-q-${q.id}">
                        <p class="fw-bold text-dark mb-2">${q.question}</p>
                        <div class="row g-2 small">
                            <div class="col-md-4">
                                <div class="p-2 rounded border ${q.answer === q.option_a ? 'bg-success-subtle border-success fw-bold text-success' : 'bg-light'}">
                                    <span class="badge bg-secondary me-1">A</span> ${q.option_a}
                                    ${q.answer === q.option_a ? ' <i class="bi bi-check-lg"></i> (Correcta)' : ''}
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="p-2 rounded border ${q.answer === q.option_b ? 'bg-success-subtle border-success fw-bold text-success' : 'bg-light'}">
                                    <span class="badge bg-secondary me-1">B</span> ${q.option_b}
                                    ${q.answer === q.option_b ? ' <i class="bi bi-check-lg"></i> (Correcta)' : ''}
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="p-2 rounded border ${q.answer === q.option_c ? 'bg-success-subtle border-success fw-bold text-success' : 'bg-light'}">
                                    <span class="badge bg-secondary me-1">C</span> ${q.option_c}
                                    ${q.answer === q.option_c ? ' <i class="bi bi-check-lg"></i> (Correcta)' : ''}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Formulario de Edición en Línea (Oculto por Defecto) -->
                    <div id="edit-form-q-${q.id}" style="display: none;" class="mt-2 pt-2 border-top">
                        <div class="mb-2">
                            <label class="form-label small fw-semibold">Enunciado:</label>
                            <input type="text" class="form-control form-control-sm input-edit-question" value="${q.question}">
                        </div>
                        <div class="row g-2 mb-2">
                            <div class="col-md-4">
                                <label class="form-label small">Opción A:</label>
                                <input type="text" class="form-control form-control-sm input-edit-opta" value="${q.option_a}">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label small">Opción B:</label>
                                <input type="text" class="form-control form-control-sm input-edit-optb" value="${q.option_b}">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label small">Opción C:</label>
                                <input type="text" class="form-control form-control-sm input-edit-optc" value="${q.option_c}">
                            </div>
                        </div>
                        <div class="mb-2">
                            <label class="form-label small fw-semibold">Respuesta Correcta:</label>
                            <input type="text" class="form-control form-control-sm input-edit-answer" value="${q.answer}">
                        </div>
                        <div class="d-flex justify-content-end gap-2">
                            <button type="button" class="btn btn-sm btn-secondary btn-cancel-edit-q" data-id="${q.id}">Cancelar</button>
                            <button type="button" class="btn btn-sm btn-primary btn-save-edit-q" data-id="${q.id}">Guardar Cambios</button>
                        </div>
                    </div>
                </div>
            `;
        });

        modalQuestionsList.innerHTML = html;

        // Enlazar acciones de preguntas
        modalQuestionsList.querySelectorAll('.btn-toggle-approve-q').forEach(btn => {
            btn.addEventListener('click', async () => {
                const qid = btn.dataset.id;
                const newStatus = btn.dataset.current !== '1';
                try {
                    const resp = await fetch(`/teacher/api/assessments/${assessmentId}/questions/${qid}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ approved: newStatus })
                    });
                    const d = await resp.json();
                    if (resp.ok && d.success) {
                        showModalAssessmentFeedback(`Pregunta #${qid} ${newStatus ? 'aprobada' : 'desaprobada'} por docente.`, 'success');
                        openAssessmentReviewModal(assessmentId);
                    } else {
                        showModalAssessmentFeedback(d.error || 'Error al actualizar pregunta', 'danger');
                    }
                } catch (e) {
                    showModalAssessmentFeedback(`Error: ${e.message}`, 'danger');
                }
            });
        });

        modalQuestionsList.querySelectorAll('.btn-toggle-edit-q').forEach(btn => {
            btn.addEventListener('click', () => {
                const qid = btn.dataset.id;
                const form = document.getElementById(`edit-form-q-${qid}`);
                const view = document.getElementById(`view-q-${qid}`);
                if (form && view) {
                    const isShown = form.style.display !== 'none';
                    form.style.display = isShown ? 'none' : 'block';
                    view.style.display = isShown ? 'block' : 'none';
                }
            });
        });

        modalQuestionsList.querySelectorAll('.btn-cancel-edit-q').forEach(btn => {
            btn.addEventListener('click', () => {
                const qid = btn.dataset.id;
                const form = document.getElementById(`edit-form-q-${qid}`);
                const view = document.getElementById(`view-q-${qid}`);
                if (form) form.style.display = 'none';
                if (view) view.style.display = 'block';
            });
        });

        modalQuestionsList.querySelectorAll('.btn-save-edit-q').forEach(btn => {
            btn.addEventListener('click', async () => {
                const qid = btn.dataset.id;
                const card = document.getElementById(`card-q-${qid}`);
                if (!card) return;

                const qText = card.querySelector('.input-edit-question')?.value?.trim();
                const optA = card.querySelector('.input-edit-opta')?.value?.trim();
                const optB = card.querySelector('.input-edit-optb')?.value?.trim();
                const optC = card.querySelector('.input-edit-optc')?.value?.trim();
                const ans = card.querySelector('.input-edit-answer')?.value?.trim();

                if (!qText || !optA || !optB) {
                    showModalAssessmentFeedback('El enunciado y al menos dos opciones son obligatorios.', 'danger');
                    return;
                }

                try {
                    const resp = await fetch(`/teacher/api/assessments/${assessmentId}/questions/${qid}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            question: qText,
                            option_a: optA,
                            option_b: optB,
                            option_c: optC,
                            answer: ans || optA,
                            approved: true // Al editar y guardar, queda validada por el docente
                        })
                    });
                    const d = await resp.json();
                    if (resp.ok && d.success) {
                        showModalAssessmentFeedback('Pregunta editada y guardada correctamente.', 'success');
                        openAssessmentReviewModal(assessmentId);
                    } else {
                        showModalAssessmentFeedback(d.error || 'Error al guardar edición', 'danger');
                    }
                } catch (e) {
                    showModalAssessmentFeedback(`Error: ${e.message}`, 'danger');
                }
            });
        });

        modalQuestionsList.querySelectorAll('.btn-delete-q').forEach(btn => {
            btn.addEventListener('click', async () => {
                const qid = btn.dataset.id;
                if (!confirm('¿Seguro de eliminar esta pregunta de la evaluación?')) return;
                try {
                    const resp = await fetch(`/teacher/api/assessments/${assessmentId}/questions/${qid}`, {
                        method: 'DELETE'
                    });
                    const d = await resp.json();
                    if (resp.ok && d.success) {
                        showModalAssessmentFeedback('Pregunta eliminada.', 'info');
                        openAssessmentReviewModal(assessmentId);
                    } else {
                        showModalAssessmentFeedback(d.error || 'Error al eliminar', 'danger');
                    }
                } catch (e) {
                    showModalAssessmentFeedback(`Error: ${e.message}`, 'danger');
                }
            });
        });
    }

    async function approveAssessment(assessmentId) {
        try {
            const resp = await fetch(`/teacher/api/assessments/${assessmentId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await resp.json();
            if (resp.ok && data.success) {
                showModalAssessmentFeedback('✅ Evaluación aprobada por el docente (Estado: APPROVED). Ahora puedes publicarla.', 'success');
                loadTeacherAssessments();
                openAssessmentReviewModal(assessmentId);
            } else {
                showModalAssessmentFeedback(data.error || 'No se pudo aprobar la evaluación', 'danger');
            }
        } catch (e) {
            showModalAssessmentFeedback(`Error: ${e.message}`, 'danger');
        }
    }

    async function publishAssessment(assessmentId) {
        try {
            const resp = await fetch(`/teacher/api/assessments/${assessmentId}/publish`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await resp.json();
            if (resp.ok && data.success) {
                showModalAssessmentFeedback('🚀 ¡Evaluación PUBLICADA! Los alumnos ya pueden visualizar y rendir las preguntas aprobadas.', 'success');
                loadTeacherAssessments();
                openAssessmentReviewModal(assessmentId);
            } else {
                showModalAssessmentFeedback(data.error || 'No se pudo publicar la evaluación', 'danger');
            }
        } catch (e) {
            showModalAssessmentFeedback(`Error: ${e.message}`, 'danger');
        }
    }

    // Botones de acción general dentro del modal
    const btnModalApproveTop = document.getElementById('btn-modal-approve-assessment');
    const btnModalApproveFooter = document.getElementById('btn-modal-footer-approve');
    const btnModalPublishTop = document.getElementById('btn-modal-publish-assessment');
    const btnModalPublishFooter = document.getElementById('btn-modal-footer-publish');

    [btnModalApproveTop, btnModalApproveFooter].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                const aid = document.getElementById('modal-assessment-id')?.value;
                if (aid) approveAssessment(aid);
            });
        }
    });

    [btnModalPublishTop, btnModalPublishFooter].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                const aid = document.getElementById('modal-assessment-id')?.value;
                if (aid) publishAssessment(aid);
            });
        }
    });

    // Formulario para agregar pregunta manual
    const btnAddManualQ = document.getElementById('btn-add-manual-q');
    if (btnAddManualQ) {
        btnAddManualQ.addEventListener('click', async () => {
            const aid = document.getElementById('modal-assessment-id')?.value;
            if (!aid) return;

            const qText = document.getElementById('new-q-text')?.value?.trim();
            const optA = document.getElementById('new-q-opta')?.value?.trim();
            const optB = document.getElementById('new-q-optb')?.value?.trim();
            const optC = document.getElementById('new-q-optc')?.value?.trim();

            if (!qText || !optA || !optB) {
                showModalAssessmentFeedback('El enunciado y al menos dos alternativas son obligatorios.', 'warning');
                return;
            }

            try {
                const resp = await fetch(`/teacher/api/assessments/${aid}/questions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: qText,
                        option_a: optA,
                        option_b: optB,
                        option_c: optC || 'Otra alternativa',
                        answer: optA,
                        approved: true // Pregunta agregada directamente por el docente nace aprobada
                    })
                });
                const d = await resp.json();
                if (resp.ok && d.success) {
                    showModalAssessmentFeedback('Pregunta agregada y aprobada correctamente.', 'success');
                    document.getElementById('new-q-text').value = '';
                    document.getElementById('new-q-opta').value = '';
                    document.getElementById('new-q-optb').value = '';
                    document.getElementById('new-q-optc').value = '';
                    openAssessmentReviewModal(aid);
                } else {
                    showModalAssessmentFeedback(d.error || 'Error al agregar pregunta', 'danger');
                }
            } catch (e) {
                showModalAssessmentFeedback(`Error: ${e.message}`, 'danger');
            }
        });
    }

    // Generador con IA
    if (formGenerateAssessment) {
        formGenerateAssessment.addEventListener('submit', async (e) => {
            e.preventDefault();
            const topicSelect = document.getElementById('assessment-gen-topic-select');
            const titleInput = document.getElementById('assessment-gen-title-input');
            const topicId = topicSelect?.value;
            const selectedOpt = topicSelect?.options[topicSelect.selectedIndex];
            const topicTitle = selectedOpt?.dataset?.title || '';
            const grade = selectedOpt?.dataset?.grade || 5;
            const title = (titleInput?.value || '').trim() || `Evaluación de ${topicTitle || 'Computación'}`;

            if (!topicId) {
                showAssessmentGenFeedback('Selecciona un tema para generar la evaluación.', 'warning');
                return;
            }

            const generateButton = document.getElementById('btn-generate-assessment-ai');
            if (generateButton) generateButton.disabled = true;
            showAssessmentGenFeedback('🤖 Analizando el PPT y creando preguntas verificables. Puede tardar hasta 45 segundos; quedarán en revisión docente.', 'info');

            try {
                const resp = await fetch('/teacher/api/assessments/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        topic_id: topicId,
                        topic_title: topicTitle,
                        grade: grade,
                        title: title,
                        question_count: 15
                    })
                });
                const data = await resp.json();
                if (resp.ok && data.success) {
                    showAssessmentGenFeedback(`✅ ¡Evaluación creada con ${data.questions?.length || 0} preguntas verificables en estado <strong>${data.status}</strong>! No está publicada a los alumnos hasta que la valides.`, 'success');
                    loadTeacherAssessments();
                    if (data.assessment_id) {
                        setTimeout(() => openAssessmentReviewModal(data.assessment_id), 800);
                    }
                } else {
                    showAssessmentGenFeedback(data.error || 'No se pudo generar la evaluación.', 'danger');
                }
            } catch (err) {
                showAssessmentGenFeedback(`Error al generar con IA: ${err.message}`, 'danger');
            } finally {
                if (generateButton) generateButton.disabled = false;
            }
        });
    }

    if (btnRefreshAssessments) {
        btnRefreshAssessments.addEventListener('click', () => loadTeacherAssessments());
    }

    // Cargar la lista inicial de evaluaciones
    loadTeacherAssessments();

    // =========================================================================
    // GOAL: Generador de Juegos Educativos con IA usando Ollama (Gobernanza Docente)
    // =========================================================================

    const formGenerateAiGame = document.getElementById('form-generate-ai-game');
    const aiGameGenTopicSelect = document.getElementById('ai-game-gen-topic-select');
    const aiGameGenTypeSelect = document.getElementById('ai-game-gen-type-select');
    const aiGameGenSourceSelect = document.getElementById('ai-game-gen-source-select');
    const aiGamePresentationWrap = document.getElementById('ai-game-gen-presentation-wrap');
    const aiGamePresentationSelect = document.getElementById('ai-game-gen-presentation-select');
    const btnGenerateAiGame = document.getElementById('btn-generate-ai-game');
    const btnRefreshAiGames = document.getElementById('btn-refresh-ai-games-list');
    const aiGameGenFeedback = document.getElementById('ai-game-gen-feedback');
    const aiGamesContainer = document.getElementById('teacher-ai-games-list-container');
    const aiGamesCountBadge = document.getElementById('ai-games-count-badge');

    const aiGameReviewModalEl = document.getElementById('aiGameReviewModal');
    let aiGameReviewModal = null;
    if (aiGameReviewModalEl && typeof bootstrap !== 'undefined') {
        aiGameReviewModal = new bootstrap.Modal(aiGameReviewModalEl);
    }

    function showAiGameFeedback(msg, type = 'info') {
        if (!aiGameGenFeedback) return;
        aiGameGenFeedback.style.display = 'block';
        aiGameGenFeedback.className = `alert alert-${type} py-2 px-3 small mt-2`;
        aiGameGenFeedback.innerHTML = msg;
    }

    function showModalAiGameFeedback(msg, type = 'info') {
        const fb = document.getElementById('modal-ai-game-feedback');
        if (!fb) return;
        fb.style.display = 'block';
        fb.className = `alert alert-${type} py-2 px-3 small mt-2`;
        fb.innerHTML = msg;
        setTimeout(() => { if (fb) fb.style.display = 'none'; }, 4000);
    }

    async function loadTeacherAiGames() {
        if (!aiGamesContainer) return;
        aiGamesContainer.innerHTML = '<p class="text-muted small mb-0"><span class="spinner-border spinner-border-sm me-1"></span> Cargando juegos generados por IA...</p>';

        try {
            const resp = await fetch(`/teacher/api/ai-games?${materialFilterParams().toString()}`);
            const data = await resp.json();
            if (!resp.ok || !data.success) {
                aiGamesContainer.innerHTML = `<div class="alert alert-danger py-2 small mb-0">${data.error || 'No se pudieron cargar los juegos.'}</div>`;
                return;
            }

            const games = data.games || [];
            if (aiGamesCountBadge) aiGamesCountBadge.textContent = `${games.length} juegos`;

            if (games.length === 0) {
                aiGamesContainer.innerHTML = `
                    <div class="p-3 text-center bg-white rounded-3 border text-muted small">
                        <i class="bi bi-controller fs-4 d-block mb-1 text-secondary"></i>
                        No hay juegos generados aún. Elige un tema arriba y pulsa <strong>Generar</strong>.
                    </div>`;
                return;
            }

            let html = '<div class="table-responsive"><table class="table table-hover align-middle mb-0 small"><thead class="table-light"><tr>';
            html += '<th>Tema / Título</th><th>Tipo</th><th>Estado</th><th>Contenido</th><th class="text-end">Acciones Docente</th></tr></thead><tbody>';

            games.forEach(g => {
                const st = g.status || 'PENDING_REVIEW';
                let badgeClass = 'bg-secondary text-white';
                let statusLabel = st;
                if (st === 'GENERATED') {
                    badgeClass = 'bg-secondary text-white';
                    statusLabel = '1. GENERATED';
                } else if (st === 'PENDING_REVIEW') {
                    badgeClass = 'bg-warning text-dark';
                    statusLabel = '2. PENDING_REVIEW';
                } else if (st === 'APPROVED') {
                    badgeClass = 'bg-info text-dark';
                    statusLabel = '3. APPROVED';
                } else if (st === 'PUBLISHED') {
                    badgeClass = 'bg-success text-white';
                    statusLabel = '4. PUBLISHED (Visible)';
                }

                const typeLabels = {
                    'multiple_choice': '🎯 Opción Múltiple',
                    'true_false': '⚖️ V/F',
                    'fill_blank': '✏️ Completar',
                    'matching': '🧩 Unir Conceptos',
                    'memory': '🃏 Memoria',
                    'ordering': '🔢 Ordenar',
                    'drag_drop': '🧲 Clasificar',
                    'challenge': '🚀 Aventura'
                };
                const typeLabel = typeLabels[g.game_type] || g.game_type;

                const c = g.content_json || {};
                let previewText = c.question || c.statement || c.sentence || (c.pairs ? `${c.pairs.length} parejas` : '') || (c.items ? `${c.items.length} tarjetas` : '') || (c.levels ? `${c.levels.length} niveles` : 'Contenido interactivo');
                if (previewText.length > 55) previewText = previewText.substring(0, 52) + '...';

                html += `
                    <tr>
                        <td>
                            <strong class="text-dark">${escapeText(g.title)}</strong>
                            <small class="text-muted d-block">${escapeText(g.topic_title || 'Tema')}</small>
                        </td>
                        <td><span class="badge bg-light text-dark border">${typeLabel}</span></td>
                        <td><span class="badge ${badgeClass} px-2 py-1">${statusLabel}</span></td>
                        <td><span class="text-muted fst-italic">${escapeText(previewText)}</span></td>
                        <td class="text-end">
                            <div class="btn-group btn-group-sm">
                                <button type="button" class="btn btn-outline-primary btn-review-ai-game" data-game-id="${g.id}" title="Revisar o Editar">
                                    <i class="bi bi-pencil-square me-1"></i> Revisar
                                </button>
                                ${st !== 'PUBLISHED' ? `
                                <button type="button" class="btn btn-outline-success btn-quick-publish-ai-game" data-game-id="${g.id}" title="Publicar para Alumnos">
                                    <i class="bi bi-send-check"></i>
                                </button>` : ''}
                                <button type="button" class="btn btn-outline-danger btn-delete-ai-game" data-game-id="${g.id}" title="Eliminar">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            });

            html += '</tbody></table></div>';
            aiGamesContainer.innerHTML = html;

            // Enlazar eventos de botones
            aiGamesContainer.querySelectorAll('.btn-review-ai-game').forEach(btn => {
                btn.addEventListener('click', () => openAiGameReviewModal(btn.dataset.gameId));
            });

            aiGamesContainer.querySelectorAll('.btn-quick-publish-ai-game').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const gameId = btn.dataset.gameId;
                    try {
                        const resp = await fetch(`/teacher/api/ai-games/${gameId}/publish`, { method: 'POST' });
                        const data = await resp.json();
                        if (resp.ok && data.success) {
                            loadTeacherAiGames();
                        } else {
                            alert(data.error || 'No se pudo publicar el juego.');
                        }
                    } catch (e) {
                        alert(`Error: ${e.message}`);
                    }
                });
            });

            aiGamesContainer.querySelectorAll('.btn-delete-ai-game').forEach(btn => {
                btn.addEventListener('click', async () => {
                    if (!confirm('¿Estás seguro de eliminar este juego generado por IA?')) return;
                    const gameId = btn.dataset.gameId;
                    try {
                        const resp = await fetch(`/teacher/api/ai-games/${gameId}`, { method: 'DELETE' });
                        const data = await resp.json();
                        if (resp.ok && data.success) {
                            loadTeacherAiGames();
                        } else {
                            alert(data.error || 'No se pudo eliminar el juego.');
                        }
                    } catch (e) {
                        alert(`Error: ${e.message}`);
                    }
                });
            });

        } catch (err) {
            aiGamesContainer.innerHTML = `<div class="alert alert-danger py-2 small mb-0">Error de conexión: ${err.message}</div>`;
        }
    }

    async function openAiGameReviewModal(gameId) {
        if (!aiGameReviewModal) return;
        const modalIdInput = document.getElementById('modal-ai-game-id');
        const modalTitleInput = document.getElementById('modal-ai-game-title');
        const modalInstructionInput = document.getElementById('modal-ai-game-instruction');
        const modalStatusBadge = document.getElementById('modal-ai-game-status-badge');
        const modalTypeBadge = document.getElementById('modal-ai-game-type-badge');
        const modalDifficulty = document.getElementById('modal-ai-game-difficulty');
        const dynamicContentArea = document.getElementById('modal-ai-game-dynamic-content');

        modalIdInput.value = gameId;
        dynamicContentArea.innerHTML = '<p class="text-muted small mb-0"><span class="spinner-border spinner-border-sm me-1"></span> Cargando datos del juego...</p>';
        aiGameReviewModal.show();

        try {
            const resp = await fetch(`/teacher/api/ai-games/${gameId}`);
            const data = await resp.json();
            if (!resp.ok || !data.success) {
                dynamicContentArea.innerHTML = `<div class="alert alert-danger py-2 small">${data.error || 'Error al obtener el juego.'}</div>`;
                return;
            }

            const game = data.game;
            modalTitleInput.value = game.title || '';
            modalInstructionInput.value = game.instruction || '';

            const st = game.status || 'PENDING_REVIEW';
            modalStatusBadge.textContent = st;
            modalStatusBadge.className = `badge ${st === 'PUBLISHED' ? 'bg-success' : st === 'APPROVED' ? 'bg-info text-dark' : 'bg-warning text-dark'} fs-6 px-3 py-2 rounded-pill`;

            modalTypeBadge.textContent = game.game_type;

            const c = game.content_json || {};
            if (modalDifficulty) modalDifficulty.value = (c._meta || {}).difficulty || 'easy';
            let dynHtml = '';

            if (game.game_type === 'multiple_choice') {
                dynHtml = `
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Pregunta</label>
                        <input type="text" class="form-control" id="edit-mc-question" value="${escapeText(c.question || '')}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Opciones de respuesta (una por línea o separadas por coma)</label>
                        <textarea class="form-control" id="edit-mc-options" rows="3" required>${(c.options || []).join('\n')}</textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Respuesta Correcta</label>
                        <input type="text" class="form-control text-success fw-bold" id="edit-mc-answer" value="${escapeText(c.answer || '')}" required>
                    </div>
                    <div>
                        <label class="form-label small fw-bold">Explicación motivadora</label>
                        <input type="text" class="form-control" id="edit-mc-explanation" value="${escapeText(c.explanation || '')}">
                    </div>
                `;
            } else if (game.game_type === 'true_false') {
                dynHtml = `
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Afirmación</label>
                        <input type="text" class="form-control" id="edit-tf-statement" value="${escapeText(c.statement || '')}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Respuesta Correcta</label>
                        <select class="form-select text-primary fw-bold" id="edit-tf-answer">
                            <option value="true" ${c.correct_answer === true ? 'selected' : ''}>✅ Verdadero</option>
                            <option value="false" ${c.correct_answer === false ? 'selected' : ''}>❌ Falso</option>
                        </select>
                    </div>
                    <div>
                        <label class="form-label small fw-bold">Explicación</label>
                        <input type="text" class="form-control" id="edit-tf-explanation" value="${escapeText(c.explanation || '')}">
                    </div>
                `;
            } else if (game.game_type === 'fill_blank') {
                dynHtml = `
                    <div class="mb-3">
                        <label class="form-label small fw-bold">Oración con espacio a completar (usa '______')</label>
                        <input type="text" class="form-control" id="edit-fb-sentence" value="${escapeText(c.sentence || '')}" required>
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-md-6">
                            <label class="form-label small fw-bold">Palabra que completa (blank_word)</label>
                            <input type="text" class="form-control text-success fw-bold" id="edit-fb-word" value="${escapeText(c.blank_word || (c.answers && c.answers[0]) || '')}" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label small fw-bold">Alternativas separadas por coma</label>
                            <input type="text" class="form-control" id="edit-fb-options" value="${escapeText((c.options || []).join(', '))}">
                        </div>
                    </div>
                    <div>
                        <label class="form-label small fw-bold">Explicación</label>
                        <input type="text" class="form-control" id="edit-fb-explanation" value="${escapeText(c.explanation || '')}">
                    </div>
                `;
            } else if (game.game_type === 'matching') {
                const pairs = c.pairs || [];
                let pairsRows = '';
                pairs.forEach((p, idx) => {
                    pairsRows += `
                        <div class="row g-2 mb-2 pair-row">
                            <div class="col-md-5"><input type="text" class="form-control form-control-sm pair-left" value="${escapeText(p.left || '')}" placeholder="Concepto"></div>
                            <div class="col-md-7"><input type="text" class="form-control form-control-sm pair-right" value="${escapeText(p.right || '')}" placeholder="Definición o significado"></div>
                        </div>
                    `;
                });
                dynHtml = `
                    <label class="form-label small fw-bold mb-2">Parejas conceptuales para unir:</label>
                    <div id="matching-pairs-container">${pairsRows}</div>
                    <div class="mt-2">
                        <label class="form-label small fw-bold">Explicación</label>
                        <input type="text" class="form-control" id="edit-match-explanation" value="${escapeText(c.explanation || '')}">
                    </div>
                `;
            } else {
                dynHtml = `
                    <label class="form-label small fw-bold">Datos del juego (JSON)</label>
                    <p class="small text-muted">Puedes editar las tarjetas, pasos, categorías o niveles. La estructura se validará antes de guardar.</p>
                    <textarea class="form-control font-monospace small" id="edit-game-json" rows="12" required>${escapeText(JSON.stringify(c, null, 2))}</textarea>
                `;
            }

            dynamicContentArea.innerHTML = dynHtml;

        } catch (err) {
            dynamicContentArea.innerHTML = `<div class="alert alert-danger py-2 small">${err.message}</div>`;
        }
    }

    // Guardar cambios del modal
    const btnModalSave = document.getElementById('btn-modal-ai-game-save');
    if (btnModalSave) {
        btnModalSave.addEventListener('click', async () => {
            const gameId = document.getElementById('modal-ai-game-id').value;
            const newTitle = document.getElementById('modal-ai-game-title').value.trim();
            const newInstruction = document.getElementById('modal-ai-game-instruction').value.trim();
            const newDifficulty = document.getElementById('modal-ai-game-difficulty').value;
            const typeBadge = document.getElementById('modal-ai-game-type-badge').textContent.trim();

            let newContent = {};
            if (typeBadge === 'multiple_choice') {
                const q = document.getElementById('edit-mc-question').value.trim();
                const rawOpts = document.getElementById('edit-mc-options').value;
                const opts = rawOpts.split(/\r?\n|,/).map(o => o.trim()).filter(Boolean);
                const ans = document.getElementById('edit-mc-answer').value.trim();
                const exp = document.getElementById('edit-mc-explanation').value.trim();
                newContent = { question: q, options: opts, answer: ans, explanation: exp };
            } else if (typeBadge === 'true_false') {
                const stmt = document.getElementById('edit-tf-statement').value.trim();
                const ans = document.getElementById('edit-tf-answer').value === 'true';
                const exp = document.getElementById('edit-tf-explanation').value.trim();
                newContent = { statement: stmt, correct_answer: ans, explanation: exp };
            } else if (typeBadge === 'fill_blank') {
                const s = document.getElementById('edit-fb-sentence').value.trim();
                const w = document.getElementById('edit-fb-word').value.trim();
                const opts = document.getElementById('edit-fb-options').value.split(',').map(o => o.trim()).filter(Boolean);
                const exp = document.getElementById('edit-fb-explanation').value.trim();
                newContent = { sentence: s, blank_word: w, answers: [w], options: opts, explanation: exp };
            } else if (typeBadge === 'matching') {
                const pairs = [];
                document.querySelectorAll('.pair-row').forEach(row => {
                    const l = row.querySelector('.pair-left')?.value.trim();
                    const r = row.querySelector('.pair-right')?.value.trim();
                    if (l && r) pairs.push({ left: l, right: r });
                });
                const exp = document.getElementById('edit-match-explanation').value.trim();
                newContent = { pairs, explanation: exp };
            } else {
                try {
                    newContent = JSON.parse(document.getElementById('edit-game-json').value);
                    delete newContent._meta;
                } catch (error) {
                    showModalAiGameFeedback('El JSON del juego no es válido.', 'danger');
                    return;
                }
            }

            try {
                btnModalSave.disabled = true;
                const resp = await fetch(`/teacher/api/ai-games/${gameId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: newTitle,
                        instruction: newInstruction,
                        content_json: newContent,
                        difficulty: newDifficulty
                    })
                });
                const data = await resp.json();
                btnModalSave.disabled = false;
                if (resp.ok && data.success) {
                    showModalAiGameFeedback('✅ Cambios guardados y validados correctamente.', 'success');
                    loadTeacherAiGames();
                } else {
                    showModalAiGameFeedback(data.error || 'Error al guardar cambios.', 'danger');
                }
            } catch (err) {
                btnModalSave.disabled = false;
                showModalAiGameFeedback(`Error: ${err.message}`, 'danger');
            }
        });
    }

    async function loadAiGamePresentationOptions() {
        if (!aiGamePresentationWrap || !aiGamePresentationSelect) return;
        const topicId = aiGameGenTopicSelect?.value;
        const usingPresentation = aiGameGenSourceSelect?.value === 'presentation';
        aiGamePresentationWrap.classList.toggle('d-none', !usingPresentation);
        if (!usingPresentation) {
            aiGamePresentationSelect.innerHTML = '<option value="">No se usará una presentación</option>';
            aiGamePresentationSelect.disabled = true;
            return;
        }
        if (!topicId) {
            aiGamePresentationSelect.innerHTML = '<option value="">Selecciona primero un tema</option>';
            aiGamePresentationSelect.disabled = true;
            return;
        }

        aiGamePresentationSelect.disabled = true;
        aiGamePresentationSelect.innerHTML = '<option value="">Buscando presentaciones...</option>';
        try {
            const response = await fetch(`/teacher/api/presentations/${topicId}`);
            const data = await response.json();
            const presentations = data.presentations || [];
            if (!response.ok || presentations.length === 0) {
                aiGamePresentationSelect.innerHTML = '<option value="">No hay presentaciones para este tema</option>';
                return;
            }
            aiGamePresentationSelect.innerHTML = presentations.map(presentation =>
                `<option value="${presentation.id}">Sesión ${presentation.session_number}: ${escapeText(presentation.title || presentation.file_name || 'Presentación')}</option>`,
            ).join('');
            aiGamePresentationSelect.disabled = false;
        } catch (error) {
            aiGamePresentationSelect.innerHTML = '<option value="">No se pudo cargar las presentaciones</option>';
        }
    }

    [aiGameGenTopicSelect, aiGameGenSourceSelect].forEach(control => {
        control?.addEventListener('change', loadAiGamePresentationOptions);
    });
    loadAiGamePresentationOptions();

    const btnModalRegenerate = document.getElementById('btn-modal-ai-game-regenerate');
    if (btnModalRegenerate) {
        btnModalRegenerate.addEventListener('click', async () => {
            const gameId = document.getElementById('modal-ai-game-id').value;
            if (!confirm('Se reemplazará esta versión por una nueva basada en el material original. ¿Continuar?')) return;
            try {
                btnModalRegenerate.disabled = true;
                const resp = await fetch(`/teacher/api/ai-games/${gameId}/regenerate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ difficulty: document.getElementById('modal-ai-game-difficulty').value }) });
                const data = await resp.json();
                btnModalRegenerate.disabled = false;
                if (resp.ok && data.success) {
                    showModalAiGameFeedback('Nueva versión creada. Revísala antes de aprobarla.', 'success');
                    openAiGameReviewModal(gameId);
                    loadTeacherAiGames();
                } else {
                    showModalAiGameFeedback(data.error || 'No se pudo regenerar el juego.', 'danger');
                }
            } catch (error) {
                btnModalRegenerate.disabled = false;
                showModalAiGameFeedback(`Error: ${error.message}`, 'danger');
            }
        });
    }

    // Aprobar desde el modal
    const btnModalApprove = document.getElementById('btn-modal-ai-game-approve');
    if (btnModalApprove) {
        btnModalApprove.addEventListener('click', async () => {
            const gameId = document.getElementById('modal-ai-game-id').value;
            try {
                const resp = await fetch(`/teacher/api/ai-games/${gameId}/approve`, { method: 'POST' });
                const data = await resp.json();
                if (resp.ok && data.success) {
                    showModalAiGameFeedback('✅ ¡Juego APROBADO por el profesor!', 'success');
                    document.getElementById('modal-ai-game-status-badge').textContent = 'APPROVED';
                    document.getElementById('modal-ai-game-status-badge').className = 'badge bg-info text-dark fs-6 px-3 py-2 rounded-pill';
                    loadTeacherAiGames();
                } else {
                    showModalAiGameFeedback(data.error || 'No se pudo aprobar.', 'danger');
                }
            } catch (err) {
                showModalAiGameFeedback(`Error: ${err.message}`, 'danger');
            }
        });
    }

    // Publicar desde el modal
    const btnModalPublish = document.getElementById('btn-modal-ai-game-publish');
    if (btnModalPublish) {
        btnModalPublish.addEventListener('click', async () => {
            const gameId = document.getElementById('modal-ai-game-id').value;
            try {
                const resp = await fetch(`/teacher/api/ai-games/${gameId}/publish`, { method: 'POST' });
                const data = await resp.json();
                if (resp.ok && data.success) {
                    showModalAiGameFeedback('🚀 ¡Juego PUBLICADO! Ahora es visible para los alumnos.', 'success');
                    document.getElementById('modal-ai-game-status-badge').textContent = 'PUBLISHED';
                    document.getElementById('modal-ai-game-status-badge').className = 'badge bg-success fs-6 px-3 py-2 rounded-pill';
                    loadTeacherAiGames();
                } else {
                    showModalAiGameFeedback(data.error || 'No se pudo publicar.', 'danger');
                }
            } catch (err) {
                showModalAiGameFeedback(`Error: ${err.message}`, 'danger');
            }
        });
    }

    // Eliminar desde el modal
    const btnModalDelete = document.getElementById('btn-modal-ai-game-delete');
    if (btnModalDelete) {
        btnModalDelete.addEventListener('click', async () => {
            if (!confirm('¿Seguro que deseas eliminar este juego?')) return;
            const gameId = document.getElementById('modal-ai-game-id').value;
            try {
                const resp = await fetch(`/teacher/api/ai-games/${gameId}`, { method: 'DELETE' });
                const data = await resp.json();
                if (resp.ok && data.success) {
                    if (aiGameReviewModal) aiGameReviewModal.hide();
                    loadTeacherAiGames();
                } else {
                    showModalAiGameFeedback(data.error || 'Error al eliminar.', 'danger');
                }
            } catch (err) {
                showModalAiGameFeedback(`Error: ${err.message}`, 'danger');
            }
        });
    }

    // Generar con IA desde el formulario
    if (formGenerateAiGame) {
        formGenerateAiGame.addEventListener('submit', async (e) => {
            e.preventDefault();
            const topicId = aiGameGenTopicSelect.value;
            const gameType = aiGameGenTypeSelect.value;
            const sourceChoice = aiGameGenSourceSelect.value;

            if (!topicId) {
                showAiGameFeedback('Por favor, selecciona un tema.', 'warning');
                return;
            }

            btnGenerateAiGame.disabled = true;
            btnGenerateAiGame.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Generando...';
            showAiGameFeedback('⏳ Generando y creando juego...', 'info');

            try {
                let targetUrl = '';
                if (sourceChoice === 'presentation') {
                    const presentationId = aiGamePresentationSelect?.value;
                    if (!presentationId) {
                        showAiGameFeedback('Selecciona una presentación del tema antes de generar el juego.', 'warning');
                        return;
                    }
                    targetUrl = `/teacher/api/presentations/${presentationId}/generate-game`;
                }

                if (sourceChoice === 'material') {
                    // Buscar material de texto del tema seleccionado.
                    const mResp = await fetch(`/student/api/topics/${topicId}/materials`);
                    const mData = await mResp.json();
                    const materials = mData.materials || [];
                    const textMat = materials.find(m => m.source === 'material') || materials[0];
                    if (textMat && textMat.id) {
                        targetUrl = `/teacher/api/materials/${textMat.id}/generate-game`;
                    }
                }

                if (!targetUrl) {
                    showAiGameFeedback('No hay material disponible para la fuente elegida. Sube o publica material en este tema primero.', 'warning');
                    return;
                }

                const resp = await fetch(targetUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ game_type: gameType })
                });
                const data = await resp.json();

                if (resp.ok && data.success) {
                    const noticeText = data.notice ? ` (${data.notice})` : '';
                    showAiGameFeedback(`✅ ¡Juego generado con éxito en estado <strong>${data.status}</strong>!${noticeText} Abre la revisión para validar y publicar.`, 'success');
                    loadTeacherAiGames();
                    if (data.game_id) {
                        setTimeout(() => openAiGameReviewModal(data.game_id), 700);
                    }
                } else {
                    showAiGameFeedback(data.error || 'No se pudo generar el juego.', 'danger');
                }
            } catch (err) {
                showAiGameFeedback(`Error de generación: ${err.message}`, 'danger');
            } finally {
                btnGenerateAiGame.disabled = false;
                btnGenerateAiGame.innerHTML = '<i class="bi bi-robot me-1"></i> Generar';
            }
        });
    }

    if (btnRefreshAiGames) {
        btnRefreshAiGames.addEventListener('click', () => loadTeacherAiGames());
    }

    // Cargar la lista inicial de juegos IA generados
    loadTeacherAiGames();
});


document.addEventListener('click', async event => {
    const button = event.target.closest('.prepare-practice');
    if (!button || button.disabled) return;
    button.disabled = true;
    const label = button.textContent;
    button.textContent = 'Preparando preguntas...';
    try {
        const response = await fetch(`/teacher/api/${button.dataset.source}/${button.dataset.id}/prepare-practice`, { method: 'POST' });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'No se pudo preparar la actividad.');
        alert(`${data.questions.length} preguntas guardadas. Origen: ${data.source}. Los alumnos pueden practicar sin esperar a la IA.`);
    } catch (error) {
        alert(error.message);
    } finally {
        button.disabled = false;
        button.textContent = label;
    }
});

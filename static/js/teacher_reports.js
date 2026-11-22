function reportQuery(extra = {}) {
    const grade = extra.grade || document.getElementById('report-grade')?.value || '5';
    const period = extra.period || document.getElementById('report-period')?.value || '1';
    const section = extra.section || 'all';
    return {grade, period, section, ...extra};
}

function levelBadge(code) {
    const map = {
        AD: 'badge bg-success',
        A: 'badge bg-primary',
        B: 'badge bg-warning text-dark',
        C: 'badge bg-danger',
    };
    return `<span class="${map[code] || 'badge bg-secondary'}">${code}</span>`;
}

function renderReportChart(chart) {
    const box = document.getElementById('report-chart');
    if (!box) return;
    const max = Math.max(1, ...chart.map(item => Number(item.value) || 0));
    box.innerHTML = chart.map(item => `
        <div class="report-chart-row">
            <span>${item.label}</span>
            <div class="report-chart-track">
                <div class="report-chart-bar" style="width:${(Number(item.value) / max) * 100}%; background:${item.color}"></div>
            </div>
            <strong>${item.value}</strong>
        </div>
    `).join('');
}

async function loadAcademicReport() {
    const gradeSelect = document.getElementById('notes-report-grade');
    const periodSelect = document.getElementById('notes-report-period');
    if (gradeSelect) gradeSelect.value = document.getElementById('report-grade')?.value || gradeSelect.value;
    if (periodSelect) periodSelect.value = document.getElementById('report-period')?.value || periodSelect.value;
    const query = reportQuery({
        grade: document.getElementById('notes-report-grade')?.value,
        period: document.getElementById('notes-report-period')?.value,
        section: 'all',
    });
    const params = new URLSearchParams(query);
    const response = await fetch(`/teacher/api/reports/gradebook?${params}`);
    const data = await response.json();
    if (!data.success) return;

    document.getElementById('report-average').textContent = `${data.average ?? 'Pendiente'}${data.average_status === 'provisional' ? ' (provisional)' : ''}`;
    document.getElementById('report-ad').textContent = data.counts.destacado;
    document.getElementById('report-a').textContent = data.counts.esperado;
    document.getElementById('report-b').textContent = data.counts.proceso;
    document.getElementById('report-c').textContent = data.counts.apoyo;
    renderReportChart(data.chart || []);

    const body = document.getElementById('report-notes-body');
    if (!body) return;
    if (!data.rows.length) {
        body.innerHTML = '<tr><td colspan="7" class="text-muted">No hay alumnos para este filtro.</td></tr>';
        return;
    }
    body.innerHTML = data.rows.map(row => `
        <tr class="report-note-row" data-id="${row.student_id}" data-name="${row.student_name}" data-grade="${row.grade}" data-score="${row.average}" data-observations="${row.level_label || row.level}" data-section="${row.section || 'A'}">
            <td>${row.n}</td>
            <td><strong>${row.student_name}</strong><br><small class="text-muted">${row.code} · ${row.grade}° ${row.section}</small></td>
            <td>${row.activities}</td>
            <td>${row.evaluations}</td>
            <td><strong>${row.average ?? 'Pendiente'}</strong></td>
            <td>${levelBadge(row.level)}</td>
            <td class="report-institutional-note"></td>
        </tr>
    `).join('');

    const reportRows = document.querySelectorAll('.report-note-row');
    reportRows.forEach(reportRow => {
        reportRow.querySelector('.report-institutional-note').textContent =
            institutionalNote(reportRow.dataset.id, query.period);
        reportRow.addEventListener('click', () => {
            const score = Number(reportRow.dataset.score || 0);
            selectedNotesRow = reportRow;
            window.selectedNotesRow = reportRow;
            document.querySelectorAll('.report-note-row').forEach(r => r.classList.remove('selected'));
            reportRow.classList.add('selected');
            if (window.notesStudentName) window.notesStudentName.value = reportRow.dataset.name || '';
            if (window.selectedStudentScore) window.selectedStudentScore.textContent = String(score);
            if (window.selectedStudentGrade) window.selectedStudentGrade.textContent = `${reportRow.dataset.grade || '0'}°`;
            if (window.selectedStudentNotes) window.selectedStudentNotes.textContent = reportRow.dataset.observations || '—';
            if (window.selectedStudentImage) {
                if (typeof window.updateStatusDisplay === 'function') window.updateStatusDisplay(score);
            }
            if (typeof window.updatePrediction === 'function') {
                window.updatePrediction(reportRow.dataset.name || '', score);
            }
            if (typeof window.loadNotesResults === 'function') {
                window.loadNotesResults();
            }
        });
    });

    if (reportRows.length > 0 && !document.querySelector('.report-note-row.selected')) {
        reportRows[0].click();
    }
}

function downloadExcel(extra = {}) {
    const query = reportQuery(extra);
    const params = new URLSearchParams(query);
    window.location.href = `/teacher/api/reports/export.xlsx?${params}`;
}

document.addEventListener('DOMContentLoaded', () => {
    const loadBtn = document.getElementById('btn-load-report');
    if (loadBtn) loadBtn.addEventListener('click', loadAcademicReport);
    ['report-grade', 'report-period', 'notes-report-grade', 'notes-report-period'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', () => {
            if (id.startsWith('notes-report')) {
                const grade = document.getElementById('notes-report-grade')?.value;
                const period = document.getElementById('notes-report-period')?.value;
                if (document.getElementById('report-grade') && grade) document.getElementById('report-grade').value = grade;
                if (document.getElementById('report-period') && period) document.getElementById('report-period').value = period;
            }
            loadAcademicReport();
        });
    });
    document.getElementById('btn-export-selected-excel')?.addEventListener('click', () => downloadExcel());
    document.getElementById('btn-export-complete-excel')?.addEventListener('click', () => downloadExcel({grade: 'all', complete: 'true'}));
    document.querySelectorAll('[data-export-grade]').forEach(button => {
        button.addEventListener('click', () => {
            const grade = button.dataset.exportGrade;
            downloadExcel(grade === 'all' ? {grade: 'all', complete: 'true'} : {grade});
        });
    });
    if (document.getElementById('section-reportes')) {
        loadAcademicReport();
    }
});

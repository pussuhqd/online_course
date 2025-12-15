/**
 * Главный файл приложения - JavaScript логика
 */

const API_URL = 'http://localhost:5001/api';

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    loadEmployees();
    loadCourses();
    loadRegistrations();
    loadStatistics();
    loadDeletedRecords();
    loadRecommendations();
    populateSelects();

    // Event listeners для форм
    document.getElementById('employeeForm').addEventListener('submit', addEmployee);
    document.getElementById('courseForm').addEventListener('submit', addCourse);
    document.getElementById('registrationForm').addEventListener('submit', addRegistration);

    // Обновление данных каждые 10 секунд
    setInterval(() => {
        loadStatistics();
        loadRecommendations();
    }, 10000);
});

// ==================== ТАБ НАВИГАЦИЯ ====================

function initializeTabs() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Скрыть все контенты
    const contents = document.querySelectorAll('.content');
    contents.forEach(content => content.classList.remove('active'));

    // Убрать активное состояние у всех кнопок
    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(button => button.classList.remove('active'));

    // Показать выбранный контент и активировать кнопку
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Обновить данные при переключении
    if (tabName === 'deleted') {
        loadDeletedRecords();
    }
}

// ==================== УВЕДОМЛЕНИЯ ====================

function showAlert(elementId, message, type = 'success') {
    const alertDiv = document.getElementById(elementId);
    alertDiv.innerHTML = `<div class="alert ${type}">${message}</div>`;
    setTimeout(() => {
        alertDiv.innerHTML = '';
    }, 5000);
}

// ==================== СОТРУДНИКИ ====================

async function loadEmployees() {
    try {
        const response = await fetch(`${API_URL}/employees?deleted=false`);
        const employees = await response.json();
        displayEmployees(employees);
    } catch (error) {
        console.error('Error loading employees:', error);
    }
}

function displayEmployees(employees) {
    const tbody = document.getElementById('employeesList');
    tbody.innerHTML = '';

    if (employees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px;">Нет добавленных сотрудников</td></tr>';
        return;
    }

    employees.forEach(emp => {
        const row = tbody.insertRow();
        const createdDate = new Date(emp.created_at).toLocaleDateString('ru-RU');
        
        row.innerHTML = `
            <td>${emp.id}</td>
            <td><strong>${emp.full_name}</strong></td>
            <td>${emp.position}</td>
            <td>${emp.phone}</td>
            <td>${createdDate}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-small secondary" onclick="viewEmployee(${emp.id})">👁️ Просмотр</button>
                    <button class="btn-small danger" onclick="deleteEmployee(${emp.id})">🗑️ Удалить</button>
                </div>
            </td>
        `;
    });
}

async function addEmployee(e) {
    e.preventDefault();

    const formData = {
        full_name: document.getElementById('empName').value,
        phone: document.getElementById('empPhone').value,
        position: document.getElementById('empPosition').value
    };

    try {
        const response = await fetch(`${API_URL}/employees`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            showAlert('employeeAlert', '✅ Сотрудник успешно добавлен!', 'success');
            document.getElementById('employeeForm').reset();
            loadEmployees();
            populateSelects();
        } else {
            const error = await response.json();
            showAlert('employeeAlert', `❌ Ошибка: ${error.error}`, 'error');
        }
    } catch (error) {
        showAlert('employeeAlert', `❌ Ошибка: ${error.message}`, 'error');
    }
}

async function deleteEmployee(id) {
    if (!confirm('Вы уверены, что хотите удалить этого сотрудника?')) return;

    try {
        const response = await fetch(`${API_URL}/employees/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('employeeAlert', '✅ Сотрудник удалён!', 'success');
            loadEmployees();
            populateSelects();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function searchEmployees() {
    const query = document.getElementById('empSearch').value;
    if (!query) {
        loadEmployees();
        return;
    }

    fetch(`${API_URL}/employees/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => displayEmployees(data))
        .catch(err => console.error('Error:', err));
}

// ==================== КУРСЫ ====================

async function loadCourses() {
    try {
        const response = await fetch(`${API_URL}/courses?deleted=false`);
        const courses = await response.json();
        displayCourses(courses);
    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

function displayCourses(courses) {
    const tbody = document.getElementById('coursesList');
    tbody.innerHTML = '';

    if (courses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px;">Нет добавленных курсов</td></tr>';
        return;
    }

    courses.forEach(course => {
        const row = tbody.insertRow();
        const createdDate = new Date(course.created_at).toLocaleDateString('ru-RU');
        
        row.innerHTML = `
            <td>${course.id}</td>
            <td><strong>${course.title}</strong></td>
            <td>${course.duration_hours}</td>
            <td>${course.certificate_type}</td>
            <td>${createdDate}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-small secondary" onclick="viewCourse(${course.id})">👁️ Просмотр</button>
                    <button class="btn-small danger" onclick="deleteCourse(${course.id})">🗑️ Удалить</button>
                </div>
            </td>
        `;
    });
}

async function addCourse(e) {
    e.preventDefault();

    const formData = {
        title: document.getElementById('courseName').value,
        duration_hours: parseInt(document.getElementById('courseDuration').value),
        certificate_type: document.getElementById('certificateType').value
    };

    try {
        const response = await fetch(`${API_URL}/courses`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            showAlert('courseAlert', '✅ Курс успешно добавлен!', 'success');
            document.getElementById('courseForm').reset();
            loadCourses();
            populateSelects();
        } else {
            const error = await response.json();
            showAlert('courseAlert', `❌ Ошибка: ${error.error}`, 'error');
        }
    } catch (error) {
        showAlert('courseAlert', `❌ Ошибка: ${error.message}`, 'error');
    }
}

async function deleteCourse(id) {
    if (!confirm('Вы уверены, что хотите удалить этот курс?')) return;

    try {
        const response = await fetch(`${API_URL}/courses/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('courseAlert', '✅ Курс удалён!', 'success');
            loadCourses();
            populateSelects();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ==================== РЕГИСТРАЦИИ ====================

async function loadRegistrations() {
    try {
        const response = await fetch(`${API_URL}/registrations?deleted=false`);
        const registrations = await response.json();
        displayRegistrations(registrations);
    } catch (error) {
        console.error('Error loading registrations:', error);
    }
}

function displayRegistrations(registrations) {
    const tbody = document.getElementById('registrationsList');
    tbody.innerHTML = '';

    if (registrations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px;">Нет регистраций на курсы</td></tr>';
        return;
    }

    registrations.forEach(reg => {
        const row = tbody.insertRow();
        const regDate = new Date(reg.registered_at).toLocaleDateString('ru-RU');
        const statusBadge = `<span class="badge ${reg.status}">${getStatusLabel(reg.status)}</span>`;
        
        row.innerHTML = `
            <td>${reg.id}</td>
            <td>${reg.employee_name}</td>
            <td>${reg.course_title}</td>
            <td>${statusBadge}</td>
            <td>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${reg.progress_percent}%"></div>
                </div>
                <small>${reg.progress_percent}%</small>
            </td>
            <td>${regDate}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-small secondary" onclick="updateProgress(${reg.id})">📊 Прогресс</button>
                    <button class="btn-small success" onclick="updateStatus(${reg.id})">✅ Статус</button>
                    <button class="btn-small danger" onclick="deleteRegistration(${reg.id})">🗑️ Удалить</button>
                </div>
            </td>
        `;
    });
}

async function addRegistration(e) {
    e.preventDefault();

    const formData = {
        employee_id: parseInt(document.getElementById('regEmployee').value),
        course_id: parseInt(document.getElementById('regCourse').value)
    };

    try {
        const response = await fetch(`${API_URL}/registrations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            showAlert('registrationAlert', '✅ Сотрудник зачислен на курс!', 'success');
            document.getElementById('registrationForm').reset();
            loadRegistrations();
            loadStatistics();
        } else {
            const error = await response.json();
            showAlert('registrationAlert', `❌ Ошибка: ${error.error}`, 'error');
        }
    } catch (error) {
        showAlert('registrationAlert', `❌ Ошибка: ${error.message}`, 'error');
    }
}

async function updateStatus(regId) {
    const newStatus = prompt('Выберите новый статус:\n1. in_progress (В процессе)\n2. completed (Завершен)');
    if (!newStatus) return;

    let statusValue = newStatus === '1' ? 'in_progress' : newStatus === '2' ? 'completed' : null;
    if (!statusValue) return;

    try {
        const response = await fetch(`${API_URL}/registrations/${regId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: statusValue })
        });

        if (response.ok) {
            showAlert('registrationAlert', '✅ Статус обновлён!', 'success');
            loadRegistrations();
            loadStatistics();
        } else {
            const error = await response.json();
            showAlert('registrationAlert', `❌ Ошибка: ${error.error}`, 'error');
        }
    } catch (error) {
        showAlert('registrationAlert', `❌ Ошибка: ${error.message}`, 'error');
    }
}

async function updateProgress(regId) {
    const progress = prompt('Введите прогресс (0-100):');
    if (progress === null) return;

    try {
        const response = await fetch(`${API_URL}/registrations/${regId}/progress`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ progress_percent: parseInt(progress) })
        });

        if (response.ok) {
            showAlert('registrationAlert', '✅ Прогресс обновлён!', 'success');
            loadRegistrations();
            loadStatistics();
        } else {
            const error = await response.json();
            showAlert('registrationAlert', `❌ Ошибка: ${error.error}`, 'error');
        }
    } catch (error) {
        showAlert('registrationAlert', `❌ Ошибка: ${error.message}`, 'error');
    }
}

async function deleteRegistration(id) {
    if (!confirm('Вы уверены, что хотите удалить эту регистрацию?')) return;

    try {
        const response = await fetch(`${API_URL}/registrations/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('registrationAlert', '✅ Регистрация удалена!', 'success');
            loadRegistrations();
            loadStatistics();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ==================== СТАТИСТИКА ====================

async function loadStatistics() {
    try {
        const response = await fetch(`${API_URL}/statistics`);
        const stats = await response.json();
        displayStatistics(stats);
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

function displayStatistics(stats) {
    const container = document.getElementById('statsContainer');
    const total = stats.by_status.enrolled + stats.by_status.in_progress + stats.by_status.completed;
    
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Всего сотрудников</div>
            <div class="stat-value">${stats.total_employees}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Всего курсов</div>
            <div class="stat-value">${stats.total_courses}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Всего регистраций</div>
            <div class="stat-value">${stats.total_registrations}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Завершено</div>
            <div class="stat-value" style="color: #10b981;">${stats.by_status.completed}</div>
            <div class="stat-percent">${total > 0 ? ((stats.by_status.completed / total) * 100).toFixed(1) : 0}% от всех</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">В процессе</div>
            <div class="stat-value" style="color: #f59e0b;">${stats.by_status.in_progress}</div>
            <div class="stat-percent">${total > 0 ? ((stats.by_status.in_progress / total) * 100).toFixed(1) : 0}% от всех</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Зачислено</div>
            <div class="stat-value" style="color: #2563eb;">${stats.by_status.enrolled}</div>
            <div class="stat-percent">${total > 0 ? ((stats.by_status.enrolled / total) * 100).toFixed(1) : 0}% от всех</div>
        </div>
    `;

    // Диаграмма статусов
    drawStatusChart(stats.by_status);
    
    // Диаграмма популярных курсов
    if (stats.popular_courses.length > 0) {
        drawCourseChart(stats.popular_courses);
    }
}

function drawStatusChart(statusData) {
    const chartDiv = document.getElementById('statusChart');
    const total = statusData.enrolled + statusData.in_progress + statusData.completed;
    
    if (total === 0) {
        chartDiv.innerHTML = '<p style="color: #999; text-align: center;">Нет данных</p>';
        return;
    }

    const enrolledPercent = (statusData.enrolled / total * 100).toFixed(1);
    const inProgressPercent = (statusData.in_progress / total * 100).toFixed(1);
    const completedPercent = (statusData.completed / total * 100).toFixed(1);

    chartDiv.innerHTML = `
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Зачислено</span>
                <strong>${enrolledPercent}%</strong>
            </div>
            <div style="background: #e5e7eb; border-radius: 4px; height: 10px; overflow: hidden;">
                <div style="background: #2563eb; height: 100%; width: ${enrolledPercent}%;"></div>
            </div>
        </div>
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>В процессе</span>
                <strong>${inProgressPercent}%</strong>
            </div>
            <div style="background: #e5e7eb; border-radius: 4px; height: 10px; overflow: hidden;">
                <div style="background: #f59e0b; height: 100%; width: ${inProgressPercent}%;"></div>
            </div>
        </div>
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Завершено</span>
                <strong>${completedPercent}%</strong>
            </div>
            <div style="background: #e5e7eb; border-radius: 4px; height: 10px; overflow: hidden;">
                <div style="background: #10b981; height: 100%; width: ${completedPercent}%;"></div>
            </div>
        </div>
    `;
}

function drawCourseChart(courses) {
    const chartDiv = document.getElementById('courseChart');
    
    if (!courses || courses.length === 0) {
        chartDiv.innerHTML = '<p style="color: #999; text-align: center;">Нет данных</p>';
        return;
    }

    const maxCount = Math.max(...courses.map(c => c.count));
    let html = '';

    courses.forEach(course => {
        const percent = (course.count / maxCount * 100);
        html += `
            <div style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-size: 12px;">${course.title}</span>
                    <strong>${course.count}</strong>
                </div>
                <div style="background: #e5e7eb; border-radius: 4px; height: 8px; overflow: hidden;">
                    <div style="background: #667eea; height: 100%; width: ${percent}%;"></div>
                </div>
            </div>
        `;
    });

    chartDiv.innerHTML = html;
}

// ==================== РЕКОМЕНДАЦИИ ====================

async function loadRecommendations() {
    try {
        const response = await fetch(`${API_URL}/report/recommendations`);
        const recommendations = await response.json();
        displayRecommendations(recommendations);
    } catch (error) {
        console.error('Error loading recommendations:', error);
    }
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendationsContainer');
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p style="color: #999;">Нет доступных рекомендаций</p>';
        return;
    }

    let html = '';
    recommendations.forEach(rec => {
        html += `
            <div class="recommendation-item">
                <div class="recommendation-title">${rec.title}</div>
                <div class="recommendation-description">${rec.description}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ==================== УДАЛЕННЫЕ ЗАПИСИ ====================

async function loadDeletedRecords() {
    try {
        const [empResponse, courseResponse, regResponse] = await Promise.all([
            fetch(`${API_URL}/employees?deleted=true`),
            fetch(`${API_URL}/courses?deleted=true`),
            fetch(`${API_URL}/registrations?deleted=true`)
        ]);

        const employees = await empResponse.json();
        const courses = await courseResponse.json();
        const registrations = await regResponse.json();

        displayDeletedEmployees(employees);
        displayDeletedCourses(courses);
        displayDeletedRegistrations(registrations);
    } catch (error) {
        console.error('Error loading deleted records:', error);
    }
}

function displayDeletedEmployees(employees) {
    const tbody = document.getElementById('deletedEmployeesList');
    tbody.innerHTML = '';

    if (employees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">Нет удаленных сотрудников</td></tr>';
        return;
    }

    employees.forEach(emp => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${emp.id}</td>
            <td>${emp.full_name}</td>
            <td>${emp.position}</td>
            <td>${emp.phone}</td>
            <td>-</td>
        `;
    });
}

function displayDeletedCourses(courses) {
    const tbody = document.getElementById('deletedCoursesList');
    tbody.innerHTML = '';

    if (courses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px;">Нет удаленных курсов</td></tr>';
        return;
    }

    courses.forEach(course => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${course.id}</td>
            <td>${course.title}</td>
            <td>${course.duration_hours}</td>
            <td>-</td>
        `;
    });
}

function displayDeletedRegistrations(registrations) {
    const tbody = document.getElementById('deletedRegistrationsList');
    tbody.innerHTML = '';

    if (registrations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">Нет удаленных регистраций</td></tr>';
        return;
    }

    registrations.forEach(reg => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${reg.id}</td>
            <td>${reg.employee_name}</td>
            <td>${reg.course_title}</td>
            <td>${reg.status}</td>
            <td>-</td>
        `;
    });
}

// ==================== ЭКСПОРТ ====================

function downloadReport() {
    window.location.href = `${API_URL}/report/generate`;
}

// ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

function getStatusLabel(status) {
    const labels = {
        'enrolled': 'Зачислен',
        'in_progress': 'В процессе',
        'completed': 'Завершен'
    };
    return labels[status] || status;
}

async function populateSelects() {
    try {
        const [empResponse, courseResponse] = await Promise.all([
            fetch(`${API_URL}/employees?deleted=false`),
            fetch(`${API_URL}/courses?deleted=false`)
        ]);

        const employees = await empResponse.json();
        const courses = await courseResponse.json();

        const empSelect = document.getElementById('regEmployee');
        const courseSelect = document.getElementById('regCourse');

        empSelect.innerHTML = '<option value="">Выберите сотрудника</option>';
        employees.forEach(emp => {
            const option = document.createElement('option');
            option.value = emp.id;
            option.textContent = emp.full_name;
            empSelect.appendChild(option);
        });

        courseSelect.innerHTML = '<option value="">Выберите курс</option>';
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = course.title;
            courseSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error populating selects:', error);
    }
}
function viewHtmlReport() {
    fetch('/api/report/view-html')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
            setTimeout(() => window.URL.revokeObjectURL(url), 100);
        })
        .catch(() => showNotification('Ошибка при генерации отчёта', 'danger'));
}

function downloadHtmlReport() {
    fetch('/api/report/download-html')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `course_report_${new Date().toLocaleDateString().replace(/\//g, '_')}.html`;
            a.click();
            window.URL.revokeObjectURL(url);
            showNotification('Отчёт скачан! (2 листа A4)', 'success');
        })
        .catch(() => showNotification('Ошибка при скачивании', 'danger'));
}

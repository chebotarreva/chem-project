// Конфигурация API
const API_BASE_URL = '/api'; // Nginx проксирует /api → FastAPI
let currentPage = 1;
const pageSize = 10;

// ====================
// УТИЛИТЫ
// ====================

// Показать сообщение
function showMessage(elementId, message, type = 'info') {
    const element = document.getElementById(elementId);
    element.innerHTML = `<p class="${type}">${message}</p>`;
    element.style.display = 'block';
}

// Очистить сообщение
function clearMessage(elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    element.style.display = 'none';
}

// Проверка статуса сервисов
async function checkServices() {
    try {
        const res = await fetch(`${API_BASE_URL}/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        console.log("Данные health check:", data);

        // ТВОЯ СТРУКТУРА JSON: data.services.database, data.services.redis
        const dbStatus = data.services?.database || "unknown";
        const redisStatus = data.services?.redis || "unknown";
        const apiStatus = data.status || "unknown";

        document.getElementById("apiStatus").innerHTML =
            `API: <span class="${apiStatus === "healthy" ? "online" : "offline"}">${apiStatus}</span>`;
        document.getElementById("dbStatus").innerHTML =
            `База данных: <span class="${dbStatus === "connected" ? "online" : "offline"}">${dbStatus}</span>`;
        document.getElementById("redisStatus").innerHTML =
            `Redis: <span class="${redisStatus === "connected" ? "online" : "offline"}">${redisStatus}</span>`;

    } catch (error) {
        console.error("ОШИБКА проверки сервисов:", error);
        document.getElementById("apiStatus").innerHTML =
            'API: <span class="offline">не доступен</span>';
    }
}

// ====================
// ТАБЫ
// ====================

document.querySelectorAll('.tab-link').forEach(button => {
    button.addEventListener('click', () => {
        // Убрать активный класс у всех вкладок
        document.querySelectorAll('.tab-link').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Активировать выбранную вкладку
        button.classList.add('active');
        const tabId = button.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');

        // Если открыли вкладку списка молекул — загрузить их
        if (tabId === 'list') {
            loadMolecules();
        }
    });
});

// ====================
// ДОБАВЛЕНИЕ МОЛЕКУЛЫ
// ====================

document.getElementById('addMoleculeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessage('addResult');

    const name = document.getElementById('name').value.trim();
    const smiles = document.getElementById('smiles').value.trim();

    if (!name || !smiles) {
        showMessage('addResult', 'Заполните все поля.', 'error');
        return;
    }

    showMessage('addResult', '<i class="fas fa-spinner fa-spin"></i> Молекула добавляется...', 'loading');

    try {
        const response = await fetch(`${API_BASE_URL}/molecules/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, smiles })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('addResult', `
                <strong>Успешно добавлено!</strong><br>
                ID: ${data.id}<br>
                Название: ${data.name}<br>
                SMILES: <code>${data.smiles}</code>
            `, 'success');
            // Очищаем форму
            document.getElementById('addMoleculeForm').reset();
        } else {
            showMessage('addResult', `ОШИБКА: ${data.detail || 'Неизвестная ОШИБКА'}`, 'error');
        }
    } catch (error) {
        showMessage('addResult', `ОШИБКА сети: ${error.message}`, 'error');
    }
});

// ====================
// ЗАГРУЗКА СПИСКА МОЛЕКУЛ
// ====================

async function loadMolecules() {
    const container = document.getElementById('moleculesList');
    container.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i>молекулы загружаются...</p>';

    try {
        // ИСПРАВЛЕНО: используем параметры page и page_size вместо skip и limit
        const response = await fetch(`${API_BASE_URL}/molecules/?page=${currentPage}&page_size=${pageSize}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        console.log('Данные от API:', data);

        // ВАЖНО: структура ответа: {molecules: [...], total: X, page: N, page_size: Y, total_pages: Z}
        const moleculesArray = data.molecules || [];
        const totalMolecules = data.total || 0;
        const totalPages = data.total_pages || Math.ceil(totalMolecules / pageSize);

        container.innerHTML = '';

        if (moleculesArray.length === 0) {
            container.innerHTML = '<p class="result">База данных пуста. Добавьте первую молекулу!</p>';
            return;
        }

        moleculesArray.forEach(molecule => {
            const card = document.createElement('div');
            card.className = 'molecule-card';
            card.innerHTML = `
                <h3>${molecule.name || 'Без названия'}</h3>
                <p><strong>ID:</strong> ${molecule.id}</p>
                <p><strong>SMILES:</strong> <span class="smiles">${molecule.smiles}</span></p>
                <div style="margin-top: 15px;">
                    <button onclick="deleteMolecule(${molecule.id})" class="btn-secondary" style="padding: 5px 10px; font-size: 0.9rem;">
                        <i class="fas fa-trash"></i> Удалить
                    </button>
                </div>
            `;
            container.appendChild(card);
        });

        // Используем total_pages из ответа API
        document.getElementById('pageInfo').textContent = `Страница ${currentPage} из ${totalPages}`;

        // Правильно блокируем кнопки пагинации
        document.getElementById('prevPage').disabled = currentPage <= 1;
        document.getElementById('nextPage').disabled = currentPage >= totalPages;

    } catch (error) {
        console.error('ОШИБКА загрузки молекул:', error);
        container.innerHTML = `<p class="error">ОШИБКА загрузки: ${error.message}</p>`;
    }
}
// Пагинация
document.getElementById('prevPage').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadMolecules();
    }
});

document.getElementById('nextPage').addEventListener('click', () => {
    currentPage++;
    loadMolecules();
});

document.getElementById('loadMolecules').addEventListener('click', loadMolecules);

// Удаление молекулы
async function deleteMolecule(id) {
    if (!confirm(`Удалить молекулу с ID ${id}?`)) return;

    try {
        const response = await fetch(`${API_BASE_URL}/molecules/${id}`, { method: 'DELETE' });
        if (response.ok) {
            alert('Молекула удалена!');
            loadMolecules(); // Обновляем список
        } else {
            const data = await response.json();
            alert(`ОШИБКА: ${data.detail}`);
        }
    } catch (error) {
        alert(`ОШИБКА сети: ${error.message}`);
    }
}

// ====================
// СИНХРОННЫЙ ПОИСК
// ====================

document.getElementById("searchForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessage("searchResult");

    const substructure = document.getElementById("substructure").value.trim();
    if (!substructure) {
        showMessage("searchResult", "Введите SMILES субструктуры.", "error");
        return;
    }

    showMessage("searchResult", '<i class="fas fa-spinner fa-spin"></i> Поиск...', "loading");

    try {
        const response = await fetch(`${API_BASE_URL}/search/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ substructure })
        });

        const data = await response.json();
        console.log("Результат поиска:", data); // Для отладки

        if (response.ok) {
            if (data.found_count > 0) {
                // Формируем список с ID, названием и SMILES
                const list = data.results.map(mol =>
                    `<li>
                        <strong>${mol.name || "Без названия"}</strong>
                        (ID: ${mol.id})<br>
                        <code class="smiles">${mol.smiles}</code>
                    </li>`
                ).join('');

                let cacheInfo = "";
                if (data.cached) {
                    cacheInfo = '<small><i class="fas fa-bolt"></i> Результат из кеша</small><br>';
                }

                showMessage("searchResult", `
                    ${cacheInfo}
                    <strong>Нашлось ${data.found_count} молекул:</strong>
                    <ul class="search-results">${list}</ul>
                `, "success");
            } else {
                showMessage("searchResult", "Ничего не нашлось. Попробуйте другую субструктуру.", "info");
            }
        } else {
            showMessage("searchResult", `ОШИБКА: ${data.detail || "Неизвестная ошибка"}`, "error");
        }
    } catch (error) {
        showMessage("searchResult", `ОШИБКА сети: ${error.message}`, "error");
    }
});

// ====================
// АСИНХРОННЫЙ ПОИСК
// ====================

let currentTaskId = null;

document.getElementById('asyncSearchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessage('asyncTaskStatus');
    clearMessage('asyncTaskResult');

    const substructure = document.getElementById('asyncSubstructure').value.trim();
    if (!substructure) {
        showMessage('asyncTaskStatus', 'Введите SMILES субструктуры.', 'error');
        return;
    }

    showMessage('asyncTaskStatus', '<i class="fas fa-spinner fa-spin"></i> Запускаем асинхронную задачу...', 'loading');

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/search/async`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ substructure })
        });

        const data = await response.json();

        if (response.ok) {
            currentTaskId = data.task_id;
            showMessage('asyncTaskStatus', `
                Задача запущена!<br>
                <strong>ID задачи:</strong> ${data.task_id}<br>
                <button onclick="checkTaskStatus()" class="btn-secondary">
                    <i class="fas fa-sync-alt"></i> Проверить статус
                </button>
            `, 'success');
        } else {
            showMessage('asyncTaskStatus', `ОШИБКА: ${data.detail}`, 'error');
        }
    } catch (error) {
        showMessage('asyncTaskStatus', `ОШИБКА сети: ${error.message}`, 'error');
    }
});

// Проверка статуса задачи
async function checkTaskStatus() {
    if (!currentTaskId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${currentTaskId}/status`);
        const data = await response.json();

        let statusHtml = `<strong>Статус задачи ${currentTaskId}:</strong> ${data.status}`;

        if (data.status === "SUCCESS") {
            // Получаем результат
            const resultRes = await fetch(`${API_BASE_URL}/tasks/${currentTaskId}/result`);
            const resultData = await resultRes.json();
            console.log("Результат:", resultData);

            if (resultData.result && resultData.result.found_count > 0) {
                const list = resultData.result.results.map(mol =>
                    `<li>
                        <strong>${mol.name || "Без названия"}</strong>
                        (ID: ${mol.id})<br>
                        <code class="smiles">${mol.smiles}</code>
                    </li>`
                ).join('');

                statusHtml += '<br>УСПЕХ! Задача завершена!';
                showMessage("asyncTaskResult",
                    `<strong>Результаты (${resultData.result.found_count}):</strong>
                    <ul class="search-results">${list}</ul>`,
                    "success");
            } else if (resultData.result && resultData.result.found_count === 0) {
                statusHtml += '<br>УСПЕХ! Задача завершена!';
                showMessage("asyncTaskResult", "🔍 Ничего не найдено.", "info");
            } else if (resultData.result && resultData.result.error) {
                statusHtml += '<br>ОШИБКА: задача завершилась с ошибкой.';
                showMessage("asyncTaskResult", `Ошибка: ${resultData.result.error}`, "error");
            }
        } else if (data.status === 'FAILURE') {
            statusHtml += '<br>ОШИБКА! Задача завершилась с ошибкой.';
        } else if (data.status === 'PENDING' || data.status === "PROGRESS") {
            statusHtml += '<br>Задача ещё выполняется...';
            // Обновляем прогресс, если есть
            if (data.progress) {
                statusHtml += `<br>Прогресс: ${data.progress}%`;
            }
            // Проверим снова через 2 секунды
            setTimeout(checkTaskStatus, 2000);
        }

        showMessage('asyncTaskStatus', statusHtml, 'info');
    } catch (error) {
        console.error("ОШИБКА проверки статуса:", error);
        showMessage('asyncTaskStatus', `ОШИБКА проверки статуса: ${error.message}`, 'error');
    }
}

// ====================
// ИНИЦИАЛИЗАЦИЯ
// ====================

// При загрузке страницы проверяем сервисы
document.addEventListener('DOMContentLoaded', () => {
    checkServices();
    // Проверять сервисы каждые 30 секунд
    setInterval(checkServices, 30000);
});
// Полностью переписанный admin.js
console.log("🎯 ADMIN.JS ЗАГРУЖЕН - ПРИВЯЗКА КНИГ ДОЛЖНА РАБОТАТЬ");

document.addEventListener('DOMContentLoaded', function() {
    console.log("🔄 ADMIN.JS ЗАГРУЖЕН");

    // ===== 1. ДИНАМИЧЕСКАЯ ЗАГРУЗКА БИБЛИОТЕК =====
    initializeLibrarySelects();

    // ===== 2. ОСНОВНЫЕ ОБРАБОТЧИКИ =====
    initializeMainHandlers();

    // ===== 3. СВОРАЧИВАНИЕ ПАНЕЛЕЙ =====
    initializeCollapsePanels();

    // ===== 4. AJAX ФОРМЫ =====
    initializeAjaxForms();

    // ===== 5. УПРАВЛЕНИЕ ЭКЗЕМПЛЯРАМИ КНИГ =====
    initializeCopiesManagement();

    console.log("✅ ВСЕ СКРИПТЫ ИНИЦИАЛИЗИРОВАНЫ");
});

// ===== ФУНКЦИИ =====

function initializeLibrarySelects() {
    console.log("📚 Инициализация выбора библиотек...");
    
    const addBookSelect = document.getElementById('add-book-select');
    const addLibrarySelect = document.getElementById('add-library-select');
    const addRelationBtn = document.getElementById('add-relation-btn');
    
    const deleteBookSelect = document.getElementById('delete-book-select');
    const deleteLibrarySelect = document.getElementById('delete-library-select');
    const deleteRelationBtn = document.getElementById('delete-relation-btn');

    // Обработчики для добавления связи
    if (addBookSelect && addLibrarySelect) {
        addBookSelect.addEventListener('change', function() {
            const bookId = this.value;
            if (!bookId) {
                resetSelect(addLibrarySelect, '-- Сначала выберите книгу --', true);
                addRelationBtn.disabled = true;
                return;
            }
            loadLibraries(bookId, 'without-book', addLibrarySelect, addRelationBtn);
        });

        addLibrarySelect.addEventListener('change', function() {
            addRelationBtn.disabled = !this.value;
        });
    }

    // Обработчики для удаления связи
    if (deleteBookSelect && deleteLibrarySelect) {
        deleteBookSelect.addEventListener('change', function() {
            const bookId = this.value;
            if (!bookId) {
                resetSelect(deleteLibrarySelect, '-- Сначала выберите книгу --', true);
                deleteRelationBtn.disabled = true;
                return;
            }
            loadLibraries(bookId, 'with-book', deleteLibrarySelect, deleteRelationBtn);
        });

        deleteLibrarySelect.addEventListener('change', function() {
            deleteRelationBtn.disabled = !this.value;
        });
    }
}

function initializeMainHandlers() {
    console.log("🔧 Инициализация основных обработчиков...");
    
    // Уведомления
    window.showNotification = function(message, type = 'success') {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toast = new bootstrap.Toast(document.getElementById(toastId), { 
            autohide: true, 
            delay: 3000 
        });
        toast.show();
        
        // Автоудаление после скрытия
        document.getElementById(toastId).addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    };

    // Обработчики для обычных форм (НЕ табличных)
    document.querySelectorAll('form[method="post"]').forEach(form => {
        if (!form.closest('table')) {
            form.addEventListener('submit', handleFormSubmit);
        }
    });
    
    // Обработчики удаления
    document.querySelectorAll('a[href*="/delete/"]').forEach(link => {
        link.addEventListener('click', handleDeleteClick);
    });
}

function initializeCollapsePanels() {
    console.log("📦 Инициализация сворачивания панелей...");
    
    const collapseToggles = document.querySelectorAll('.collapse-toggle');
    console.log(`🎯 Найдено переключателей: ${collapseToggles.length}`);

    // Инициализация переключателей
    collapseToggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-bs-target');
        const targetElement = document.querySelector(targetId);
        const cardElement = targetElement.closest('.card');
        const storageKey = `panel-${targetId}-collapsed`;
        
        // Восстанавливаем состояние
        const isCollapsed = localStorage.getItem(storageKey) === 'true';
        if (isCollapsed) {
            collapsePanel(targetElement, cardElement, toggle, true);
        }
        
        // Обработчик клика
        toggle.addEventListener('click', function() {
            const targetId = this.getAttribute('data-bs-target');
            const targetElement = document.querySelector(targetId);
            const cardElement = targetElement.closest('.card');
            const storageKey = `panel-${targetId}-collapsed`;
            
            if (targetElement.classList.contains('collapsed')) {
                expandPanel(targetElement, cardElement, this);
                localStorage.setItem(storageKey, 'false');
            } else {
                collapsePanel(targetElement, cardElement, this);
                localStorage.setItem(storageKey, 'true');
            }
            
            setTimeout(updateGlobalToggle, 450);
        });
    });

    // Создаем глобальную кнопку
    createGlobalToggle();
}

function initializeTableEditForms() {
    console.log("📝 Инициализация форм редактирования в таблицах...");
    
    // Ждем немного чтобы DOM полностью загрузился
    setTimeout(() => {
        const tableForms = document.querySelectorAll('table form');
        console.log(`📋 Найдено форм в таблицах: ${tableForms.length}`);
        
        tableForms.forEach((form, index) => {
            if (form.action.includes('/edit/')) {
                console.log(`🎯 Форма редактирования ${index + 1}:`, form.action);
                
                // УДАЛЯЕМ ВСЕ СУЩЕСТВУЮЩИЕ ОБРАБОТЧИКИ
                const newForm = form.cloneNode(true);
                form.parentNode.replaceChild(newForm, form);
                
                // НАЗНАЧАЕМ НОВЫЙ ОБРАБОТЧИК
                newForm.addEventListener('submit', function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    event.stopImmediatePropagation();
                    
                    console.log("🔥 ОТПРАВКА ФОРМЫ РЕДАКТИРОВАНИЯ:", this.action);
                    
                    handleTableFormSubmit(this);
                });
            }
        });
    }, 200);
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

function loadLibraries(bookId, type, selectElement, buttonElement) {
    selectElement.innerHTML = '<option value="">Загрузка...</option>';
    selectElement.disabled = false;
    
    // ИСПРАВЛЕННЫЙ URL - убрано дублирование "book"
    fetch(`/admin/api/libraries/${type}/${bookId}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(libraries => {
            if (libraries.length === 0) {
                selectElement.innerHTML = `<option value="">Нет доступных библиотек</option>`;
                buttonElement.disabled = true;
            } else {
                selectElement.innerHTML = '<option value="">-- Выберите библиотеку --</option>';
                libraries.forEach(library => {
                    selectElement.innerHTML += `<option value="${library.id}">${library.name} — ${library.address}</option>`;
                });
                buttonElement.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            selectElement.innerHTML = '<option value="">Ошибка загрузки</option>';
            buttonElement.disabled = true;
        });
}

function resetSelect(selectElement, placeholder, disabled) {
    selectElement.innerHTML = `<option value="">${placeholder}</option>`;
    selectElement.disabled = disabled;
}

// Обработчики форм
function handleFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Сохранение...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (response.ok) {
            showNotification('Успешно сохранено!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error('Server error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка сохранения', 'danger');
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    });
}

function handleTableFormSubmit(form) {
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const originalHTML = submitButton.innerHTML;
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (response.ok) {
            showNotification('Изменения сохранены!', 'success');
            setTimeout(() => location.reload(), 800);
        } else {
            throw new Error('Server error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка при сохранении', 'danger');
        submitButton.disabled = false;
        submitButton.innerHTML = originalHTML;
    });
}

function handleDeleteClick(event) {
    event.preventDefault();
    
    if (!confirm('Вы уверены?')) return;
    
    const link = event.target.closest('a');
    const originalText = link.textContent;
    
    link.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    link.style.pointerEvents = 'none';
    
    fetch(link.href, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (response.ok) {
            showNotification('Удалено!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error('Server error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка удаления', 'danger');
        link.textContent = originalText;
        link.style.pointerEvents = 'auto';
    });
}

// Функции для сворачивания панелей
function collapsePanel(targetElement, cardElement, toggle, instant = false) {
    if (instant) {
        targetElement.style.height = '0';
        targetElement.classList.add('collapsed');
        cardElement.classList.add('collapsed-card');
        toggle.classList.remove('arrow-up');
        toggle.classList.add('arrow-down');
        return;
    }
    
    const startHeight = targetElement.scrollHeight;
    targetElement.style.height = startHeight + 'px';
    targetElement.classList.add('collapsing');
    
    requestAnimationFrame(() => {
        targetElement.style.height = '0';
        setTimeout(() => {
            targetElement.classList.remove('collapsing');
            targetElement.classList.add('collapsed');
            cardElement.classList.add('collapsed-card');
            toggle.classList.remove('arrow-up');
            toggle.classList.add('arrow-down');
            targetElement.style.height = '';
        }, 400);
    });
}

function expandPanel(targetElement, cardElement, toggle) {
    targetElement.classList.remove('collapsed');
    cardElement.classList.remove('collapsed-card');
    
    const startHeight = targetElement.scrollHeight;
    targetElement.style.height = '0';
    targetElement.classList.remove('collapsing');
    
    requestAnimationFrame(() => {
        targetElement.style.height = startHeight + 'px';
        targetElement.classList.add('collapsing');
        setTimeout(() => {
            targetElement.classList.remove('collapsing');
            toggle.classList.remove('arrow-down');
            toggle.classList.add('arrow-up');
            targetElement.style.height = '';
        }, 400);
    });
}

function createGlobalToggle() {
    const collapseToggles = document.querySelectorAll('.collapse-toggle');
    const globalToggle = document.createElement('button');
    globalToggle.className = 'btn btn-outline-primary btn-sm mb-3';
    globalToggle.id = 'toggle-all-panels';

    function updateButtonText() {
        const collapsedCount = Array.from(collapseToggles).filter(toggle => 
            toggle.classList.contains('arrow-down')
        ).length;
        const totalCount = collapseToggles.length;
        const expandedCount = totalCount - collapsedCount;

        if (collapsedCount === totalCount) {
            globalToggle.innerHTML = '<span class="me-2">ᨆ</span> Развернуть все';
        } else if (expandedCount === 1) {
            globalToggle.innerHTML = '<span class="me-2">ᨆ</span> Развернуть остальные';
        } else if (expandedCount === 2 && totalCount === 3) {
            globalToggle.innerHTML = '<span class="me-2">ᨈ</span> Свернуть все';
        } else if (expandedCount === totalCount) {
            globalToggle.innerHTML = '<span class="me-2">ᨈ</span> Свернуть все';
        } else {
            globalToggle.innerHTML = `<span class="me-2">ᨈ</span> Свернуть все (${expandedCount}/${totalCount})`;
        }
    }

    function determineAction() {
        const collapsedCount = Array.from(collapseToggles).filter(toggle => 
            toggle.classList.contains('arrow-down')
        ).length;
        const expandedCount = collapseToggles.length - collapsedCount;

        return (collapsedCount === collapseToggles.length || expandedCount === 1) ? 'expand' : 'collapse';
    }

    updateButtonText();

    globalToggle.addEventListener('click', function() {
        const action = determineAction();
        collapseToggles.forEach(toggle => {
            const targetId = toggle.getAttribute('data-bs-target');
            const targetElement = document.querySelector(targetId);
            const cardElement = targetElement.closest('.card');
            
            if (action === 'expand') {
                expandPanel(targetElement, cardElement, toggle);
                localStorage.setItem(`panel-${targetId}-collapsed`, 'false');
            } else {
                collapsePanel(targetElement, cardElement, toggle);
                localStorage.setItem(`panel-${targetId}-collapsed`, 'true');
            }
        });
        setTimeout(updateButtonText, 450);
    });

    const container = document.querySelector('.container');
    const existingToggle = document.getElementById('toggle-all-panels');
    if (existingToggle) existingToggle.remove();
    if (container) container.insertBefore(globalToggle, container.firstChild);

    window.updateGlobalToggle = updateButtonText;
}

// AJAX формы (обычные)
function initializeAjaxForms() {
    console.log("🔄 Инициализация AJAX форм...");
    
    // Ищем только формы с классом .ajax-form, но НЕ .quantity-update-form
    const ajaxForms = document.querySelectorAll('.ajax-form:not(.quantity-update-form)');
    console.log(`📋 Найдено AJAX форм (без форм обновления количества): ${ajaxForms.length}`);
    
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log("🎯 AJAX отправка формы:", this.action);
            
            const formData = new FormData(this);
            const submitButton = document.querySelector(`button[form="${this.id}"]`);
            
            if (submitButton) {
                const originalHTML = submitButton.innerHTML;
                const originalText = submitButton.textContent;
                
                // Показываем загрузку
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Сохранение...';
                
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("✅ Ответ от сервера:", data);
                    
                    if (data.success) {
                        showNotification(data.message, 'success');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        throw new Error(data.error || 'Unknown error');
                    }
                })
                .catch(error => {
                    console.error('❌ Ошибка:', error);
                    showNotification('Ошибка при сохранении: ' + error.message, 'danger');
                    
                    // Восстанавливаем кнопку
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalHTML;
                    submitButton.textContent = originalText;
                });
            }
        });
    });
}

// Управление экземплярами книг
function initializeCopiesManagement() {
    console.log("📊 Инициализация управления экземплярами...");
    
    const librarySelect = document.getElementById('library-select-stats');
    const loadStatsBtn = document.getElementById('load-stats-btn');
    
    if (librarySelect && loadStatsBtn) {
        // Активировать кнопку при выборе библиотеки
        librarySelect.addEventListener('change', function() {
            loadStatsBtn.disabled = !this.value;
        });
        
        // Обработчик загрузки статистики
        loadStatsBtn.addEventListener('click', function() {
            const libraryId = librarySelect.value;
            if (!libraryId) return;
            
            loadLibraryDetails(libraryId);
        });
        
        // Инициализация форм при загрузке (если они уже есть на странице)
        setTimeout(() => {
            initializeQuantityForms();
        }, 100);
    }
}

function loadLibraryDetails(libraryId) {
    const loadBtn = document.getElementById('load-stats-btn');
    const originalText = loadBtn.textContent;
    
    loadBtn.disabled = true;
    loadBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Загрузка...';
    
    // Скрываем старые данные
    document.getElementById('stats-block').classList.add('d-none');
    document.getElementById('management-block').classList.add('d-none');
    document.getElementById('reservations-block').classList.add('d-none');
    document.getElementById('no-data-message').classList.remove('d-none');
    
    fetch(`/admin/api/library/${libraryId}/details`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log("📊 Получены данные библиотеки:", data);
            
            if (data.success) {
                displayLibraryStats(data.data);
                displayBooksTable(data.data.books);
                displayReservations(data.data.reservations);
                document.getElementById('no-data-message').classList.add('d-none');
            } else {
                throw new Error(data.error || 'Неизвестная ошибка');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка загрузки данных:', error);
            showNotification('Ошибка загрузки данных: ' + error.message, 'danger');
        })
        .finally(() => {
            loadBtn.disabled = false;
            loadBtn.textContent = originalText;
        });
}

function displayLibraryStats(data) {
    const stats = data.stats;
    
    // Обновляем статистику
    document.getElementById('total-books').textContent = stats.total_books;
    document.getElementById('total-copies').textContent = stats.total_copies;
    document.getElementById('available-copies').textContent = stats.available_copies;
    document.getElementById('reserved-copies').textContent = stats.reserved_copies;
    
    // Показываем блок статистики
    document.getElementById('stats-block').classList.remove('d-none');
}

function displayBooksTable(books) {
    const tableBody = document.getElementById('books-table-body');
    const tableBlock = document.getElementById('management-block');
    const libraryId = document.getElementById('library-select-stats').value;
    
    if (books.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    Нет книг в этой библиотеке
                </td>
            </tr>
        `;
    } else {
        tableBody.innerHTML = '';
        
        books.forEach(book => {
            const row = document.createElement('tr');
            row.id = `book-row-${book.book_id}`;
            
            // Создаем форму с классом ajax-form
            row.innerHTML = `
                <td>${book.title}</td>
                <td>${book.author}</td>
                <td>
                    <span class="badge bg-primary rounded-pill">${book.total_quantity}</span>
                </td>
                <td>
                    <span class="badge bg-success rounded-pill">${book.available_quantity}</span>
                </td>
                <td>
                    <span class="badge bg-warning rounded-pill">${book.reserved_quantity}</span>
                </td>
                <td>
                    <form class="ajax-form quantity-update-form" 
                          data-action="/admin/api/book_library/update_quantity"
                          style="width: 180px;">
                        <input type="hidden" name="book_id" value="${book.book_id}">
                        <input type="hidden" name="library_id" value="${libraryId}">
                        <div class="input-group input-group-sm">
                            <input type="number" 
                                   class="form-control quantity-input" 
                                   value="${book.total_quantity}" 
                                   min="${book.reserved_quantity}" 
                                   max="100"
                                   name="quantity"
                                   required>
                            <button class="btn btn-outline-primary" 
                                    type="submit">
                                Обновить
                            </button>
                        </div>
                        <small class="text-muted d-block mt-1">
                            Мин: ${book.reserved_quantity} (активные брони)
                        </small>
                    </form>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // Инициализируем AJAX обработчики для новых форм
        initializeQuantityForms();
    }
    
    tableBlock.classList.remove('d-none');
}

function initializeQuantityForms() {
    console.log("🔄 Инициализация форм обновления количества...");
    
    const quantityForms = document.querySelectorAll('.quantity-update-form');
    console.log(`📋 Найдено форм обновления количества: ${quantityForms.length}`);
    
    quantityForms.forEach(form => {
        // Удаляем существующие обработчики
        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        
        // Добавляем новый обработчик
        newForm.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log("🎯 AJAX отправка формы обновления количества");
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            
            if (submitButton) {
                const originalHTML = submitButton.innerHTML;
                const originalText = submitButton.textContent;
                
                // Показываем загрузку
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
                
                // Преобразуем FormData в JSON
                const jsonData = {};
                formData.forEach((value, key) => {
                    jsonData[key] = key === 'quantity' ? parseInt(value) : value;
                });
                
                fetch('/admin/api/book_library/update_quantity', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(jsonData)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("✅ Ответ от сервера:", data);
                    
                    if (data.success) {
                        showNotification('Количество обновлено!', 'success');
                        
                        // Обновляем данные в таблице
                        const libraryId = document.getElementById('library-select-stats').value;
                        setTimeout(() => {
                            loadLibraryDetails(libraryId);
                        }, 500);
                    } else {
                        throw new Error(data.error || 'Unknown error');
                    }
                })
                .catch(error => {
                    console.error('❌ Ошибка:', error);
                    showNotification('Ошибка при обновлении: ' + error.message, 'danger');
                    
                    // Восстанавливаем кнопку
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalHTML;
                    submitButton.textContent = originalText;
                });
            }
        });
    });
}

function displayReservations(reservations) {
    const reservationsBody = document.getElementById('reservations-body');
    const reservationsBlock = document.getElementById('reservations-block');
    
    if (reservations.length === 0) {
        reservationsBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    Нет активных броней
                </td>
            </tr>
        `;
    } else {
        reservationsBody.innerHTML = '';
        
        reservations.forEach(res => {
            const row = document.createElement('tr');
            
            let daysText = '';
            if (res.days_left === 0) {
                daysText = '<span class="badge bg-danger">Сегодня истекает</span>';
            } else if (res.days_left === 1) {
                daysText = '<span class="badge bg-warning">1 день</span>';
            } else {
                daysText = `<span class="badge bg-info">${res.days_left} дней</span>`;
            }
            
            row.innerHTML = `
                <td>${res.book_title}</td>
                <td>${res.user_name}</td>
                <td>${res.reservation_date}</td>
                <td>${res.expiry_date} (${daysText})</td>
            `;
            
            reservationsBody.appendChild(row);
        });
    }
    
    reservationsBlock.classList.remove('d-none');
}

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Book(db.Model): #comment for testing
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    libraries = db.relationship('Library', secondary='book_library', backref='books')

class Library(db.Model):
    __tablename__ = 'library'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)

class BookLibrary(db.Model):
    __tablename__ = 'book_library'
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey('library.id'), primary_key=True)
    quantity = db.Column(db.Integer, default=1)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user')  # ← НОВОЕ ПОЛЕ

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

class BookReservation(db.Model):
    __tablename__ = 'book_reservation'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    library_id = db.Column(db.Integer, db.ForeignKey('library.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expiry_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    book = db.relationship('Book', backref='reservations')
    library = db.relationship('Library', backref='reservations')
    user = db.relationship('User', backref='reservations')

# --- Вспомогательные функции ---
def get_available_libraries_for_book(book_id):
    """Получить список библиотек, где книга доступна для бронирования"""
    book = Book.query.get(book_id)
    if not book:
        return []
    
    available_libraries = []
    
    for library in book.libraries:
        # Находим связь книга-библиотека
        book_library = BookLibrary.query.filter_by(
            book_id=book_id,
            library_id=library.id
        ).first()
        
        if not book_library:
            continue
            
        # Считаем активные брони для этой книги в этой библиотеке
        active_reservation_count = BookReservation.query.filter_by(
            book_id=book_id,
            library_id=library.id,
            is_active=True
        ).count()
        
        # Книга доступна если: Активных броней < Общего количества
        # ТЕПЕРЬ ИСПОЛЬЗУЕМ ВЫЧИСЛЕНИЕ!
        if active_reservation_count < book_library.quantity:
            available_libraries.append(library)
    
    return available_libraries

def is_book_available_in_any_library(book_id):
    """Проверить, доступна ли книга для бронирования в любой библиотеке"""
    book = Book.query.get(book_id)
    if not book:
        return False
    
    for library in book.libraries:
        book_library = BookLibrary.query.filter_by(
            book_id=book_id,
            library_id=library.id
        ).first()
        
        if not book_library:
            continue
            
        active_reservation_count = BookReservation.query.filter_by(
            book_id=book_id,
            library_id=library.id,
            is_active=True
        ).count()
        
        if active_reservation_count < book_library.quantity:
            return True
    
    return False

def get_libraries_without_book(book_id):
    """Получить библиотеки, с которыми книга НЕ связана"""
    book = Book.query.get(book_id)
    if not book:
        return []
    
    # Все библиотеки минус те, с которыми книга уже связана
    all_libraries = Library.query.all()
    linked_library_ids = [lib.id for lib in book.libraries]
    
    return [lib for lib in all_libraries if lib.id not in linked_library_ids]

def get_libraries_with_book(book_id):
    """Получить библиотеки, с которыми книга связана"""
    book = Book.query.get(book_id)
    if not book:
        return []
    
    return book.libraries

def update_expired_reservations():
    """Автоматически освобождает просроченные брони"""
    now = datetime.now(timezone.utc)
    
    expired_reservations = BookReservation.query.filter(
        BookReservation.is_active == True,
        BookReservation.expiry_date < now
    ).all()
    
    for reservation in expired_reservations:
        reservation.is_active = False
    
    if expired_reservations:
        db.session.commit()
        print(f"Освобождено {len(expired_reservations)} просроченных броней")
    
    return len(expired_reservations)

@app.context_processor
def utility_processor():
    """Добавляем функции в контекст всех шаблонов"""
    def get_available_copies_count(book_id, library_id):
        """Получить количество доступных экземпляров книги в конкретной библиотеке"""
        book_library = BookLibrary.query.filter_by(
            book_id=book_id,
            library_id=library_id
        ).first()
        
        if not book_library:
            return 0
        
        # Считаем активные брони
        active_reservation_count = BookReservation.query.filter_by(
            book_id=book_id,
            library_id=library_id,
            is_active=True
        ).count()
        
        # Вычисляем доступное количество
        available = book_library.quantity - active_reservation_count
        
        return max(0, available)
    
    return dict(get_available_copies_count=get_available_copies_count)

# Добавим API endpoints для динамической загрузки библиотек
@app.route('/admin/api/libraries/without-book/<int:book_id>')
@login_required
def api_libraries_without_book(book_id):
    """API для получения библиотек, с которыми книга не связана"""
    libraries = get_libraries_without_book(book_id)
    libraries_data = [{'id': lib.id, 'name': lib.name, 'address': lib.address} for lib in libraries]
    return jsonify(libraries_data)

@app.route('/admin/api/libraries/with-book/<int:book_id>')
@login_required
def api_libraries_with_book(book_id):
    """API для получения библиотек, с которыми книга связана"""
    libraries = get_libraries_with_book(book_id)
    libraries_data = [{'id': lib.id, 'name': lib.name, 'address': lib.address} for lib in libraries]
    return jsonify(libraries_data)

# --- Новые API endpoints для управления количеством ---
@app.route('/admin/api/library/<int:library_id>/details')
@login_required
def get_library_details(library_id):
    """Получить детальную информацию о библиотеке (экземпляры книг)"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    try:
        # Сначала освобождаем просроченные брони
        update_expired_reservations()
        
        # Получаем все связи для библиотеки
        relations = BookLibrary.query.filter_by(library_id=library_id).all()
        
        books_data = []
        for rel in relations:
            book = Book.query.get(rel.book_id)
            
            if not book:
                continue
            
            active_reservations_count = BookReservation.query.filter_by(
                book_id=rel.book_id,
                library_id=library_id,
                is_active=True
            ).count()
            
            available_quantity = max(0, rel.quantity - active_reservations_count)
            
            books_data.append({
                'book_id': book.id,
                'title': book.title,
                'author': book.author,
                'total_quantity': rel.quantity,
                'available_quantity': available_quantity,
                'reserved_quantity': active_reservations_count,
                'active_reservations': active_reservations_count
            })
        
        # Получаем активные брони для отображения
        reservations = BookReservation.query.filter_by(
            library_id=library_id,
            is_active=True
        ).join(Book).join(User).all()
        
        reservations_data = []
        now = datetime.now(timezone.utc)  # ← ИЗМЕНЕНИЕ ЗДЕСЬ!
        
        for res in reservations:
            if not res.book or not res.user:
                continue
            
            if res.expiry_date is None:
                days_left = 0
                expiry_date_formatted = 'Не указано'
            else:
                # Делаем expiry_date aware (с часовым поясом) для сравнения
                if res.expiry_date.tzinfo is None:
                    # Если naive datetime (без часового пояса)
                    expiry_date_aware = res.expiry_date.replace(tzinfo=timezone.utc)
                else:
                    expiry_date_aware = res.expiry_date
                
                days_left = max(0, (expiry_date_aware - now).days)
                expiry_date_formatted = res.expiry_date.strftime('%d.%m.%Y %H:%M')
            
            reservations_data.append({
                'book_title': res.book.title,
                'user_name': res.user.username,
                'reservation_date': res.reservation_date.strftime('%d.%m.%Y %H:%M'),
                'expiry_date': expiry_date_formatted,
                'days_left': days_left
            })
        
        total_books = len(books_data)
        total_copies = sum(b['total_quantity'] for b in books_data) if books_data else 0
        total_available = sum(b['available_quantity'] for b in books_data) if books_data else 0
        total_reserved = total_copies - total_available
        
        return jsonify({
            'success': True,
            'data': {
                'books': books_data,
                'reservations': reservations_data,
                'stats': {
                    'total_books': total_books,
                    'total_copies': total_copies,
                    'available_copies': total_available,
                    'reserved_copies': total_reserved,
                    'active_reservations': len(reservations_data)
                }
            }
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Ошибка в get_library_details: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': f"Внутренняя ошибка сервера: {str(e)}"}), 500
    
@app.route('/admin/api/book_library/update_quantity', methods=['POST'])
@login_required
def update_book_library_quantity():
    """Обновить количество экземпляров книги в библиотеке"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    try:
        book_id = request.json.get('book_id')
        library_id = request.json.get('library_id')
        new_quantity = int(request.json.get('quantity'))
        
        if new_quantity < 0:
            return jsonify({'success': False, 'error': 'Количество не может быть отрицательным'}), 400
        
        # Находим связь
        book_library = BookLibrary.query.filter_by(
            book_id=book_id,
            library_id=library_id
        ).first()
        
        if not book_library:
            return jsonify({'success': False, 'error': 'Связь не найдена'}), 404
        
        # Проверяем, что новое количество не меньше активных броней
        active_reservations = BookReservation.query.filter_by(
            book_id=book_id,
            library_id=library_id,
            is_active=True
        ).count()
        
        if new_quantity < active_reservations:
            return jsonify({
                'success': False, 
                'error': f'Нельзя установить меньше {active_reservations} (есть активные брони)'
            }), 400
        
        # Обновляем только общее количество
        book_library.quantity = new_quantity
        db.session.commit()
        
        # ВЫЧИСЛЯЕМ доступное количество для ответа
        available_quantity = max(0, new_quantity - active_reservations)
        
        return jsonify({
            'success': True,
            'message': 'Количество обновлено',
            'data': {
                'total_quantity': new_quantity,
                'available_quantity': available_quantity,  # ← ВЫЧИСЛЕННОЕ!
                'reserved_quantity': active_reservations   # ← реальные активные брони
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/book_library/stats/<int:library_id>')
@login_required
def get_library_book_stats(library_id):
    """Получить статистику по книгам в библиотеке"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    
    try:
        # Получаем все связи для этой библиотеки
        relations = BookLibrary.query.filter_by(library_id=library_id).all()
        
        # Собираем статистику
        total_books = 0
        total_copies = 0
        available_copies = 0
        
        books_data = []
        for rel in relations:
            book = Book.query.get(rel.book_id)
            
            # Считаем активные брони
            active_reservations = BookReservation.query.filter_by(
                book_id=rel.book_id,
                library_id=library_id,
                is_active=True
            ).count()
            
            # ВЫЧИСЛЯЕМ доступное количество
            available_quantity = max(0, rel.quantity - active_reservations)
            
            total_books += 1
            total_copies += rel.quantity
            available_copies += available_quantity  # ← ВЫЧИСЛЕННОЕ!
            
            books_data.append({
                'book_id': book.id,
                'title': book.title,
                'author': book.author,
                'quantity': rel.quantity,
                'available_quantity': available_quantity,  # ← ВЫЧИСЛЕННОЕ!
                'reserved': active_reservations  # ← реальные активные брони
            })
        
        return jsonify({
            'success': True,
            'data': {
                'library_id': library_id,
                'stats': {
                    'total_books': total_books,
                    'total_copies': total_copies,
                    'available_copies': available_copies,  # ← ВЫЧИСЛЕННОЕ!
                    'reserved_copies': total_copies - available_copies
                },
                'books': books_data
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def index():
    title = request.args.get('title', '')
    author = request.args.get('author', '')
    genre = request.args.get('genre', '')
    
    query = Book.query
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    if genre:
        query = query.filter(Book.genre.ilike(f'%{genre}%'))
    
    books = query.all()
    
    # Для каждой книги определяем доступные библиотеки
    book_availability = {}
    for book in books:
        available_libraries = get_available_libraries_for_book(book.id)
        book_availability[book.id] = {
            'available_libraries': available_libraries,
            'is_available': len(available_libraries) > 0  # Просто проверяем, есть ли доступные библиотеки
        }
    
    return render_template('index.html', books=books, book_availability=book_availability)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Этот логин уже занят')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            
            # Для AJAX запросов возвращаем JSON ответ
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response_data = {'success': True}
                if user.is_admin():
                    response_data['redirect'] = url_for('admin_panel')
                else:
                    response_data['redirect'] = url_for('index')
                return jsonify(response_data)
            
            # Для обычных запросов - редирект
            if user.is_admin():
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('index'))
            
        # Обработка ошибок для AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Неверные данные для входа'})
        
        flash('Неверные данные для входа')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Маршруты администратора ---

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin():
        flash('Доступ запрещен. Требуются права администратора.')
        return redirect(url_for('index'))
    
    books = Book.query.all()
    libraries = Library.query.all()
    return render_template('admin_panel.html', books=books, libraries=libraries)

@app.route('/admin/book/add', methods=['POST'])
@login_required
def add_book():
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        book = Book(title=title, author=author, genre=genre)
        db.session.add(book)
        db.session.commit()
        
        # Для AJAX запросов возвращаем успешный ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Книга успешно добавлена'})
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Ошибка при добавлении книги: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin/book/delete/<int:book_id>')
@login_required
def delete_book(book_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        book = Book.query.get_or_404(book_id)
        db.session.delete(book)
        db.session.commit()
        
        # Для AJAX запросов возвращаем успешный ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Книга успешно удалена'})
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Ошибка при удалении книги: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin/book/edit/<int:book_id>', methods=['POST'])
@login_required
def edit_book(book_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        book = Book.query.get_or_404(book_id)
        book.title = request.form['title']
        book.author = request.form['author']
        book.genre = request.form['genre']
        db.session.commit()
        
        # Для AJAX запросов возвращаем JSON ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Книга успешно обновлена'})
        
        # Для обычных POST запросов (форм в таблицах) - редирект с flash сообщением
        flash('Книга успешно обновлена!', 'success')
        return redirect(url_for('admin_panel'))
        
    except Exception as e:
        db.session.rollback()
        # Для AJAX запросов
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        
        # Для обычных POST запросов
        flash(f'Ошибка при обновлении книги: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/library/add', methods=['POST'])
@login_required
def add_library():
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        name = request.form['name']
        address = request.form['address']
        library = Library(name=name, address=address)
        db.session.add(library)
        db.session.commit()
        
        # Для AJAX запросов возвращаем успешный ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Библиотека успешно добавлена'})
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Ошибка при добавлении библиотеки: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin/library/delete/<int:library_id>')
@login_required
def delete_library(library_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        library = Library.query.get_or_404(library_id)
        db.session.delete(library)
        db.session.commit()
        
        # Для AJAX запросов возвращаем успешный ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Библиотека успешно удалена'})
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Ошибка при удалении библиотеки: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin/library/edit/<int:library_id>', methods=['POST'])
@login_required
def edit_library(library_id):
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        library = Library.query.get_or_404(library_id)
        library.name = request.form['name']
        library.address = request.form['address']
        db.session.commit()
        
        # Для AJAX запросов возвращаем JSON ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Библиотека успешно обновлена'})
        
        # Для обычных POST запросов (форм в таблицах) - редирект с flash сообщением
        flash('Библиотека успешно обновлена!', 'success')
        return redirect(url_for('admin_panel'))
        
    except Exception as e:
        db.session.rollback()
        # Для AJAX запросов
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        
        # Для обычных POST запросов
        flash(f'Ошибка при обновлении библиотеки: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/book_library/add', methods=['POST'])
@login_required
def add_book_library():
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        book_id = request.form['book_id']
        library_id = request.form['library_id']
        
        # Проверяем, не существует ли уже такая связь
        existing = BookLibrary.query.filter_by(book_id=book_id, library_id=library_id).first()
        if existing:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Связь уже существует'})
            flash('Связь уже существует')
            return redirect(url_for('admin_panel'))
            
        bl = BookLibrary(book_id=book_id, library_id=library_id)
        db.session.add(bl)
        db.session.commit()
        
        # Для AJAX запросов возвращаем успешный ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Связь успешно добавлена'})
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Ошибка при добавлении связи: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin/book_library/delete', methods=['POST'])
@login_required
def delete_book_library():
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
    try:
        book_id = request.form['book_id']
        library_id = request.form['library_id']
        bl = BookLibrary.query.filter_by(book_id=book_id, library_id=library_id).first()
        if bl:
            db.session.delete(bl)
            db.session.commit()
            message = 'Связь успешно удалена'
        else:
            message = 'Связь не найдена'
        
        # Для AJAX запросов возвращаем успешный ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': message})
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Ошибка при удалении связи: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/reserve/<int:book_id>', methods=['POST'])
@login_required
def reserve_book(book_id):
    library_id = request.form.get('library_id')
    
    if not library_id:
        flash('Пожалуйста, выберите библиотеку', 'error')
        return redirect(url_for('index'))
    
    try:
        # Сначала освобождаем просроченные брони
        update_expired_reservations()
        
        # Находим связь книга-библиотека
        book_library = BookLibrary.query.filter_by(
            book_id=book_id,
            library_id=library_id
        ).first()
        
        if not book_library:
            flash('Книга не найдена в этой библиотеке', 'error')
            return redirect(url_for('index'))
        
        # Считаем активные брони для проверки доступности
        active_reservation_count = BookReservation.query.filter_by(
            book_id=book_id,
            library_id=library_id,
            is_active=True
        ).count()
        
        # Проверяем, есть ли доступные экземпляры
        if active_reservation_count >= book_library.quantity:
            flash('Нет доступных экземпляров в выбранной библиотеке', 'error')
            return redirect(url_for('index'))
        
        # Создаем бронирование
        now = datetime.now(timezone.utc)
        reservation = BookReservation(
            book_id=book_id,
            library_id=int(library_id),
            user_id=current_user.id,
            reservation_date=now,
            expiry_date=now + timedelta(days=7)
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        flash('Книга успешно забронирована на 7 дней!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при бронировании: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
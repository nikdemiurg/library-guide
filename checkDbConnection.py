from app import app, db, Book, Library, User, Admin, BookLibrary

with app.app_context():
    try:
        # Проверяем подключение и получаем ВСЕ книги
        books = Book.query.all()
        libraries = Library.query.all()
        users = User.query.all()
        admins = Admin.query.all()
        book_libraries = BookLibrary.query.all()
        
        print("✅ Подключение к PostgreSQL успешно!")
        print(f"✅ Найдено книг: {len(books)}")
        print(f"✅ Найдено библиотек: {len(libraries)}")
        print(f"✅ Найдено пользователей: {len(users)}")
        print(f"✅ Найдено администраторов: {len(admins)}")
        print(f"✅ Найдено связей книг-библиотек: {len(book_libraries)}")
        
        # Выводим подробную информацию о книгах
        if books:
            print("\n📚 Список книг в базе:")
            for book in books:
                print(f"   - {book.title} (ID: {book.id})")
        
        if libraries:
            print("\n🏛️ Список библиотек в базе:")
            for library in libraries:
                print(f"   - {library.name} (ID: {library.id})")
        
        if book_libraries:
            print("\n🔗 Связи книг с библиотеками:")
            for bl in book_libraries:
                print(f"   - Книга ID:{bl.book_id} -> Библиотека ID:{bl.library_id}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
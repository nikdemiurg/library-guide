# check_final.py
from app import app, db
from sqlalchemy import text

print("🎯 ФИНАЛЬНАЯ ПРОВЕРКА ОБНОВЛЕНИЯ")
print("=" * 50)

with app.app_context():
    try:
        # 1. Проверяем модель
        print("1. Проверка модели BookLibrary...")
        from app import BookLibrary
        
        # Проверяем атрибуты
        attrs = [attr for attr in dir(BookLibrary) if not attr.startswith('_')]
        print(f"   Атрибуты модели: {attrs}")
        
        if hasattr(BookLibrary, 'quantity') and hasattr(BookLibrary, 'available_quantity'):
            print("   ✅ Поля quantity и available_quantity есть в модели")
        else:
            print("   ❌ Поля отсутствуют в модели!")
            print("   Обновите класс BookLibrary в app.py")
        
        # 2. Проверяем данные в БД
        print("\n2. Проверка данных в таблице...")
        query = text("""
            SELECT 
                COUNT(*) as total,
                SUM(quantity) as total_qty,
                SUM(available_quantity) as avail_qty,
                COUNT(CASE WHEN quantity IS NULL THEN 1 END) as null_qty,
                COUNT(CASE WHEN available_quantity IS NULL THEN 1 END) as null_avail
            FROM book_library
        """)
        result = db.session.execute(query).fetchone()
        
        print(f"   Всего записей: {result[0]}")
        print(f"   Всего экземпляров: {result[1] or 0}")
        print(f"   Доступно экземпляров: {result[2] or 0}")
        print(f"   Записей с NULL в quantity: {result[3]}")
        print(f"   Записей с NULL в available_quantity: {result[4]}")
        
        if result[3] > 0 or result[4] > 0:
            print("   ⚠️ Есть NULL значения - нужно обновить!")
        
        # 3. Тестовый запрос через модель
        print("\n3. Тест через SQLAlchemy модель...")
        try:
            sample = BookLibrary.query.first()
            if sample:
                print(f"   Пример записи:")
                print(f"     book_id: {sample.book_id}")
                print(f"     library_id: {sample.library_id}")
                print(f"     quantity: {sample.quantity}")
                print(f"     available_quantity: {sample.available_quantity}")
            else:
                print("   ⚠️ Нет данных в таблице")
        except Exception as e:
            print(f"   ❌ Ошибка при запросе: {e}")
        
        # 4. Проверяем, обновлены ли все записи
        print("\n4. Проверка обновления записей...")
        null_check_query = text("""
            SELECT EXISTS(
                SELECT 1 FROM book_library 
                WHERE quantity IS NULL OR available_quantity IS NULL
            ) as has_nulls
        """)
        null_check = db.session.execute(null_check_query).fetchone()
        
        if null_check and null_check[0]:
            print("   ⚠️ Есть записи с NULL значениями")
            print("   Выполните в pgAdmin:")
            print("   UPDATE book_library SET quantity = 1 WHERE quantity IS NULL;")
            print("   UPDATE book_library SET available_quantity = 1 WHERE available_quantity IS NULL;")
        else:
            print("   ✅ Все записи обновлены (нет NULL)")
        
        # 5. Проверяем несколько записей
        print("\n5. Примеры записей:")
        sample_query = text("""
            SELECT book_id, library_id, quantity, available_quantity 
            FROM book_library 
            LIMIT 3
        """)
        samples = db.session.execute(sample_query).fetchall()
        
        for i, sample in enumerate(samples):
            print(f"   Запись {i+1}: book_id={sample[0]}, library_id={sample[1]}, qty={sample[2]}, avail={sample[3]}")
        
        print("\n" + "=" * 50)
        print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
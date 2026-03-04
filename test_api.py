# test_api.py
from app import app
import json

with app.test_client() as client:
    # Тестируем endpoint статистики
    print("🔍 Тестируем API...")
    
    # 1. Проверяем endpoint статистики
    print("\n1. Тест /admin/api/book_library/stats/1")
    response = client.get('/admin/api/book_library/stats/1')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = json.loads(response.data)
        print(f"   Success: {data.get('success')}")
        print(f"   Данные: {data.get('data', {}).get('stats', {})}")
    else:
        print(f"   Ошибка: {response.data}")
    
    # 2. Проверяем endpoint обновления количества
    print("\n2. Тест /admin/api/book_library/quantity")
    
    # Сначала нужно залогиниться как админ
    # Для теста создайте временного пользователя
    print("   ⚠️ Требуется авторизация администратора")
from werkzeug.security import generate_password_hash

# Генерируем хэш для пароля 'admin123'
password_hash = generate_password_hash('admin123')
print(f"Хэш для 'admin123': {password_hash}")

# Копируй этот хэш и используй в SQL запросе
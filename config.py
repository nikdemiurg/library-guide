import os

class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Подключение к PostgreSQL - убедитесь что БД уже создана
    SQLALCHEMY_DATABASE_URI = "postgresql://library_user:library_pass@localhost:5432/library_db"
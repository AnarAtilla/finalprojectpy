import mysql.connector

# Подключение к серверу MySQL без указания базы данных
db = mysql.connector.connect(
    host="your_host",
    user="yor_id",
    password="your_password"
)

# Создание курсора
cursor = db.cursor()

# SQL-код для создания новой базы данных и таблиц
sql_create_database = """
CREATE DATABASE IF NOT EXISTS project_student;
USE project_student;

CREATE TABLE search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    search_text TEXT,
    req_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    SQL_req TEXT
);

CREATE TABLE bot_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    search_text TEXT,
    req_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    SQL_req TEXT
);
"""

# Выполнение SQL-кода
cursor.execute(sql_create_database)

# Закрытие курсора и соединения
cursor.close()
db.close()
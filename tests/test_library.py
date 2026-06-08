import os
import pytest

import library

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import inspect

# =========================================================
# ТЕСТОВАЯ БД
# =========================================================

TEST_DB = "sqlite:///test.db"

engine = create_engine(TEST_DB, echo=False)
Session = sessionmaker(bind=engine)

# =========================================================
# 0. Настройка тестовой базы
# =========================================================

@pytest.fixture(autouse=True)
def setup_db():

    # подменяем БД
    library.engine = engine
    library.Session = Session

    # пересоздаём таблицы
    library.Base.metadata.drop_all(engine)
    library.create_tables()
    library.seed_data()

    yield

    library.Base.metadata.drop_all(engine)

# =========================================================
# 1. Проверка таблиц
# =========================================================

def test_tables_exist():
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    assert "books" in tables
    assert "users" in tables
    assert "borrowings" in tables

# =========================================================
# 2. Проверка seed данных
# =========================================================

def test_seed_data():

    session = Session()

    books_count = session.query(library.Book).count()
    users_count = session.query(library.User).count()

    assert books_count >= 3
    assert users_count >= 2

    session.close()

# =========================================================
# 3. Выдача книги
# =========================================================

def test_borrow_book():

    library.borrow_book(1, 1)

    session = Session()

    book = session.query(library.Book).filter_by(id=1).first()

    assert book.available is False

    session.close()

# =========================================================
# 4. Повторная выдача запрещена
# =========================================================

def test_borrow_book_twice(capfd):

    library.borrow_book(1, 2)
    library.borrow_book(1, 2)

    out = capfd.readouterr().out

    assert "уже выдана" in out

# =========================================================
# 5. Возврат книги
# =========================================================

def test_return_book():

    library.borrow_book(1, 3)
    library.return_book(3)

    session = Session()

    book = session.query(library.Book).filter_by(id=3).first()

    assert book.available is True

    session.close()

# =========================================================
# 6. Добавление пользователя
# =========================================================

def test_add_user():

    library.add_user("Test User", "test@example.com")

    session = Session()

    user = session.query(library.User).filter_by(
        email="test@example.com"
    ).first()

    assert user is not None

    session.close()

# =========================================================
# 7. Проверка UNIQUE email
# =========================================================

def test_duplicate_user(capfd):

    library.add_user("A", "dup@mail.com")
    library.add_user("B", "dup@mail.com")

    out = capfd.readouterr().out

    assert "уже существует" in out

# =========================================================
# 8. Поиск книг
# =========================================================

def test_search_books(capfd):

    library.search_books("1984")

    out = capfd.readouterr().out

    assert "1984" in out or "Orwell" in out

# Запуск тестов: pytest tests/test_library.py из корневой папки проекта.
from datetime import date

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Date
)

from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker
)

from sqlalchemy.exc import IntegrityError

# =========================================================
# Настройка базы данных
# =========================================================

DATABASE_URL = "sqlite:///library.db"

# Создание движка для работы с базой данных
engine = create_engine(
    DATABASE_URL,
    echo=False
)

# Создание сессии для взаимодействия с базой данных
Session = sessionmaker(bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# =========================================================
# ORM-МОДЕЛИ
# =========================================================

# Модель книги
class Book(Base):

    # Имя таблицы в базе данных
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)

    title = Column(String, nullable=False)

    author = Column(String, nullable=False)

    year = Column(Integer)

    available = Column(Boolean, default=True)

    # Связь с таблицей Borrowing
    borrowings = relationship(
        "Borrowing",
        back_populates="book"
    )

    # -----------------------------------------------------
    # Методы модели
    # -----------------------------------------------------

    # Методы для изменения статуса книги
    def mark_as_borrowed(self):
        self.available = False

    # Метод для возврата книги
    def mark_as_returned(self):
        self.available = True

    # Метод для отображения статуса книги
    def status(self):
        return "Доступна" if self.available else "Выдана"

    # Магический метод для строкового представления книги
    def __str__(self):
        return (
            f"{self.id}: "
            f"{self.title} "
            f"({self.author}, {self.year}) — "
            f"{self.status()}"
        )

# Модель пользователя
class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    email = Column(
        String,
        nullable=False,
        unique=True
    )

    # Связь с Borrowing
    borrowings = relationship(
        "Borrowing",
        back_populates="user"
    )

    # -----------------------------------------------------
    # Методы модели
    # -----------------------------------------------------

    # Метод для получения списка активных (не возвращенных) книг пользователя
    def get_active_books(self):

        return [
            borrowing.book
            for borrowing in self.borrowings
            if not borrowing.book.available
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"


# Модель выдачи книги
class Borrowing(Base):

    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    book_id = Column(
        Integer,
        ForeignKey("books.id")
    )

    borrow_date = Column(Date)

    # Связи
    user = relationship(
        "User",
        back_populates="borrowings"
    )

    book = relationship(
        "Book",
        back_populates="borrowings"
    )

    # -----------------------------------------------------
    # Статический метод
    # -----------------------------------------------------
    
    # Статический метод для создания новой выдачи книги
    # Используется вместо конструктора, так как при выдаче нужно сразу менять статус книги
    @staticmethod
    def create(session, user, book):

        borrowing = Borrowing(
            user=user,
            book=book,
            borrow_date=date.today()
        )

        book.mark_as_borrowed()

        session.add(borrowing)

        return borrowing

# =========================================================
# СОЗДАНИЕ ТАБЛИЦ
# =========================================================

def create_tables():

    Base.metadata.create_all(engine)

# =========================================================
# ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ
# =========================================================

def seed_data():

    session = Session()

    try:

        # Проверка:
        # если данные уже есть — не добавлять повторно

        if session.query(Book).first():
            print("⚠️ Начальные данные уже существуют.")
            return

        books = [

            Book(
                title="1984",
                author="George Orwell",
                year=1949
            ),

            Book(
                title="Brave New World",
                author="Aldous Huxley",
                year=1932
            ),

            Book(
                title="Fahrenheit 451",
                author="Ray Bradbury",
                year=1953
            ),

            Book(
                title="To Kill a Mockingbird",
                author="Harper Lee",
                year=1960
            ),

            Book(
                title="The Great Gatsby",
                author="F. Scott Fitzgerald",
                year=1925
            )
        ]

        users = [

            User(
                name="Alice",
                email="alice@example.com"
            ),

            User(
                name="Bob",
                email="bob@example.com"
            ),

            User(
                name="Charlie",
                email="charlie@example.com"
            )
        ]

        session.add_all(books)

        session.add_all(users)

        session.commit()

        print("✅ Начальные данные добавлены.")

    except Exception as e:

        session.rollback()

        print("❌ Ошибка:", e)

    finally:

        session.close()


# =========================================================
# Функции для работы с библиотекой
# =========================================================

def show_books():
    session = Session()

    books = session.query(Book).all()

    for b in books:
        status = "Доступна" if b.available else "Выдана"
        print(f"{b.id}: {b.title} — {b.author} ({status})")

    session.close()


def borrow_book(user_id, book_id):
    session = Session()

    try:
        book = session.query(Book).filter_by(id=book_id).first()

        if not book:
            print("❌ Книга не найдена")
            return

        if not book.available:
            print("❌ Книга уже выдана")
            return

        borrowing = Borrowing(
            user_id=user_id,
            book_id=book_id,
            borrow_date=date.today()
        )

        book.available = False

        session.add(borrowing)
        session.commit()

        print("📚 Книга выдана")

    except Exception as e:
        session.rollback()
        print("❌ Ошибка:", e)

    finally:
        session.close()


def return_book(book_id):
    session = Session()

    try:
        book = session.query(Book).filter_by(id=book_id).first()

        if not book:
            print("❌ Книга не найдена")
            return

        if book.available:
            print("ℹ️ Книга уже доступна")
            return

        book.available = True
        session.commit()

        print("📦 Книга возвращена")

    except Exception as e:
        session.rollback()
        print("❌ Ошибка:", e)

    finally:
        session.close()


def show_user_books(user_id):
    session = Session()

    borrowings = (
        session.query(Borrowing)
        .join(Book)
        .filter(Borrowing.user_id == user_id)
        .all()
    )

    if not borrowings:
        print("Нет выданных книг")
    else:
        for b in borrowings:
            print(f"{b.book.title} — {b.borrow_date}")

    session.close()


def search_books(keyword):
    session = Session()

    books = (
        session.query(Book)
        .filter(
            (Book.title.ilike(f"%{keyword}%")) |
            (Book.author.ilike(f"%{keyword}%"))
        )
        .all()
    )

    for b in books:
        print(f"{b.title} — {b.author}")

    session.close()


def add_user(name, email):
    session = Session()

    try:
        session.add(User(name=name, email=email))
        session.commit()
        print("✅ Пользователь добавлен")

    except IntegrityError:
        session.rollback()
        print("❌ Ошибка: пользователь с таким email уже существует")

    finally:
        session.close()

# =========================================================
# МЕНЮ
# =========================================================

def main_menu():
    while True:

        print("\n📚 Меню")
        print("1 - Показать книги")
        print("2 - Выдать книгу")
        print("3 - Вернуть книгу")
        print("4 - Книги пользователя")
        print("5 - Поиск")
        print("6 - Добавить пользователя")
        print("7 - Выход")

        choice = input(">>> ")

        if choice == "1":
            show_books()

        elif choice == "2":
            borrow_book(
                int(input("user_id: ")),
                int(input("book_id: "))
            )

        elif choice == "3":
            return_book(int(input("book_id: ")))

        elif choice == "4":
            show_user_books(int(input("user_id: ")))

        elif choice == "5":
            search_books(input("keyword: "))

        elif choice == "6":
            add_user(
                input("name: "),
                input("email: ")
            )

        elif choice == "7":
            break

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    create_tables()
    seed_data()
    main_menu()
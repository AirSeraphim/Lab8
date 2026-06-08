import pytest
import sys
import io
from sqlalchemy import create_engine, inspect
from datetime import date
import service

@pytest.fixture(scope="function")
def setup_db():
    service.engine = create_engine('sqlite:///:memory:')
    service.create_tables()
    yield
    service.Base.metadata.drop_all(service.engine)

def test_create_tables(setup_db):
    inspector = inspect(service.engine)
    assert inspector.has_table('Clients')
    assert inspector.has_table('Requests')

def test_add_client(setup_db, capsys):
    client_id = service.add_client("Иван Иванов", "1234567890")
    assert client_id is not None
    
    client_id_2 = service.add_client("Петр Петров", "1234567890")
    assert client_id_2 is None
    
    captured = capsys.readouterr()
    assert "❌ Клиент с таким телефоном уже существует" in captured.out

def test_create_request(setup_db, capsys):
    client_id = service.add_client("Сидор Сидоров", "0987654321")
    req_id = service.create_request(client_id, "Ноутбук", "Не включается")
    assert req_id is not None
    
    reqs = service.get_client_requests(client_id)
    assert len(reqs) == 1
    assert reqs[0].device == "Ноутбук"
    assert reqs[0].status == "new"
    assert reqs[0].created_at == date.today()

def test_update_status(setup_db, capsys):
    client_id = service.add_client("Тест Тестов", "111222333")
    req_id = service.create_request(client_id, "ПК", "Тормозит")
    
    service.update_status(req_id, "in_progress")
    reqs = service.get_client_requests(client_id)
    assert reqs[0].status == "in_progress"
    
    with pytest.raises(ValueError, match="Некорректный статус"):
        service.update_status(req_id, "invalid_status")

def test_search_requests(setup_db, capsys):
    client_id = service.add_client("Поиск Поисков", "444555666")
    service.create_request(client_id, "MacBook", "Экран разбит")
    service.create_request(client_id, "iPhone", "Не работает экран")
    
    # Поиск по устройству
    results = service.search_requests("MacBook")
    assert len(results) == 1
    
    # Поиск по проблеме (частичное совпадение, регистронезависимо)
    results = service.search_requests("экран")
    assert len(results) == 2

def test_search_requests_case_insensitive(setup_db):
    client_id = service.add_client("Тест", "999888777")
    service.create_request(client_id, "Ноутбук", "Разбит экран")
    
    # Поиск в разных регистрах
    assert len(service.search_requests("ЭКРАН")) == 1
    assert len(service.search_requests("экран")) == 1
    assert len(service.search_requests("Экран")) == 1

def test_search_no_results(setup_db):
    results = service.search_requests("НесуществующееУстройство")
    assert len(results) == 0

def test_get_requests_nonexistent_client(setup_db):
    reqs = service.get_client_requests(99999)
    assert len(reqs) == 0

def test_update_status_nonexistent_request(setup_db):
    # Попытка обновить несуществующую заявку
    service.update_status(99999, "in_progress")
    # Должно либо вернуть False/None, либо вывести ошибку

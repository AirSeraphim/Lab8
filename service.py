from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, or_, func
from sqlalchemy.exc import IntegrityError
from datetime import date

try:
    from sqlalchemy.orm import declarative_base, relationship, sessionmaker
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Client(Base):
    __tablename__ = 'Clients'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    requests = relationship("Request", back_populates="client")

class Request(Base):
    __tablename__ = 'Requests'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('Clients.id'))
    device = Column(String, nullable=False)
    problem = Column(String, nullable=False)
    status = Column(String, nullable=False, default='new')
    created_at = Column(Date, nullable=False, default=date.today)
    client = relationship("Client", back_populates="requests")

engine = create_engine('sqlite:///service.db', echo=False)

def get_session():
    Session = sessionmaker(bind=engine)
    return Session()

def create_tables():
    Base.metadata.create_all(engine)

def add_client(name, phone):
    session = get_session()
    try:
        new_client = Client(name=name, phone=phone)
        session.add(new_client)
        session.commit()
        return new_client.id
    except IntegrityError:
        session.rollback()
        print("❌ Клиент с таким телефоном уже существует", flush=True)
        return None
    finally:
        session.close()

def create_request(client_id, device, problem):
    session = get_session()
    try:
        new_request = Request(
            client_id=client_id, 
            device=device, 
            problem=problem, 
            status='new', 
            created_at=date.today()
        )
        session.add(new_request)
        session.commit()
        return new_request.id
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при создании заявки: {e}", flush=True)
        return None
    finally:
        session.close()

def update_status(request_id, status):
    valid_statuses = ['new', 'in_progress', 'done']
    if status not in valid_statuses:
        raise ValueError("Некорректный статус")
    
    session = get_session()
    try:
        req = session.query(Request).filter(Request.id == request_id).first()
        if req:
            req.status = status
            session.commit()
        else:
            print("❌ Заявка не найдена.", flush=True)
    finally:
        session.close()

def get_client_requests(client_id):
    session = get_session()
    try:
        client = session.query(Client).filter(Client.id == client_id).first()
        if client:
            results = []
            for req in client.requests:
                print(f"Устройство: {req.device}, Проблема: {req.problem}, Статус: {req.status}, Дата: {req.created_at}", flush=True)
                results.append(req)
            return results
        else:
            print("❌ Клиент не найден.", flush=True)
            return []
    finally:
        session.close()

def search_requests(keyword):
    session = get_session()
    try:
        # Пробуем несколько подходов для регистронезависимого поиска
        keyword_lower = keyword.lower()
        keyword_upper = keyword.upper()
        keyword_title = keyword.capitalize()
        
        # Ищем с учетом всех вариантов регистра
        results = session.query(Request).filter(
            or_(
                Request.device.like(f"%{keyword}%"),
                Request.device.like(f"%{keyword_lower}%"),
                Request.device.like(f"%{keyword_upper}%"),
                Request.device.like(f"%{keyword_title}%"),
                Request.problem.like(f"%{keyword}%"),
                Request.problem.like(f"%{keyword_lower}%"),
                Request.problem.like(f"%{keyword_upper}%"),
                Request.problem.like(f"%{keyword_title}%")
            )
        ).all()
        
        # Убираем дубликаты
        unique_results = []
        seen_ids = set()
        for req in results:
            if req.id not in seen_ids:
                seen_ids.add(req.id)
                unique_results.append(req)
        
        output = []
        for req in unique_results:
            print(f"Устройство: {req.device}, Проблема: {req.problem}, Статус: {req.status}, Дата: {req.created_at}", flush=True)
            output.append(req)
        return output
    finally:
        session.close()
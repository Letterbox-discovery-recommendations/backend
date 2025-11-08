import os

from dotenv import load_dotenv
from sqlmodel import create_engine, Session, select


load_dotenv()
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def get_engine():
    return engine


def get_session():
    with Session(engine) as session:
        yield session


def get_or_create(session: Session, model, **kwargs):
    """
    Busca una instancia. Si no existe, la crea y la AÑADE a la sesión actual,
    pero NO hace commit. El commit se hará fuera de esta función.
    """
    defaults = kwargs.pop("defaults", {})
    instance = session.exec(select(model).filter_by(**kwargs)).first()

    if instance:
        return instance
    else:
        instance_data = {**kwargs, **defaults}
        instance = model(**instance_data)
        session.add(instance)
        return instance
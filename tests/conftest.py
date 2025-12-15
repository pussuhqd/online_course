import os
import importlib
from datetime import datetime
import pytest


def _type_default_value(col):
    # максимально “универсальные” значения для обязательных полей
    try:
        pytype = col.type.python_type
    except Exception:
        pytype = str

    if pytype is int:
        return 1
    if pytype is float:
        return 1.0
    if pytype is bool:
        return False
    if pytype is datetime:
        return datetime.utcnow()
    return "test"


def make_instance(model, **overrides):
    """
    Создаёт инстанс модели и заполняет обязательные (nullable=False) поля,
    если у них нет default/server_default и это не PK/FK.
    """
    obj = model()
    table = getattr(model, "__table__", None)
    if table is None:
        for k, v in overrides.items():
            setattr(obj, k, v)
        return obj

    for col in table.columns:
        if col.primary_key:
            continue
        if col.name in overrides:
            continue
        if getattr(col, "nullable", True):
            continue
        if col.default is not None or col.server_default is not None:
            continue
        if getattr(col, "foreign_keys", None):
            if len(col.foreign_keys) > 0:
                continue
        setattr(obj, col.name, _type_default_value(col))

    for k, v in overrides.items():
        setattr(obj, k, v)
    return obj


@pytest.fixture(scope="session")
def app_module():
    # импортируем app.py как модуль
    import app as app_mod
    return app_mod


@pytest.fixture()
def flask_app(app_module, tmp_path, monkeypatch):
    """
    Поднимает приложение и БД для каждого теста.
    Важно: chdir в tmp_path, чтобы отчёты писались в временную папку.
    """
    monkeypatch.chdir(tmp_path)

    app = app_module.app
    db = app_module.db

    app.config.update(
        TESTING=True,
        # если в твоём app.py это поле уже используется — отлично;
        # если нет, тесты всё равно отработают, но будут писать в текущую БД.
        SQLALCHEMY_DATABASE_URI=os.environ.get("TEST_DATABASE_URI", "sqlite:///:memory:"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    with app.app_context():
        # на всякий случай — чистим
        try:
            db.session.remove()
            db.drop_all()
        except Exception:
            pass
        db.create_all()

        yield app

        db.session.remove()
        try:
            db.drop_all()
        except Exception:
            pass


@pytest.fixture()
def db(app_module):
    return app_module.db


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture()
def models(app_module):
    return app_module.Employee, app_module.Course, app_module.Registration


@pytest.fixture()
def sample_data(flask_app, db, models):
    Employee, Course, Registration = models

    with flask_app.app_context():
        # employee
        e = make_instance(Employee)
        # часто есть full_name/first_name/last_name — заполним если есть
        if hasattr(e, "full_name"):
            e.full_name = "Test Employee"
        if hasattr(e, "first_name"):
            e.first_name = "Test"
        if hasattr(e, "last_name"):
            e.last_name = "Employee"

        # course
        c = make_instance(Course)
        if hasattr(c, "title"):
            c.title = "Test Course"
        if hasattr(c, "name"):
            c.name = "Test Course"
        if hasattr(c, "duration_hours"):
            c.duration_hours = 10

        db.session.add_all([e, c])
        db.session.commit()

        # registrations
        r1 = make_instance(
            Registration,
            employee_id=e.id,
            course_id=c.id,
            status=Registration.STATUS_ENROLLED,
            progress_percent=0,
        )
        r2 = make_instance(
            Registration,
            employee_id=e.id,
            course_id=c.id,
            status=Registration.STATUS_COMPLETED,
            progress_percent=100,
            is_deleted=True,  # удалённая запись не должна учитываться
        )

        db.session.add_all([r1, r2])
        db.session.commit()

        return {"employee": e, "course": c, "registrations": [r1, r2]}

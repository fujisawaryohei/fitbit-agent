import pytest
from backend.containers import Container


@pytest.fixture(scope="session", autouse=True)
def container():
    c = Container()
    c.wire(modules=["backend.controllers.auth", "backend.controllers.chat"])
    yield c
    c.unwire()

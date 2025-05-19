from run import app 
import pytest

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_home_redirect(client):
    response = client.get('/')
    assert response.status_code == 302
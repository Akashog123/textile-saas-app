import json
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from routes.stores_routes import stores_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(stores_bp)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def client(app):
    return app.test_client()

@patch('routes.stores_routes.StoreRegion')
def test_get_stores_returns_list(mock_store_region, client):
    fake_row_1 = MagicMock(RegionID=1, StoreName='Store A',
                           Latitude=12.34, Longitude=56.78,
                           RegionName='Region 1', ImagePath='path/to/image_a.jpg')
    fake_row_2 = MagicMock(RegionID=2, StoreName='Store B',
                           Latitude=23.45, Longitude=67.89,
                           RegionName='Region 2', ImagePath='path/to/image_b.jpg')

    mock_store_region.query.order_by.return_value.all.return_value = [fake_row_1, fake_row_2]

    resp = client.get('/stores/')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['id'] == 1
    assert data[1]['name'] == 'Store B'

@patch('routes.stores_routes.StoreRegion')
def test_get_stores_empty(mock_store_region, client):
    mock_store_region.query.order_by.return_value.all.return_value = []
    resp = client.get('/stores/')
    assert resp.status_code == 200
    assert json.loads(resp.data) == []
    
def test_content_type_and_get_json(client, patch='routes.stores_routes.StoreRegion'):
    # reuse the existing patch style in your file — shown here as an example
    from unittest.mock import MagicMock, patch as _patch
    with _patch('routes.stores_routes.StoreRegion') as mock_store_region:
        fake = MagicMock(RegionID=1, StoreName='Store A',
                         Latitude=12.34, Longitude=56.78,
                         RegionName='Region 1', ImagePath='img.jpg')
        mock_store_region.query.order_by.return_value.all.return_value = [fake]

        resp = client.get('/stores/')
        assert resp.status_code == 200
        # content type
        assert resp.content_type.startswith('application/json')
        # use Flask helper
        data = resp.get_json()
        assert isinstance(data, list)
        assert data[0]['name'] == 'Store A'

def test_unicode_store_name(client):
    from unittest.mock import MagicMock, patch as _patch
    with _patch('routes.stores_routes.StoreRegion') as mock_store_region:
        fake = MagicMock(RegionID=1, StoreName='店铺_日本',  # unicode characters
                         Latitude=12.34, Longitude=56.78,
                         RegionName='区域', ImagePath='img.jpg')
        mock_store_region.query.order_by.return_value.all.return_value = [fake]

        resp = client.get('/stores/')
        assert resp.status_code == 200
        data = resp.get_json()
        # ensure the unicode name survives serialization
        assert data[0]['name'] == '店铺_日本'

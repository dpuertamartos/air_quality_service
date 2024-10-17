import pytest
from app.routes import init_routes
import xarray as xr
import numpy as np
from threading import Lock
from flask import Flask

@pytest.fixture
def mock_dataset(monkeypatch):
    lat = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    lon = np.array([-80.0, -90.0, -100.0, -110.0, -120.0])
    pm25_data = np.array([
        [12.5, 13.0, 14.0, np.nan, 16.5],
        [11.5, 12.0, np.nan, 15.0, 16.0],
        [10.5, 11.0, 12.0, 13.0, 14.0],
        [9.5, np.nan, 11.0, 12.0, 13.0],
        [8.5, 9.0, 10.0, 11.0, 12.0],
    ])

    mock_ds = xr.Dataset(
        {
            'GWRPM25': (['lat', 'lon'], pm25_data)
        },
        coords={
            'lat': lat,
            'lon': lon
        }
    )

    return mock_ds

@pytest.fixture
def client(mock_dataset):
     # Create a new Flask app instance for each test and Lock for thread safety
    app = Flask(__name__) 
    data_lock = Lock()  # 

    # Initialize the routes with the mock dataset
    init_routes(app, mock_dataset, data_lock)
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test GET /data/<id>
def test_get_data_by_id(client, mock_dataset):
    response = client.get('/data/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == 1
    assert data['lat'] == 10.0
    assert data['lon'] == -90.0
    assert data['pm25'] == 13.0

# Test GET /data/<id> with boundary conditions (last entry)
def test_get_data_by_id_boundary(client, mock_dataset):
    total_points = len(mock_dataset['lat']) * len(mock_dataset['lon'])
    response = client.get(f'/data/{total_points - 1}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == total_points - 1
    assert data['lat'] == 50.0
    assert data['lon'] == -120.0
    assert data['pm25'] == 12.0

# Test GET /data (with pagination)
def test_get_all_data(client, mock_dataset):
    response = client.get('/data?page=1&per_page=5')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 5

    # Check the first entry in the response (lat = 10.0, lon = -80.0)
    assert data[0]['lat'] == 10.0
    assert data[0]['lon'] == -80.0

    # Check the last entry in the first page (5th entry, lat=10.0, lon=-120.0)
    assert data[-1]['lat'] == 10.0
    assert data[-1]['lon'] == -120.0
    assert data[-1]['pm25'] == 16.5

# Test GET /data/filter with valid values
def test_filter_data(client, mock_dataset):
    response = client.get('/data/filter?lat=30.0&long=-100.0')
    assert response.status_code == 200
    data = response.get_json()
    assert data['lat'] == 30.0
    assert data['lon'] == -100.0
    assert data['pm25'] == 12.0

# Test GET /data/filter with non-existent coordinates (nearest match)
def test_filter_data_nearest(client, mock_dataset):
    response = client.get('/data/filter?lat=35.0&long=-105.0')  # Nearest will be 30.0, -100.0
    assert response.status_code == 200
    data = response.get_json()
    assert data['lat'] == 30.0
    assert data['lon'] == -100.0
    assert data['pm25'] == 12.0

# Test GET /data/stats
def test_get_stats(client, mock_dataset):
    response = client.get('/data/stats')
    assert response.status_code == 200
    stats = response.get_json()
    assert stats['count'] == 22  # Non-NaN values
    assert stats['mean_pm25'] == pytest.approx(12.23, 0.01)
    assert stats['min_pm25'] == 8.5
    assert stats['max_pm25'] == 16.5

# Test PUT /data/<id> (update existing data)
def test_update_data(client, mock_dataset):
    updated_data = {
        'pm25': 18.0
    }
    response = client.put('/data/1', json=updated_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['pm25'] == 18.0

# Test DELETE /data/<id>
def test_delete_data(client, mock_dataset):
    response = client.delete('/data/1')
    assert response.status_code == 200
    result = response.get_json()
    assert result['message'] == 'Data entry 1 deleted'

# Test POST /data (add a new data entry)
def test_add_data(client, mock_dataset):
    new_data = {
        'lat': 35.0, 
        'lon': -115.0,  
        'pm25': 19.0
    }
    response = client.post('/data', json=new_data)
    assert response.status_code == 201
    data = response.get_json()
    
    # Expect the closest lat/lon to be updated, which are 30.0 and -110.0
    assert data['lat'] == 30.0  
    assert data['lon'] == -110.0  
    assert data['pm25'] == 19.0  

# Test POST /data with invalid inputs

def test_add_data_invalid_input(client, mock_dataset):
    new_data = {
        'lon': -100.0,
        'pm25': 10.0
    }
    response = client.post('/data', json=new_data)
    assert response.status_code == 400
    error = response.get_json()
    assert 'lat' in error['error']

def test_add_data_invalid_pm25(client, mock_dataset):
    new_data = {
        'lat': 30.0,
        'lon': -100.0,
        'pm25': 'invalid_value'
    }
    response = client.post('/data', json=new_data)
    assert response.status_code == 400
    error = response.get_json()
    assert 'pm25' in error['error']

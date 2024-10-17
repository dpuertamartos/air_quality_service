from flask import Flask, jsonify, request
import xarray as xr
import numpy as np
import logging
import json
from threading import Lock

DATA_SET_LOCATION = './data/data.zarr'

app = Flask(__name__)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

data_lock = Lock()

try:
    ds = xr.open_zarr(DATA_SET_LOCATION, chunks={'lat': 100, 'lon': 100})
    if ds is None:
        raise ValueError("Failed to load dataset.")
except Exception as e:
    logging.error(f"Error loading dataset: {e}")
    ds = None

@app.before_request
def log_request_info():
    """
    Logs request information before processing the request.
    """
    try:
        logging.info(f"{request.remote_addr} - {request.method} {request.url}")
        if request.method in ['POST', 'PUT', 'PATCH']:
            data = request.get_json(silent=True)  
            if data:
                logging.info(f"Body: {json.dumps(data, separators=(',', ':'))}")
            else:
                logging.info("No JSON body in the request.")
    except Exception as e:
        logging.error(f"Error logging request data: {e}", exc_info=True)


def get_data_entry(index):
    try:
        total_points = ds.sizes['lat'] * ds.sizes['lon']
        if index < 0 or index >= total_points:
            return None

        lat_size = ds.sizes['lat']
        lon_size = ds.sizes['lon']
        lat_idx = index // lon_size
        lon_idx = index % lon_size

        lat_value = ds['lat'].isel(lat=lat_idx).values.item()
        lon_value = ds['lon'].isel(lon=lon_idx).values.item()
        pm25_value = ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).values.item()

        pm25_value = float(pm25_value) if not np.isnan(pm25_value) else None

        return {
            'id': int(index),
            'lat': float(lat_value),
            'lon': float(lon_value),
            'pm25': pm25_value
        }
    except Exception as e:
        logging.error(f"Error getting data entry: {e}", exc_info=True)
        return None

@app.route('/data/<int:id>', methods=['GET'])
def get_data_by_id(id):
    try:
        entry = get_data_entry(id)
        if entry is not None:
            return jsonify(entry)
        else:
            return jsonify({'error': 'Data not found'}), 404
    except Exception as e:
        logging.error(f"Error retrieving data by ID: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# Implemented with pagination
@app.route('/data', methods=['GET'])
def get_all_data():
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=100, type=int)
        start = (page - 1) * per_page
        end = start + per_page

        total_points = ds.sizes['lat'] * ds.sizes['lon']
        if start >= total_points:
            return jsonify([])

        data = []
        for idx in range(start, min(end, total_points)):
            entry = get_data_entry(idx)
            if entry is not None:
                data.append(entry)
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error retrieving all data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/data/filter', methods=['GET'])
def filter_data():
    try:
        year = request.args.get('year', type=int)
        lat = request.args.get('lat', type=float)
        lon = request.args.get('long', type=float)

        if lat is None or lon is None:
            return jsonify({'error': 'Latitude and Longitude are required'}), 400

        # Find the nearest indices
        lat_idx = np.abs(ds['lat'].values - lat).argmin()
        lon_idx = np.abs(ds['lon'].values - lon).argmin()

        pm25_value = ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).values.item()
        pm25_value = float(pm25_value) if not np.isnan(pm25_value) else None

        result = {
            'lat': float(ds['lat'].isel(lat=lat_idx).values.item()),
            'lon': float(ds['lon'].isel(lon=lon_idx).values.item()),
            'pm25': pm25_value
        }

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error filtering data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500



@app.route('/data/stats', methods=['GET'])
def get_stats():
    try:
        pm25_da = ds['GWRPM25']

        count = int(pm25_da.count().compute())
        mean_pm25 = float(pm25_da.mean().compute())
        min_pm25 = float(pm25_da.min().compute())
        max_pm25 = float(pm25_da.max().compute())

        stats = {
            'count': count,
            'mean_pm25': mean_pm25,
            'min_pm25': min_pm25,
            'max_pm25': max_pm25
        }
        return jsonify(stats)
    except Exception as e:
        logging.error(f"Error calculating statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/data', methods=['POST'])
def add_data():
    with data_lock:
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            lat = data.get('lat')
            lon = data.get('lon')
            pm25 = data.get('pm25')

            if lat is None or lon is None or pm25 is None:
                return jsonify({'error': 'lat, lon, and pm25 are required fields'}), 400

            # Validate that pm25 is a number
            if not isinstance(pm25, (int, float)):
                return jsonify({'error': 'pm25 must be a number'}), 400

            lat_idx = np.abs(ds['lat'].values - lat).argmin()
            lon_idx = np.abs(ds['lon'].values - lon).argmin()
            ds['GWRPM25'][lat_idx, lon_idx] = pm25
            ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).load()

            updated_entry = get_data_entry(lat_idx * ds.sizes['lon'] + lon_idx)
            return jsonify(updated_entry), 201

        except Exception as e:
            logging.error(f"Error adding data: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500


@app.route('/data/<int:id>', methods=['PUT'])
def update_data(id):
    with data_lock:
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            total_points = ds.sizes['lat'] * ds.sizes['lon']
            if id < 0 or id >= total_points:
                return jsonify({'error': 'Invalid ID'}), 404

            lat_size = ds.sizes['lat']
            lon_size = ds.sizes['lon']
            lat_idx = id // lon_size
            lon_idx = id % lon_size

            pm25 = data.get('pm25')
            if pm25 is None:
                return jsonify({'error': 'pm25 is required to update'}), 400

            ds['GWRPM25'][lat_idx, lon_idx] = pm25
            ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).load()

            updated_entry = get_data_entry(id)
            return jsonify(updated_entry)

        except Exception as e:
            logging.error(f"Error updating data: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500


@app.route('/data/<int:id>', methods=['DELETE'])
def delete_data(id):
    with data_lock:
        try:
            total_points = ds.sizes['lat'] * ds.sizes['lon']
            if id < 0 or id >= total_points:
                return jsonify({'error': 'Invalid ID'}), 404

            lat_size = ds.sizes['lat']
            lon_size = ds.sizes['lon']
            lat_idx = id // lon_size
            lon_idx = id % lon_size

            ds['GWRPM25'][lat_idx, lon_idx] = np.nan
            ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).load()

            return jsonify({'message': f'Data entry {id} deleted'}), 200

        except Exception as e:
            logging.error(f"Error deleting data: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


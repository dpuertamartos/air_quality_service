from flask import jsonify, request
from app.utils import get_data_entry, get_lat_lon_indices
import logging
import numpy as np
import json

def init_routes(app, ds, data_lock):
    
    @app.before_request
    def log_request_info():
        """
        Logs request information (including body) in a single line before processing the request.
        """
        try:
            # Base log message with request details
            log_message = f"{request.remote_addr} - {request.method} {request.url}"

            # If the request method involves a body, append it to the log
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json(silent=True)
                if data:
                    log_message += f" - Body: {json.dumps(data, separators=(',', ':'))}"
                else:
                    log_message += " - No JSON body in the request."

            # Log the combined message in one line
            logging.info(log_message)

        except Exception as e:
            logging.error(f"Error logging request data: {e}", exc_info=True)

    @app.route('/data/<int:id>', methods=['GET'])
    def get_data_by_id(id):
        """
        Retrieves data entry by ID.
        """
        try:
            entry = get_data_entry(id, ds)
            if entry is not None:
                return jsonify(entry)
            else:
                return jsonify({'error': 'Data not found'}), 404
        except Exception as e:
            logging.error(f"Error retrieving data by ID: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/data', methods=['GET'])
    def get_all_data():
        """
        Retrieves all data entries with pagination support.
        """
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
                entry = get_data_entry(idx, ds)
                if entry is not None:
                    data.append(entry)
            return jsonify(data)
        except Exception as e:
            logging.error(f"Error retrieving all data: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/data/filter', methods=['GET'])
    def filter_data():
        """
        Filters data based on latitude and longitude, and optionally year.
        """
        try:
            lat = request.args.get('lat', type=float)
            lon = request.args.get('long', type=float)

            if lat is None or lon is None:
                return jsonify({'error': 'Latitude and Longitude are required'}), 400

            # Retrieves closes point to the queryed lat, lon
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
            logging.error(f"Error filtering data: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/data/stats', methods=['GET'])
    def get_stats():
        """
        Returns basic statistics (count, mean, min, max) for PM2.5 data.
        """
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
            logging.error(f"Error calculating statistics: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/data', methods=['POST'])
    def add_data():
        """
        Adds a new data entry by updating the PM2.5 value for a specific latitude and longitude.
        """
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

                if not isinstance(pm25, (int, float)):
                    return jsonify({'error': 'pm25 must be a number'}), 400

                lat_idx = np.abs(ds['lat'].values - lat).argmin()
                lon_idx = np.abs(ds['lon'].values - lon).argmin()
                ds['GWRPM25'][lat_idx, lon_idx] = pm25
                ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).load()

                updated_entry = get_data_entry(lat_idx * ds.sizes['lon'] + lon_idx, ds)
                return jsonify(updated_entry), 201

            except Exception as e:
                logging.error(f"Error adding data: {e}")
                return jsonify({'error': str(e)}), 500

    @app.route('/data/<int:id>', methods=['PUT'])
    def update_data(id):
        """
        Updates an existing data entry by ID.
        """
        with data_lock:
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400

                total_points = ds.sizes['lat'] * ds.sizes['lon']
                if id < 0 or id >= total_points:
                    return jsonify({'error': 'Invalid ID'}), 404

                lat_idx, lon_idx = get_lat_lon_indices(id, ds)

                pm25 = data.get('pm25')
                if pm25 is None:
                    return jsonify({'error': 'pm25 is required to update'}), 400

                ds['GWRPM25'][lat_idx, lon_idx] = pm25
                ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).load()

                updated_entry = get_data_entry(id, ds)
                return jsonify(updated_entry)

            except Exception as e:
                logging.error(f"Error updating data: {e}")
                return jsonify({'error': str(e)}), 500

    @app.route('/data/<int:id>', methods=['DELETE'])
    def delete_data(id):
        """
        Deletes a data entry by setting the PM2.5 value to NaN for the given ID.
        """
        with data_lock:
            try:
                total_points = ds.sizes['lat'] * ds.sizes['lon']
                if id < 0 or id >= total_points:
                    return jsonify({'error': 'Invalid ID'}), 404

                lat_idx, lon_idx = get_lat_lon_indices(id, ds)

                ds['GWRPM25'][lat_idx, lon_idx] = np.nan
                ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).load()

                return jsonify({'message': f'Data entry {id} deleted'}), 200

            except Exception as e:
                logging.error(f"Error deleting data: {e}")
                return jsonify({'error': str(e)}), 500

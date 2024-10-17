from flask import request
from app.api_utils import generate_response, extract_and_validate_json
from app.data_set_utils import ( 
    calculate_pm25_statistics, get_data_entry, get_lat_lon_indices, get_pm25_at_lat_lon, 
    paginate_data, update_pm25_value, is_valid_id
)
import logging
import numpy as np
import json
import dask

def init_routes(app, ds, data_lock, celery):

    @app.before_request
    def log_request_info():
        """
        Logs request information (including body) in a single line before processing the request.
        """
        try:
            log_message = f"{request.remote_addr} - {request.method} {request.url}"

            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json(silent=True)
                if data:
                    log_message += f" - Body: {json.dumps(data, separators=(',', ':'))}"
                else:
                    log_message += " - No JSON body in the request."

            logging.info(log_message)
        except Exception as e:
            logging.error(f"Error logging request data: {e}", exc_info=True)

    @celery.task(bind=True)
    def calculate_stats_task(self):
        """
        Background task to calculate statistics using Celery.
        """
        try:
            return calculate_pm25_statistics(ds)
        except Exception as e:
            self.update_state(state='FAILURE', meta={'exc': str(e)})
            raise

    @app.route('/data/stats-async', methods=['GET'])
    def get_stats_async():
        """
        Trigger the Celery task for calculating statistics asynchronously.
        """
        task = calculate_stats_task.apply_async()
        return generate_response(data={'task_id': task.id}, status_code=202)

    @app.route('/data/stats/<task_id>', methods=['GET'])
    def get_stats_result(task_id):
        """
        Check the status of the Celery task and return the result when ready.
        """
        task = calculate_stats_task.AsyncResult(task_id)
        if task.state == 'PENDING':
            response = {'state': task.state, 'status': 'Statistics calculation is pending...'}
        elif task.state == 'SUCCESS':
            response = {'state': task.state, 'result': task.result}
        else:
            response = {'state': task.state, 'status': 'Statistics calculation failed.'}

        return generate_response(data=response)

    @app.route('/data/stats', methods=['GET'])
    def get_stats():
        """
        Perform synchronous statistics calculation using Dask.
        """
        try:
            result = calculate_pm25_statistics(ds)
            return generate_response(data=result)
        except Exception as e:
            logging.error(f"Error calculating statistics: {e}", exc_info=True)
            return generate_response(error=str(e), status_code=500)

    @app.route('/data', methods=['GET'])
    def get_all_data():
        """
        Retrieves all data entries with pagination support.
        """
        try:
            page = request.args.get('page', default=1, type=int)
            per_page = request.args.get('per_page', default=100, type=int)
            data = paginate_data(ds, page, per_page)
            return generate_response(data=data)
        except Exception as e:
            logging.error(f"Error retrieving all data: {e}")
            return generate_response(error=str(e), status_code=500)

    @app.route('/data/<int:id>', methods=['GET'])
    def get_data_by_id(id):
        """
        Retrieves data entry by ID.
        """
        try:
            entry = get_data_entry(id, ds)
            if entry is not None:
                return generate_response(data=entry)
            else:
                return generate_response(error='Data not found', status_code=404)
        except Exception as e:
            logging.error(f"Error retrieving data by ID: {e}")
            return generate_response(error=str(e), status_code=500)

    @app.route('/data/filter', methods=['GET'])
    def filter_data():
        """
        Filters data based on latitude and longitude.
        """
        try:
            lat = request.args.get('lat', type=float)
            lon = request.args.get('long', type=float)

            if lat is None or lon is None:
                return generate_response(error='Latitude and Longitude are required', status_code=400)

            lat_idx = np.abs(ds['lat'].values - lat).argmin()
            lon_idx = np.abs(ds['lon'].values - lon).argmin()

            pm25_value = get_pm25_at_lat_lon(ds, lat_idx, lon_idx)

            result = {
                'lat': float(ds['lat'].isel(lat=lat_idx).values.item()),
                'lon': float(ds['lon'].isel(lon=lon_idx).values.item()),
                'pm25': pm25_value
            }

            return generate_response(data=result)
        except Exception as e:
            logging.error(f"Error filtering data: {e}")
            return generate_response(error=str(e), status_code=500)

    @app.route('/data', methods=['POST'])
    def add_data():
        """
        Adds a new data entry by updating the PM2.5 value for a specific latitude and longitude.
        """
        with data_lock:
            try:
                data, error = extract_and_validate_json(request, ['lat', 'lon', 'pm25'], numeric_fields=['lat', 'lon', 'pm25'])

                if error:
                    return generate_response(error=error, status_code=400)

                lat_idx = np.abs(ds['lat'].values - data['lat']).argmin()
                lon_idx = np.abs(ds['lon'].values - data['lon']).argmin()
                update_pm25_value(ds, lat_idx, lon_idx, data['pm25'])

                updated_entry = get_data_entry(lat_idx * ds.sizes['lon'] + lon_idx, ds)

                return generate_response(data=updated_entry, status_code=201)
            except Exception as e:
                logging.error(f"Error adding data: {e}")
                return generate_response(error=str(e), status_code=500)

    @app.route('/data/<int:id>', methods=['PUT'])
    def update_data(id):
        """
        Updates an existing data entry by ID.
        """
        with data_lock:
            try:
                if not is_valid_id(id, ds):
                    return generate_response(error='Invalid ID', status_code=404)

                data, error = extract_and_validate_json(request, ['pm25'], numeric_fields=['pm25'])

                if error:
                    return generate_response(error=error, status_code=400)

                lat_idx, lon_idx = get_lat_lon_indices(id, ds)
                update_pm25_value(ds, lat_idx, lon_idx, data['pm25'])

                updated_entry = get_data_entry(id, ds)

                return generate_response(data=updated_entry)
            except Exception as e:
                logging.error(f"Error updating data: {e}")
                return generate_response(error=str(e), status_code=500)

    @app.route('/data/<int:id>', methods=['DELETE'])
    def delete_data(id):
        """
        Deletes a data entry by setting the PM2.5 value to NaN for the given ID.
        """
        with data_lock:
            try:
                if not is_valid_id(id, ds):
                    return generate_response(error='Invalid ID', status_code=404)

                lat_idx, lon_idx = get_lat_lon_indices(id, ds)
                update_pm25_value(ds, lat_idx, lon_idx, pm25=np.nan)

                return generate_response(data={'message': f'Data entry {id} deleted'}, status_code=200)
            except Exception as e:
                logging.error(f"Error deleting data: {e}")
                return generate_response(error=str(e), status_code=500)

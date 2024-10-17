data_set_location = "./data/data.zarr"
port = 5000

## gunicorn config

bind = f'0.0.0.0:{port}'
workers = 4
loglevel = 'info'
accesslog = None # Gunicorn does not need to log as we already implemented custom logging
errorlog = '-'   # Log to stderr
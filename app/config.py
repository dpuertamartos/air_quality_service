data_set_location = "./data/data.zarr"
port = 5000

## gunicorn config

bind = f'0.0.0.0:{port}'
workers = 4  # Number of workers based on your server's CPU cores
loglevel = 'info'
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
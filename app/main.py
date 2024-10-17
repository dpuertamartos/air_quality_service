from flask import Flask
from app.data_loader import load_dataset
from app.routes import init_routes
from app.config import data_set_location, port
import logging
from threading import Lock

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

data_lock = Lock()
ds = load_dataset(data_set_location)

init_routes(app, ds, data_lock)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)

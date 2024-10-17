from flask import Flask
from app.data_loader import load_dataset
from app.routes import init_routes
from app.config import data_set_location, port
import logging
from threading import Lock

app = Flask(__name__)

# Configure logging, and set propagate to False to avoid duplication
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.propagate = False

data_lock = Lock()
ds = load_dataset(data_set_location)

init_routes(app, ds, data_lock)

if __name__ == '__main__':
    # Disable Werkzeug's default logging to avoid duplicate logs
    import logging
    log = logging.getLogger('werkzeug')
    log.disabled = True
    app.logger.disabled = False  # Keep the main logger enabled
    app.run(host='0.0.0.0', port=port)
    logging.info("#########-------- AIR QUALITY SERVICE launched --------#########")

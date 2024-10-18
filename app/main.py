from flask import Flask
from app.utils.data_loader import load_dataset
from app.routes.main import init_routes
from app.config.main import data_set_location, port
import logging
from threading import Lock
from app.config.celery_config import make_celery

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='memory://',  # In-memory broker
    CELERY_RESULT_BACKEND='cache+memory://'  # In-memory result backend
)
celery = make_celery(app)

# Configure logging, and set propagate to False to avoid duplication
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.propagate = False

data_lock = Lock()
ds = load_dataset(data_set_location)

init_routes(app, ds, data_lock, celery)

if __name__ == '__main__':
    # Disable Werkzeug's default logging to avoid duplicate logs
    import logging
    log = logging.getLogger('werkzeug')
    log.disabled = True
    app.logger.disabled = False  # Keep the main logger enabled
    logging.info("#########-------- AIR QUALITY SERVICE launched --------#########")
    app.run(host='0.0.0.0', port=port)
    

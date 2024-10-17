from flask import Flask, jsonify
import string
import random
import requests  
import logging
import os
import json

app = Flask(__name__)

@app.before_request
def log_request_info():
    try:
        data = request.get_json()
        if data:
            logging.info(f"{request.remote_addr} - {request.method} {request.url} - Body: {json.dumps(data, separators=(',', ':'))}")
    except Exception as e:
        logging.error(f"Error logging request data: {e}")
        
def generate_random_string(string_length=10):
    """
    Generates a random string of string_length size
    """
    all_alphanum_chars = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
    random_str = "".join(random.choice(all_alphanum_chars) for _ in range(string_length))
    return random_str

@app.route('/')
def random_string():
    """
    Endpoint to generate and show a random string
    """
    try:
        random_str = generate_random_string()
        return jsonify({'random_string': random_str})
    except Exception as e:
        logging.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
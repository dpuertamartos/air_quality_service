# Air_quality_service

Containerized flask api that serves air quality data

# How to test (linux)

Creation of virtual environment (change for windows)

0. Install python 3.11

1. `python -m venv .venv`

2. `pip install -r requirements.txt`

3. `source .venv/bin/activate`

Simplely run in root folder

4. `pytest`

# How to launch app

## OPTION 1: USE PREBUILT DOCKER IMAGE

Use the prebuilt docker image

`docker run -p 5000:5000 dpuertamartos/air-quality-microservice`

api will be exposed in `http://127.0.0.1:5000` / `http://0.0.0.0:5000`

## OPTION 2: Run locally

0. Install python 3.11
1. `git clone <repository-url>`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. Transform data to `.zarr` format by launching `python ./data_transformation/convert_to_zarr.py`
5. Run application`python -m app.main`
2. Build docker image by launching `build.sh`

## OPTION 3: Build your own Docker image

1. Clone repo
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. Transform data to `.zarr` format by launching `python ./data_transformation/convert_to_zarr.py`
5. `docker build -t air-quality -f Dockerfile .` 
6. `docker run -p 5000:5000 air-quality`





# Air Quality Service

This is a containerized Flask API that serves air quality data and supports both synchronous and asynchronous statistics calculations using Dask and Celery.

## How to Test (Linux)

### Setup Virtual Environment and Run Tests:

0. **Install Python 3.11**

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

4. Run tests using pytest:
   ```bash
   pytest
   ```

## How to Launch the App

### OPTION 1: Use Prebuilt Docker Image

You can run the prebuilt Docker image using the following command:

```bash
docker run -p 5000:5000 dpuertamartos/air-quality-microservice
```

The API will be exposed at:

- `http://127.0.0.1:5000`
- `http://0.0.0.0:5000`

### OPTION 2: Run Locally

0. **Install Python 3.11**

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Set up the virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Convert the data to `.zarr` format:
   ```bash
   python ./data_transformation/convert_to_zarr.py
   ```

5. Run the application:
   ```bash
   python -m app.main
   ```

### OPTION 3: Build Your Own Docker Image

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Set up the virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Convert the data to `.zarr` format:
   ```bash
   python ./data_transformation/convert_to_zarr.py
   ```

4. Build the Docker image:
   ```bash
   docker build -t air-quality -f Dockerfile .
   ```

5. Run the Docker container:
   ```bash
   docker run -p 5000:5000 air-quality
   ```

---

## API Endpoints

### 1. Get Data by ID
- **Endpoint**: `/data/<id>`
- **Method**: `GET`
- **Description**: Retrieves a data entry by its ID.
- **Example**:
  ```bash
  GET http://127.0.0.1:5000/data/1
  ```

### 2. Get All Data (with Pagination)
- **Endpoint**: `/data`
- **Method**: `GET`
- **Description**: Retrieves all data entries with pagination support. By default, it fetches the first page with 100 results.
- **Parameters**:
  - `page` (optional): Page number (default: 1)
  - `per_page` (optional): Number of entries per page (default: 100)
- **Example**:
  ```bash
  GET http://127.0.0.1:5000/data?page=1&per_page=100
  ```

### 3. Filter Data by Latitude and Longitude
- **Endpoint**: `/data/filter`
- **Method**: `GET`
- **Description**: Retrieves PM2.5 data for the nearest latitude and longitude provided in the query.
- **Parameters**:
  - `lat`: Latitude of the location
  - `long`: Longitude of the location
- **Example**:
  ```bash
  GET http://127.0.0.1:5000/data/filter?lat=30.0&long=-90.0
  ```

### 4. Add New Data Entry
- **Endpoint**: `/data`
- **Method**: `POST`
- **Description**: Adds a new data entry by updating the PM2.5 value for a specific latitude and longitude.
- **Example**:
  ```bash
  POST http://127.0.0.1:5000/data
  Content-Type: application/json
  {
      "lat": 30.0,
      "lon": -90.0,
      "pm25": 12.5
  }
  ```

### 5. Update Data Entry by ID
- **Endpoint**: `/data/<id>`
- **Method**: `PUT`
- **Description**: Updates an existing data entry by ID.
- **Example**:
  ```bash
  PUT http://127.0.0.1:5000/data/1
  Content-Type: application/json
  {
      "pm25": 15.0
  }
  ```

### 6. Delete Data Entry by ID
- **Endpoint**: `/data/<id>`
- **Method**: `DELETE`
- **Description**: Deletes a data entry by setting its PM2.5 value to `NaN`.
- **Example**:
  ```bash
  DELETE http://127.0.0.1:5000/data/1
  ```

### 7. Get Basic Statistics (Synchronous)
- **Endpoint**: `/data/stats`
- **Method**: `GET`
- **Description**: Retrieves basic statistics (count, mean, min, max) for PM2.5 data synchronously using Dask.
- **Example**:
  ```bash
  GET http://127.0.0.1:5000/data/stats
  ```

### 8. Get Basic Statistics (Asynchronous)
- **Endpoint**: `/data/stats-async`
- **Method**: `GET`
- **Description**: Initiates an asynchronous task to calculate PM2.5 statistics using Celery.
- **Example**:
  ```bash
  GET http://127.0.0.1:5000/data/stats-async
  ```

### 9. Get Task Result (Asynchronous)
- **Endpoint**: `/data/stats/<task_id>`
- **Method**: `GET`
- **Description**: Retrieves the result of the asynchronous statistics calculation task.
- **Example**:
  ```bash
  GET http://127.0.0.1:5000/data/stats/<task_id>
  ```

---

### Requests Example (For Reference)

The file `requests/example_request.rest` provides example API requests for testing the service using a REST client.

---

### Notes

- The API provides both synchronous and asynchronous methods for calculating statistics using Dask and Celery.
- The application supports both local and containerized execution.

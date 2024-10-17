import xarray as xr
import logging

DATA_SET_LOCATION = './data/data.zarr'

def load_dataset():
    try:
        ds = xr.open_zarr(DATA_SET_LOCATION, chunks={'lat': 100, 'lon': 100})
        if ds is None:
            raise ValueError("Failed to load dataset.")
        return ds
    except Exception as e:
        logging.error(f"Error loading dataset: {e}")
        return None

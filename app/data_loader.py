import xarray as xr
import logging

def load_dataset(data_set_location):
    try:
        ds = xr.open_zarr(data_set_location, chunks={'lat': 100, 'lon': 100})
        if ds is None:
            raise ValueError("Failed to load dataset.")
        return ds
    except Exception as e:
        logging.error(f"Error loading dataset: {e}")
        return None

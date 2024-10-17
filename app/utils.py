import logging
import numpy as np

def get_data_entry(index, ds):
    try:
        total_points = ds.sizes['lat'] * ds.sizes['lon']
        if index < 0 or index >= total_points:
            return None

        lat_size = ds.sizes['lat']
        lon_size = ds.sizes['lon']
        lat_idx = index // lon_size
        lon_idx = index % lon_size

        lat_value = ds['lat'].isel(lat=lat_idx).values.item()
        lon_value = ds['lon'].isel(lon=lon_idx).values.item()
        pm25_value = ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).values.item()

        pm25_value = float(pm25_value) if not np.isnan(pm25_value) else None

        return {
            'id': int(index),
            'lat': float(lat_value),
            'lon': float(lon_value),
            'pm25': pm25_value
        }
    except Exception as e:
        logging.error(f"Error getting data entry: {e}", exc_info=True)
        return None

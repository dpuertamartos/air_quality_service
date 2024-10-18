import logging
import numpy as np
import dask

def calculate_pm25_statistics(ds):
    """
    Calculate PM2.5 statistics (count, mean, min, max) using Dask.
    
    Args:
        ds: The dataset containing PM2.5 data.
        
    Returns:
        A dictionary with the calculated statistics.
    """
    pm25_da = ds['GWRPM25']
    count, mean_pm25, min_pm25, max_pm25 = dask.compute(
        pm25_da.count(), 
        pm25_da.mean(), 
        pm25_da.min(), 
        pm25_da.max()
    )
    
    return {
        'count': int(count),
        'mean_pm25': float(mean_pm25),
        'min_pm25': float(min_pm25),
        'max_pm25': float(max_pm25)
    }

def get_lat_lon_indices(id, ds):
    """
    Given an ID and dataset, calculate the corresponding latitude and longitude indices.
    
    Args:
        id (int): The ID representing the 1D index.
        ds (xarray.Dataset): The dataset containing latitude and longitude sizes.

    Returns:
        tuple: (lat_idx, lon_idx) representing the indices in the dataset.
    """
    lon_size = ds.sizes['lon']
    lat_idx = id // lon_size
    lon_idx = id % lon_size
    return lat_idx, lon_idx


def get_data_entry(index, ds):
    try:
        total_points = ds.sizes['lat'] * ds.sizes['lon']
        if index < 0 or index >= total_points:
            return None

        lat_idx, lon_idx = get_lat_lon_indices(index, ds)

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
    

def get_pm25_at_lat_lon(ds, lat_idx, lon_idx):
    """
    Retrieve PM2.5 value for a given latitude and longitude indices.
    
    Args:
        ds: The dataset.
        lat_idx: Latitude index.
        lon_idx: Longitude index.
    
    Returns:
        PM2.5 value (None if NaN).
    """
    pm25_value = ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).values.item()
    return float(pm25_value) if not np.isnan(pm25_value) else None

def update_pm25_value(ds, lat_idx, lon_idx, pm25):
    ds['GWRPM25'][lat_idx, lon_idx] = pm25
    ds['GWRPM25'].isel(lat=lat_idx, lon=lon_idx).load()


def is_valid_id(id, ds):
    total_points = ds.sizes['lat'] * ds.sizes['lon']
    return 0 <= id < total_points

def paginate_data(ds, page, per_page):
    """
    Paginate data from the dataset.
    
    Args:
        ds: The dataset.
        page: Page number.
        per_page: Number of entries per page.
    
    Returns:
        List of data entries for the specified page.
    """
    start = (page - 1) * per_page
    end = start + per_page

    total_points = ds.sizes['lat'] * ds.sizes['lon']
    if start >= total_points:
        return []

    data = []
    for idx in range(start, min(end, total_points)):
        entry = get_data_entry(idx, ds)
        if entry is not None:
            data.append(entry)
    return data


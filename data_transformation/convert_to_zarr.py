import xarray as xr

# Open the NetCDF file using Xarray with Dask
ds = xr.open_dataset('./data_transformation/data.nc', chunks={'lat': 100, 'lon': 100})

# Convert to Zarr format
ds.to_zarr('./data/data.zarr', mode='w')

import ee
import geemap
try:
    ee.Initialize() # enter the name of your cloud project here
except:
    ee.Authenticate()
    ee.Initialize()

# select the desired year to call images for
year = 2023
# put the coordinates for your aoi
geom = ee.Geometry.Polygon([48.166713, 30.837769,48.166713, 31.190857,48.682985, 31.190857,48.682985, 30.837769,48.166713, 30.837769])

# 1. Sentinel-2 image selection
s2_image = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
    .filterBounds(geom) \
    .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year + 1, 1, 1)) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
    .sort('CLOUDY_PIXEL_PERCENTAGE') \
    .first() \
    .clip(geom)

# Define the target projection from a 10m band. This is our ground truth grid.
target_projection = s2_image.select('B4').projection()

# 2. Select and scale bands at their native resolutions
bands_10m = s2_image.select(['B2', 'B3', 'B4', 'B8']).multiply(0.0001)
bands_20m = s2_image.select(['B5', 'B6', 'B7', 'B8A', 'B11', 'B12']).multiply(0.0001)
bandNames_20m = bands_20m.bandNames()

# 3. Create a spectrally accurate panchromatic band using a weighted average
# These weights are standard for creating luminance from RGB+NIR 
pan = bands_10m.expression(
    'R * 0.299 + G * 0.587 + B * 0.114 + NIR * 0.3', {
      'R': bands_10m.select('B4'),
      'G': bands_10m.select('B3'),
      'B': bands_10m.select('B2'),
      'NIR': bands_10m.select('B8')
}).rename('pan')

# 4. Idiomatic Resampling of 20m Bands
# Use 'bicubic' for smoother results
upsampled_20m = bands_20m.resample('bicubic').reproject(crs=target_projection)

# 5. High-Pass Filter and Vectorized Gain Calculation
kernel = ee.Kernel.laplacian8() # A standard high-pass kernel
hpf = pan.convolve(kernel).rename('hpf')

# Calculate standard deviations for all bands at once
stats = upsampled_20m.addBands(hpf).reduceRegion(
    reducer=ee.Reducer.stdDev(),
    geometry=geom,
    scale=30, # Use a slightly coarser scale for efficiency
    maxPixels=1e9,
    bestEffort=True
)

# Extract stdDev values in a server-side manner
hpf_std_dev = ee.Number(stats.get('hpf'))
std_devs_20m = ee.Image.constant(stats.toArray(bandNames_20m).toList())

# Vectorized Gain: Create a multi-band gain image instead of separate numbers
mod = 0.25
gains = std_devs_20m.divide(hpf_std_dev).multiply(mod)

# Apply gains to the HPF to create a multi-band "details" image
# GEE automatically broadcasts the single-band HPF across the gain bands
details = hpf.multiply(gains)

# 6. Final Combination
# Add the calculated details to the upsampled 20m bands in one operation
sharpened_20m = upsampled_20m.add(details).rename(bandNames_20m)

# Combine the original 10m bands with the newly sharpened 20m bands
final_image_10m = bands_10m.addBands(sharpened_20m)

# --- Visualization ---
vis_params_rgb = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3}
Map = geemap.Map()
Map.centerObject(geom, 12)
Map.addLayer(s2_image, vis_params_rgb, 'Original S2 Image')
Map.addLayer(final_image_10m, vis_params_rgb, 'Pan-Sharpened Image (10m)')
# display(Map)

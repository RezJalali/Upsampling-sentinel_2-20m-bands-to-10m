# Efficient Sentinel-2 Pansharpening in Google Earth Engine Python API🛰️
This repository contains a Python script that demonstrates an efficient, GEE-idiomatic method for upsampling Sentinel-2's 20-meter resolution bands to 10 meters. The technique uses a high-frequency modulation approach, leveraging the existing 10m bands to create a spectrally consistent, visually sharp, and analysis-ready final image.

## The Challenge: Mixed Resolutions in Sentinel-2
Sentinel-2 is a fantastic data source, but its multispectral bands come in different spatial resolutions (10m, 20m, and 60m). For many applications, such as detailed land cover classification, object detection, or simply creating beautiful, crisp imagery, it's essential to have all bands at the highest possible resolution. The challenge is to increase the resolution of the 20m bands without distorting their valuable spectral information.

**The Solution: A High-Frequency Modulation Approach**
This script implements a pan-sharpening-like method entirely within the Google Earth Engine ecosystem. Instead of using a dedicated panchromatic band (which Sentinel-2 lacks), we create a synthetic panchromatic band from the high-resolution 10m bands. We then extract the high-frequency spatial details from this synthetic band and intelligently inject them into the 20m bands.

The following images show a False Color Composite of B8A-B11 & and B12 bands before and after applying this pansharpening method respectively.
`**Before**`
<img width="1307" height="662" alt="20m" src="https://github.com/user-attachments/assets/7a58e59d-65b2-4941-93f7-12cd92bd11ac" />
`**After**`
<img width="1315" height="666" alt="10m" src="https://github.com/user-attachments/assets/dd5319cb-283b-412a-ab5f-e0cf8d882e98" />


The core methodology is as follows:

1. Create a Panchromatic Proxy: A single high-resolution band is synthesized by calculating a weighted average of the 10m bands (B2, B3, B4, B8).

2. Extract Spatial Details: A Laplacian High-Pass Filter is applied to the panchromatic proxy. This isolates the fine details like edges, textures, and small features.

3. Calculate Adaptive Gains: To preserve the spectral integrity of the original data, we don't just add the same details to every 20m band. Instead, we calculate a unique gain for each band. This gain is based on the ratio of the standard deviation of the 20m band to the standard deviation of the high-pass filter. This ensures that the amount of detail added is proportional and spectrally consistent.

4. Inject and Combine: The modulated details are added to the bicubically upsampled 20m bands. The final product is a single image containing the original 10m bands and the newly sharpened 20m bands, all at a crisp 10m resolution.

## Key Features & Why This Approach Works
- Fully GEE-Idiomatic: The entire workflow is performed using server-side functions. There's no client-side looping or slow data transfer.

- Highly Efficient: The script is optimized for performance. For instance, it uses a single reduceRegion call with a composite reducer (ee.Reducer.stdDev()) to calculate statistics for all bands at once.

- Vectorized Operations: Gain calculations are performed in a vectorized manner by creating a multi-band gain image and applying it to the detail layer in a single step. This is significantly faster and cleaner than processing each band individually.

- Spectrally Consistent: The adaptive gain calculation helps to minimize color distortion, a common problem in more naive pan-sharpening methods.

- No External Data Required: The sharpening process is self-contained, using only the information present within the Sentinel-2 image itself.

## How to Use
Prerequisites
* A Google Earth Engine account.
* Python environment with the following libraries installed:
  - earthengine-api
  - geemap

## Steps
1. Authenticate with GEE: If it's your first time running the script, you will be prompted to authenticate and authorize access to your GEE account.

2. Customize Your Inputs: Open the script and modify the following variables at the top:

3. year: Set the desired year for your analysis.

4. geom: Replace the example ee.Geometry.Polygon with your own Area of Interest (AOI).

5. Run the Script: Execute the Python script. It will perform all the processing on Google's servers and display the "before" and "after" images in an interactive geemap window.

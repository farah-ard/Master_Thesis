#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, redirect, Response, request, url_for, jsonify
import requests
from PIL import Image
from io import BytesIO
from algorithms import *
import numpy as np
from matplotlib import pyplot as plt
from scipy import ndimage
from skimage import measure, color, io
from stardist.models import StarDist2D
from stardist.plot import render_label
from csbdeep.utils import normalize
import matplotlib.pyplot as plt
from tifffile import imread
from csbdeep.utils import Path, normalize

from stardist import random_label_cmap, _draw_polygons, export_imagej_rois

lbl_cmap = random_label_cmap()

# creates a pretrained model
stardist_model = StarDist2D.from_pretrained('2D_versatile_he')

ORTHANC_URL = 'https://orthanc.uclouvain.be/wsi-orthanc'
SAMPLE_SERIES = 'b5b20eac-4b5452bc-a319853c-4f7a4d1e-d91dd475'

app = Flask(__name__)

@app.route('/')
# Redirects to URL : 'viewer.html?series=%s' % SAMPLE_SERIES
def redirection():
    return redirect('viewer.html?series=%s' % SAMPLE_SERIES, code = 302)

@app.route('/viewer.html')
def get_html():
    with open('viewer.html', 'r') as f:
        return Response(f.read(), mimetype = 'text/html')

@app.route('/viewer.js')
def get_javascript():
    with open('viewer.js', 'r') as f:
        return Response(f.read(), mimetype = 'text/javascript')

@app.route('/orthanc/<path:path>')
def orthanc_proxy(path):
    # Reverse proxy to the Orthanc server from the Flask application
    r = requests.get('%s/wsi/%s' % (ORTHANC_URL, path))
    r.raise_for_status()
    print(r.headers['Content-Type'])
    return Response(r.content, mimetype = r.headers['Content-Type'])

@app.route('/download_tiles',  methods=['POST'])
def download_tiles():
    # Get data on the tiles to download from Orthanc
    data = request.get_json()
    series_id = data.get('seriesId')
    tile_table = data.get('tileTable')
    tile_size = data.get('tileSize')
    grid_size = data.get('gridSize')
    segmentation_algo = data.get('algo')

    # Create a blank image in which the tiles will be concatenated
    full_img_width = tile_size[0]*grid_size[1]
    full_img_height = tile_size[1]*grid_size[0]
    
    full_img = Image.new('RGB', (full_img_width, full_img_height))

    # Add tiles to the blank image
    for row in range(grid_size[0]):
        for col in range(grid_size[1]):
            coords = tile_table[row][col]
            url = f'{ORTHANC_URL}/wsi/tiles/{series_id}/0/{coords[1]}/{coords[0]}/'
            r = requests.get(url)
            tile = Image.open(BytesIO(r.content))

            left = col*tile_size[0]
            top = row*tile_size[1]
            
            full_img.paste(tile, (left, top))

    full_img.save('static/reconstructed_image.jpg')
    # Image processing
    if segmentation_algo == 'watershed':
        cell_detection_output = cell_detection('static/reconstructed_image.jpg', 140)

    if segmentation_algo == 'stardist':
        X = ["static/reconstructed_image.jpg"] 
        X = list(map(cv.imread,X))
        #X = [cv.imread('')]
        n_channel = 1 if X[0].ndim == 2 else X[0].shape[-1]
        axis_norm = (0,1)   # normalize channels independently
        #axis_norm = (0,1,2) # normalize channels jointly

        if n_channel > 1:
            print("Normalizing image channels %s." % ('jointly' if axis_norm is None or 2 in axis_norm else 'independently'))
        
        #cv.imwrite('static/temp_img.jpg', X[0])
        img = normalize(X[0], 1, 99.8, axis=axis_norm)

        #img_gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        #img = normalize(img_gray, 1, 99.8, axis=(0,1))
        #X = list(map(imread,X))
        #n_channel = 1 if X[0].ndim == 2 else X[0].shape[-1]
        #axis_norm = (0,1)   # normalize channels independently
        #axis_norm = (0,1,2) # normalize channels jointly

        #if n_channel > 1:
        #    print("Normalizing image channels %s." % ('jointly' if axis_norm is None or 2 in axis_norm else 'independently'))

        labels, details = stardist_model.predict_instances(img)
        cv.imwrite('static/labels.jpg', labels)
        #From ChatGPT
        # Ensure img is in the range [0, 255] and 3 channels
        if img.ndim == 2:
            img_rgb = np.stack([img] * 3, axis=-1)
        else:
            img_rgb = img[..., :3]
        img_rgb = (img_rgb * 255).astype(np.uint8)
        transparency = 0.4
        # Create label overlay with the same shape
        label_img = lbl_cmap(labels)  # This returns an RGBA image in [0,1]
        label_rgb = (label_img[..., :3] * 255).astype(np.uint8)

        # Blend images
        blended = (transparency * label_rgb + (1 - transparency) * img_rgb).astype(np.uint8)

        # Convert to PIL and save
        Image.fromarray(blended).save('static/mask_output.jpg')
        cell_detection_output = True
    
    if cell_detection_output == True:
        img_url = url_for('static',filename='mask_output.jpg')

    #full_img.save('static/reconstructed_image.jpg')
    
    #return send_file('reconstructed_image.jpg', mimetype='image/jpg')
    return jsonify({'image_url': img_url})



if __name__ == '__main__':
    app.run(debug = True)
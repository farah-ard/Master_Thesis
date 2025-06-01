#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, redirect, Response, request, url_for, jsonify
import requests
from PIL import Image
from io import BytesIO
from algorithms import *
import numpy as np
from matplotlib import pyplot as plt
from stardist.models import StarDist2D


np.random.seed(6)


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
        cell_detection('static/reconstructed_image.jpg', 140)

    if segmentation_algo == 'stardist':
        stardist("static/reconstructed_image.jpg", stardist_model)
        
        
    
    img_url = url_for('static',filename='mask_output.jpg')


    return jsonify({'image_url': img_url})



if __name__ == '__main__':
    app.run(debug = False)
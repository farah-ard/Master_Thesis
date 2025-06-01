import requests
import time
import random
import pandas as pd
from PIL import Image
from io import BytesIO
import algorithms
from stardist.models import StarDist2D
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv

# creates a pretrained model
stardist_model = StarDist2D.from_pretrained('2D_versatile_he')

ORTHANC_URL = 'https://orthanc.uclouvain.be/wsi-orthanc'
SAMPLE_SERIES = 'b5b20eac-4b5452bc-a319853c-4f7a4d1e-d91dd475'
date_and_time = time.strftime("%Y%m%d-%H%M%S")

def save_images():
    url = f'{ORTHANC_URL}/wsi/pyramids/{SAMPLE_SERIES}/'
    r = requests.get(url)
    pyramid_json = r.json()
    tile_size = pyramid_json['TilesSizes'][0]
    series_id = SAMPLE_SERIES
    grid_sizes = [[1,1], [1,2], [1,3], [2,2], [2,3], [2,4], [3,3], [3,4], [4,4]]

    for grid_size in grid_sizes:
        for i in range(20):
            # Create a blank image in which the tiles will be concatenated
            full_img_width = tile_size[0]*grid_size[1]
            full_img_height = tile_size[1]*grid_size[0]
            full_img = Image.new('RGB', (full_img_width, full_img_height))
            first_tile_x = random.randint(6, 10)
            first_tile_y = random.randint(20, 45)
            for x in range(grid_size[0]):
                for y in range(grid_size[1]):
                    url = f'{ORTHANC_URL}/wsi/tiles/{series_id}/0/{first_tile_y+y}/{first_tile_x+x}/'
                    r = requests.get(url)
                    tile = Image.open(BytesIO(r.content))

                    left = y*tile_size[0]
                    top = x*tile_size[1]
                    
                    full_img.paste(tile, (left, top))
            size = grid_size[0]*grid_size[1]
            full_img.save('tests/images/reconstructed_image_'+str(size)+'_'+str(i)+'.jpg')
    return 


def time_process_tiles():
    df = pd.DataFrame(columns=['Algo','Grid Size X','Grid Size Y','Time'])
    algos = ['watershed','stardist']
    grid_sizes = [[1,1], [1,2], [1,3], [2,2], [2,3], [2,4], [3,3], [3,4], [4,4]]
    csv_path = 'tests/time_results_'+date_and_time+'.csv'
    for algo in algos:
        for grid_size in grid_sizes:
            for i in range(20):
                image = 'tests/images/reconstructed_image_'+str(grid_size[0]*grid_size[1])+'_'+str(i)+'.jpg'
                if(algo == 'watershed'):
                    start = time.time()
                    algorithms.cell_detection(image, 140)
                    end = time.time()

                if(algo == 'stardist'):
                    start = time.time()
                    algorithms.stardist(image, stardist_model)
                    end = time.time()
                duration = end - start
                df.loc[len(df)] = [algo, grid_size[0], grid_size[1], duration]
                time.sleep(1)
                print(i)
        df.to_csv(csv_path)
    return csv_path

def make_graph(csv_path):
    df = pd.read_csv(csv_path)
    df['Grid Size'] = df['Grid Size X'] * df['Grid Size Y']
    df_grouped = df.groupby(['Algo', 'Grid Size'])['Time']
    df_avg_time = df_grouped.mean().reset_index()
    df_std_time = df_grouped.std().reset_index()
    
    plt.figure(figsize=(10, 6))

    # Plot each Algo separately
    for algo in df_avg_time['Algo'].unique():
        subset_mean = df_avg_time[df_avg_time['Algo'] == algo]
        subset_std = df_std_time[df_std_time['Algo'] == algo]
        if algo == 'watershed':
            lbl = 'Watershed'
        else:
            lbl = 'StarDist'
        plt.errorbar(subset_mean['Grid Size'], subset_mean['Time'], yerr=subset_std['Time'], label=lbl, ecolor='grey' )

    plt.xlabel('Number of Tiles')
    plt.xticks(np.arange(1, 17, step=1))
    plt.ylabel('Time (sec)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('tests/time_graph.pdf')
    return

if __name__ == '__main__':
    #save_images()
    csv_path = time_process_tiles()
    make_graph(csv_path)
    
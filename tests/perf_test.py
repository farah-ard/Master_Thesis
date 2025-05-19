import requests
import json
import time
import random
import pandas as pd

ORTHANC_URL = 'https://orthanc.uclouvain.be/wsi-orthanc'
SAMPLE_SERIES = 'b5b20eac-4b5452bc-a319853c-4f7a4d1e-d91dd475'

def time_download_tiles():
    df = pd.DataFrame(columns=['Grid Size X','Grid Size Y','Time'])
    url = f'{ORTHANC_URL}/wsi/pyramids/{SAMPLE_SERIES}/'
    r = requests.get(url)
    pyramid_json = r.json()
    nb_tiles = pyramid_json['TilesCount'][0]
    tile_size = pyramid_json['TilesSizes'][0]
    series_id = SAMPLE_SERIES
    algo = 'watershed'
    grid_sizes = [[1,1], [1,2], [1,3], [2,2], [2,3], [2,4], [3,3], [3,4], [4,4]]
    for grid_size in grid_sizes:
        for i in range(20):
            first_tile_x = random.randint(10, 30)
            first_tile_y = random.randint(10, 30)
            tile_table = []
            rows = 0
            for x in range(first_tile_x, first_tile_x+grid_size[0]):
                tile_table.append([])
                for y in range(first_tile_y, first_tile_y+grid_size[1]):
                    tile_table[rows].append([str(x),str(y)])
                rows += 1
            print(tile_table)
            data = json.loads(json.dumps({'seriesId': series_id, 'tileTable': tile_table, 'tileSize' : tile_size, 'gridSize' : grid_size, 'algo' : algo}))
            start = time.time()
            response = requests.post("http://127.0.0.1:5000/download_tiles", json=data)
            end = time.time()
            duration = end - start
            print(f"{duration:.3f} seconds")
            df.loc[len(df)] = [grid_size[0], grid_size[1], duration]
            time.sleep(3)
    df.to_csv('tests/time_results.csv')
    return data

if __name__ == '__main__':
    time_download_tiles()
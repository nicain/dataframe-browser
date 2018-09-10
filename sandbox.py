import glob
import random
import base64
import numpy as np
import pandas as pd
import requests

from PIL import Image
from io import BytesIO
# from IPython.display import HTML
# import matplotlib.image as mpi
# import matplotlib.pyplot as plt

pd.set_option('display.max_colwidth', -1)

ts = 10
def get_thumbnail(data_array):
    i = Image.frombytes( "RGB", data_array.shape, data_array )
    # i.thumbnail((ts, ts), Image.LANCZOS)
    return i

def image_base64(im):
    with BytesIO() as buffer:
        im.save(buffer, 'jpeg')
        return base64.b64encode(buffer.getvalue()).decode()

def image_formatter(im):
    return '<img height="42" width="42" src="data:image/jpeg;base64,{0}">'.format(image_base64(im))

df = pd.DataFrame({'data':[np.random.rand(50,50) for _ in range(5)]})
# print df.info()
# dogs['file'] = dogs.id.map(lambda id: f'../input/train/{id}.jpg')
df['image'] = df['data'].map(lambda f: get_thumbnail(f))
# print df['image']

html = df[['image']].to_html(formatters={'image': image_formatter}, escape=False)
print requests.post('http://localhost:5000/active', data={'data':html})
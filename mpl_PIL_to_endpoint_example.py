import glob
import random
import base64
import numpy as np
import pandas as pd
import requests

from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

pd.set_option('display.max_colwidth', -1)

ts = 10

def to_figure(data_array):
    fig, ax = plt.subplots()
    ax.imshow(data_array)

    return fig


def get_thumbnail_PIL(data_array):
    i = Image.frombytes( "RGB", data_array.shape, data_array )
    i.thumbnail((ts, ts), Image.LANCZOS)
    return i

def image_base64_PIL(im):

    with BytesIO() as buffer:
        im.save(buffer, 'jpeg')
        return base64.b64encode(buffer.getvalue()).decode()

def image_base64_mpl(im):
    with BytesIO() as buffer:
        im.savefig(buffer, format='jpeg')
        return base64.b64encode(buffer.getvalue()).decode()

def image_formatter_mpl(im):

    return '<img height="42" width="42" src="data:image/jpeg;base64,{0}">'.format(image_base64_mpl(im))

def image_formatter_PIL(im):
    
    return '<img height="42" width="42" src="data:image/jpeg;base64,{0}">'.format(image_base64_PIL(im))

df = pd.DataFrame({'data':[np.random.rand(50,50) for _ in range(5)]})

df['image_mpl'] = df['data'].map(lambda f: to_figure(f))
df['image_PIL'] = df['data'].map(lambda f: get_thumbnail_PIL(f))


html = df[['image_mpl', 'image_PIL']].to_html(formatters={'image_mpl': image_formatter_mpl, 'image_PIL': image_formatter_PIL}, escape=False)
print requests.post('http://localhost:5000/active', data={'data':html})



# ts = 10


# def image_base64(im):
#     with BytesIO() as buffer:
#         im.savefig(buffer, format='jpeg')
#         return base64.b64encode(buffer.getvalue()).decode()

# def image_formatter(im):
#     return '<img height="42" width="42" src="data:image/jpeg;base64,{0}">'.format(image_base64(im))

# df = pd.DataFrame({'data':[np.random.rand(50,50) for _ in range(5)]})
# df['image'] = df['data'].map(lambda f: get_thumbnail(f))
# html = df[['image']].to_html(formatters={'image': image_formatter}, escape=False)
# print requests.post('http://localhost:5000/active', data={'data':html})
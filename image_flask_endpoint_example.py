import glob
import random
import base64
import numpy as np
import pandas as pd
import requests
import bokeh.plotting as bkp
from bokeh.io.export import get_screenshot_as_png

from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

pd.set_option('display.max_colwidth', -1) 

def get_figure(data_array):
    fig, ax = plt.subplots()
    ax.imshow(data_array, origin='upper')

    return fig

def get_PIL(data_array):
    # print plt.cm.viridis(data_array).shape
    i = Image.frombytes( "RGBA", data_array.shape, np.uint8(255*plt.cm.viridis(data_array))).convert('RGB')
    i = i.resize((100,100))
    # i.save('/home/nicholasc/tmp2.png')
    return i

def get_bokeh(data_array):

    p = bkp.figure(x_range=(0, data_array.shape[1]), y_range=(0, data_array.shape[0]),
            tooltips=[("x", "$x"), ("y", "$y"), ("value", "@image")])

    p.image(image=[np.flipud(data_array)], x=0, y=0, dw=data_array.shape[1], dh=data_array.shape[0], palette="Viridis11")

    return p

def image_base64_PIL(im):

    with BytesIO() as buffer:
        im.save(buffer, 'jpeg')
        return base64.b64encode(buffer.getvalue()).decode()

def image_base64_mpl(im):
    with BytesIO() as buffer:
        im.savefig(buffer, format='jpeg')
        return base64.b64encode(buffer.getvalue()).decode()

def image_base64_bokeh(im):

    with BytesIO() as buffer:
        im = get_screenshot_as_png(im)
        im.convert('RGB').save(buffer, 'jpeg')
        return base64.b64encode(buffer.getvalue()).decode()

width = height = 100

format_string = '<img height="{height}" width="{width}" src="data:image/jpeg;base64,{img}">'

def image_formatter_mpl(im):

    return format_string.format(height=height, width=width, img=image_base64_mpl(im))

def image_formatter_PIL(im):
    
    return format_string.format(height=height, width=width, img=image_base64_PIL(im))
    

def image_formatter_bokeh(im):

    return format_string.format(height=height, width=width, img=image_base64_bokeh(im))
    

df = pd.DataFrame({'data':[np.random.rand(5,5) for _ in range(5)]})

df['image_mpl'] = df['data'].map(lambda f: get_figure(f))
df['image_bokeh'] = df['data'].map(lambda f: get_bokeh(f))
df['image_PIL'] = df['data'].map(lambda f: get_PIL(f))
df.drop('data', inplace=True, axis=1)

html = df[['image_mpl', 'image_PIL', 'image_bokeh']].to_html(formatters={'image_mpl': image_formatter_mpl, 'image_PIL': image_formatter_PIL, 'image_bokeh':image_formatter_bokeh}, escape=False)

print requests.post('http://localhost:5000/active', data={'data':html})

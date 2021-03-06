import glob
import random
import base64
import numpy as np
import pandas as pd
import requests
import bokeh.plotting as bkp
from bokeh.io.export import get_screenshot_as_png
from bokeh.embed import components


from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt


from cssutils import parseStyle
from bs4 import BeautifulSoup as BeautifulSoupPre
def BeautifulSoup(*args, **kwargs):
    kwargs.setdefault('features', 'lxml')
    return BeautifulSoupPre(*args, **kwargs)


pd.set_option('display.max_colwidth', -1) 

width = height = 200

def get_figure(data_array):
    fig, ax = plt.subplots()
    ax.imshow(data_array, origin='upper')

    return fig

def get_PIL(data_array):
    i = Image.frombytes( "RGBA", data_array.shape, np.uint8(255*plt.cm.viridis(data_array))).convert('RGB')
    i = i.resize((width,height))
    return i

def get_bokeh(data_array):


    im = bkp.figure(x_range=(0, data_array.shape[1]), y_range=(0, data_array.shape[0]),
            tooltips=[("x", "$x"), ("y", "$y"), ("value", "@image")], background_fill_color=None, border_fill_color=None)

    im.image(image=[np.flipud(data_array)], x=0, y=0, dw=data_array.shape[1], dh=data_array.shape[0], palette="Viridis11")

    im.plot_height=height
    im.plot_width=width
    return im

def image_base64_PIL(im):

    with BytesIO() as buffer:
        im.save(buffer, 'png')
        return base64.b64encode(buffer.getvalue()).decode()

def image_base64_mpl(im):
    with BytesIO() as buffer:
        im.savefig(buffer, format='png', transparent=True)
        return base64.b64encode(buffer.getvalue()).decode()

def image_base64_bokeh(im):

    with BytesIO() as buffer:
        im = get_screenshot_as_png(im)
        im = im.resize((width,height))
        im.convert('RGBA').save(buffer, 'png')
        return base64.b64encode(buffer.getvalue()).decode()



format_string = '<img style="height: {height}px; width: {width}px" src="data:image/png;base64,{img}">'

def image_formatter_mpl(im):

    return format_string.format(height=height, width=width, img=image_base64_mpl(im))

def image_formatter_PIL(im):
    
    return format_string.format(height=height, width=width, img=image_base64_PIL(im))

script_list = []    
def image_formatter_bokeh(im):

    # return format_string

    script, div = components(im)
    script_list.append(script)
    div = BeautifulSoup(div).div
    div['style'] = 'height: {height}px; width: {width}px'.format(height=height, width=width)

    return div

def image_formatter_bokeh_static(im):
    
    return format_string.format(height=height, width=width, img=image_base64_bokeh(im))
    

df = pd.DataFrame({'data':[np.random.rand(5,5) for _ in range(2)]})

df['image_mpl'] = df['data'].map(lambda f: get_figure(f))
df['image_bokeh'] = df['data'].map(lambda f: get_bokeh(f))
df['image_PIL'] = df['data'].map(lambda f: get_PIL(f))
df['image_bokeh_static'] = df['image_bokeh']
df.drop('data', inplace=True, axis=1)

table_class = "display"
table_html = df[['image_mpl', 'image_PIL', 'image_bokeh_static', 'image_bokeh']].to_html(formatters={'image_mpl': image_formatter_mpl, 'image_PIL': image_formatter_PIL, 'image_bokeh_static':image_formatter_bokeh_static, 'image_bokeh':image_formatter_bokeh}, escape=False, classes=[table_class], index=False)

table_id = "example"
table_html_bs = BeautifulSoup(table_html).table
table_html_bs['id'] = table_id
style = parseStyle(table_html_bs.thead.tr['style'])
style['text-align'] = 'center'
table_html_bs.thead.tr['style'] = style.cssText


# Center all the things:
for x in table_html_bs.find_all('td'):
    x['align']='center'

header = '\n'.join(script_list)
print requests.post('http://localhost:5000/active', data={'data':str(table_html_bs), 'header':header, 'table_id':table_id})


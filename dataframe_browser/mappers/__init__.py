from inspect import getmembers, isfunction
import functools
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from dataframe_browser.utilities import one
import json

def image_formatter_mpl(image_base64):
    format_string = '<img style="height: {height}px; width: {width}px" src="data:image/png;base64,{img}">'
    return format_string.format(height=200, width=200, img=image_base64)

def image_base64_mpl(im):
    with BytesIO() as buffer:
        im.savefig(buffer, format='png', transparent=True)
        return base64.b64encode(buffer.getvalue()).decode()

class png(object):

    def __call__(self, func):

        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            # Do something before
            fig = func(*args, **kwargs)

            image_base64 = image_base64_mpl(fig)
            plt.close()

            return image_formatter_mpl(image_base64)
        return wrapper_decorator

import brain_observatory
import load_test
import widgets
import pandas as pd

mapper_library_dict = {}
for module in [brain_observatory, load_test, widgets]:
    for name, fcn in [o for o in getmembers(module) if isfunction(o[1])]:
        model_name_short = module.__name__.split('.')[-1]
        path = "{0}.{1}".format(model_name_short, name)
        mapper_library_dict[str(path)] = fcn

def squeeze(input_list):
    input_list = [x for x in input_list]
    set_val = set(tuple(input_list))
    if len(set_val) == 1:
        ret_val = one(set_val)
    else:
        ret_val = list(input_list)
    return ret_val

def to_df(series):

    df = pd.DataFrame(series.to_dict())

    df = df.describe(include='all')
    df.index.name = 'column'
    df = df.reset_index()

    table_class = "display"
    html = df.to_html(classes=[table_class], index=False, escape=False, justify='center').replace('\n', '')
    return html
    # return pd.DataFrame(series.to_dict())



for curr_fnc in [squeeze, to_df]:
    mapper_library_dict[str(curr_fnc.__name__)] = curr_fnc


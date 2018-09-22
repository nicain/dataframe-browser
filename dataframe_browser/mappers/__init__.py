from inspect import getmembers, isfunction
import functools
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from dataframe_browser.utilities import one

def image_formatter_mpl(image_base64):
    format_string = '<img style="height: {height}px; width: {width}px" src="data:image/png;base64,{img}">'
    return format_string.format(height=200, width=200, img=image_base64)

def image_base64_mpl(im):
    with BytesIO() as buffer:
        im.savefig(buffer, format='png', transparent=True)
        return base64.b64encode(buffer.getvalue()).decode()

def png(func):
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

mapper_library_dict = {}
for module in [brain_observatory, load_test]:
    mapper_library_dict[module.__name__] = dict(o for o in getmembers(module) if isfunction(o[1]))

def squeeze(input_list):
    set_val = set(tuple(input_list))
    if len(set_val) == 1:
        ret_val = one(set_val)
    else:
        ret_val = list(input_list)
    return ret_val

for curr_fnc in [squeeze]:
    mapper_library_dict[curr_fnc.__name__] = curr_fnc
import pandas as pd

from bokeh.layouts import row, widgetbox
from bokeh.models import Select, ColumnDataSource
from bokeh.plotting import figure
from bokeh.models.callbacks import CustomJS
from bokeh.embed import components
import json
from collections import Counter

from bokeh.palettes import Spectral
from bokeh.transform import factor_cmap

def xy_compare(series, width=200, size = 9, color = "#31AADE"):

    # Dict when lazy because of json encoding of arg
    if isinstance(series, dict):
        df = pd.DataFrame(series)
    else:
        df = pd.DataFrame(series.to_dict())

    columns = list(df.columns)
    initial_x_key = columns[0]
    initial_y_key = columns[1]

    df['x'] = df[initial_x_key]
    df['y'] = df[initial_y_key]

    source = ColumnDataSource(df)

    def create_figure():
        p = figure(plot_height=600, plot_width=800, tools='pan,box_zoom,hover,reset')
        p.circle(x='x', y='y', color=color, size=size, line_color="white", alpha=0.6, hover_color='white', hover_alpha=0.5, source=source)
        return p

    callback_x = CustomJS(args=dict(source=source), code="""
            
            var data = source.data;
            var f = cb_obj.value;

            var x = data['x']
            var x_src = data[f]
            for (var i = 0; i < x.length; i++) {
                x[i] = x_src[i]
            }
            source.change.emit();
            """)


    x = Select(title='X-Axis', value=initial_x_key, options=columns)
    x.js_on_change('value', callback_x)

    callback_y = CustomJS(args=dict(source=source), code="""
            
            var data = source.data;
            var f = cb_obj.value;

            var y = data['y']
            var y_src = data[f]
            for (var i = 0; i < y.length; i++) {
                y[i] = y_src[i]
            }
            source.change.emit();
            """)

    y = Select(title='Y-Axis', value=initial_y_key, options=columns)
    y.js_on_change('value', callback_y)

    controls = widgetbox([x, y], width=width)
    layout = row(controls, create_figure())

    script, div = components(layout)

    html = ''.join([script, div]).replace('\n', '')
    x = 'console.log("Bokeh: ERROR: Unable to run BokehJS code because BokehJS library is missing")'
    html = html.replace(x, x+';')

    return html

def bar_chart(series, height=350):

    s = pd.Series(series)

    cc = Counter(s)
    data_dict = {'key':[], 'count':[]}
    for key in cc:
        data_dict['key'].append(key)
        data_dict['count'].append(cc[key])
    
    df = pd.DataFrame(data_dict)
    df.sort_values(by='key', inplace=True)

    source = ColumnDataSource(df)

    if len(df) > 2:
        palette = Spectral[len(df)]
    else:
        palette = Spectral[3][:len(df)]


    p = figure(y_range=df['key'], plot_height=height, toolbar_location=None, title="Counts")
    p.hbar(y='key', right='count', height=0.9, source=source,
        line_color='white', fill_color=factor_cmap('key', palette=palette, factors=df['key']))

    # legend = Legend(items=[
    #                     ("sin(x)"   , [r0, r1]),
    #                     ("2*sin(x)" , [r2]),
    #                     ("3*sin(x)" , [r3, r4]),
    #                 ], location=(0, -30))

    p.ygrid.grid_line_color = None
    # p.x_range.start = 0
    # p.x_range.end = df['count'].max()
    # p.legend.orientation = "vertical"
    # p.legend.location = "top_center"

    # p.add_layout(p.legend, 'right')

    script, div = components(p)

    html = ''.join([script, div]).replace('\n', '')
    x = 'console.log("Bokeh: ERROR: Unable to run BokehJS code because BokehJS library is missing")'
    html = html.replace(x, x+';')

    return html

def series_categorical(series, height=350):
    
    new_series = {}
    for key, val in series.items():
        new_series[int(key)] = val


    s = pd.Series(new_series)

    if len(s.unique()) > 2:
        palette = Spectral[len(s.unique())]
    else:
        palette = Spectral[3][:len(s.unique())]

    val_color_dict = {}
    for ii, key in enumerate(sorted(s.unique())):
        val_color_dict[key] = palette[ii]

    data_dict = {'x':[], 'y':[], 'width':[], 'height':[], 'color':[], 'key':[]}
    for ii, key in enumerate(s):
        data_dict['x'].append(.5+ii)
        data_dict['y'].append(.5)
        data_dict['width'].append(1)
        data_dict['height'].append(1)
        data_dict['color'].append(val_color_dict[key])
        data_dict['key'].append(key)
    
    source = pd.DataFrame(data_dict)
    p = figure(y_range=[0,1], plot_height=height, tooltips=[('key', '@key')],tools='hover')
    p.rect(source=source, x='x', y='y', width='width', height='height', color='color')



    # source = ColumnDataSource(df)





    
    # # p.hbar(y='key', right='count', height=0.9, source=source,
    # #     line_color='white', fill_color=factor_cmap('key', palette=palette, factors=df['key']))
    # p.rect(x=[.5], y=[.5], width=[1], height=[1], color="#74ADD1")

    # legend = Legend(items=[
    #                     ("sin(x)"   , [r0, r1]),
    #                     ("2*sin(x)" , [r2]),
    #                     ("3*sin(x)" , [r3, r4]),
    #                 ], location=(0, -30))

    p.ygrid.grid_line_color = None
    p.xgrid.grid_line_color = None
    # p.x_range.start = 0
    # p.x_range.end = df['count'].max()
    # p.legend.orientation = "vertical"
    # p.legend.location = "top_center"

    # p.add_layout(p.legend, 'right')

    script, div = components(p)

    html = ''.join([script, div]).replace('\n', '')
    x = 'console.log("Bokeh: ERROR: Unable to run BokehJS code because BokehJS library is missing")'
    html = html.replace(x, x+';')

    return html

if __name__ == "__main__":
    
    import pyperclip
    from bokeh.sampledata.autompg import autompg_clean as df

    df = pd.DataFrame({'stage_name':['1_AutoRewards','1_AutoRewards','static_full_field_gratings']})
    html = bar_chart(df)

    # pyperclip.copy(html)




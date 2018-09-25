import pandas as pd

from bokeh.layouts import row, widgetbox
from bokeh.models import Select, ColumnDataSource
from bokeh.plotting import figure
from bokeh.models.callbacks import CustomJS
from bokeh.embed import components
import json

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

if __name__ == "__main__":
    
    import pyperclip
    from bokeh.sampledata.autompg import autompg_clean as df

    df = pd.DataFrame({'A':[1,2,3,4], 'B':[float('nan'),6,1,2], 'C':[0,1,6,2]})
    html = xy_compare(df)

    pyperclip.copy(html)




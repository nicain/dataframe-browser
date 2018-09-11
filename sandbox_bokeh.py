from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html, components
from bokeh.io import export_png
import base64
from io import BytesIO

plot = figure()
plot.circle([1,2], [3,4])

html = file_html(plot, CDN, "my plot")

script, div = components(plot)

# print html
# print script, div

with BytesIO() as buffer:
    export_png(plot, buffer)
    base64.b64encode(buffer.getvalue()).decode()

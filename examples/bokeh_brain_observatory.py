from dataframe_browser.client import Cursor

c = Cursor()

c.open(filename='/home/nicholasc/projects/dataframe-browser/data/cell_specimens.p')
c.query('area in ["VISpm", "VISl"]')
c.keep(['area', 'dsi_dg', 'osi_dg', 'g_dsi_dg',])
c.groupfold('area')

c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='dataframe_browser.mappers.widgets.xy_compare', new_column='bokeh', lazy=False)
c.reload()
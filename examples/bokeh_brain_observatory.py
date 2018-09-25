from dataframe_browser.client import Cursor

c = Cursor()

c.open(filename='/home/nicholasc/projects/dataframe-browser/data/cell_specimens.p')
c.query('area in ["VISpm", "VISl", "VISal"]')
c.keep(['area', 'dsi_dg', 'osi_dg', 'g_dsi_dg',])
c.groupfold('area')

c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='dataframe_browser.mappers.widgets.xy_compare', new_column='bokeh', lazy=True, axis=1)
# c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='to_df', new_column='df', lazy=False, drop=True)
# c.reload()
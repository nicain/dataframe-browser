from dataframe_browser.client import Cursor

c = Cursor()

c.open(filename='/home/nicholasc/projects/dataframe-browser/data/cell_specimens.p')
c.query('area in ["VISpm", "VISl", "VISal"]')
c.keep(['area', 'dsi_dg', 'osi_dg', 'g_dsi_dg',])
c.fold('area')

c.apply(columns=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='widgets.xy_compare', new_column='bokeh', lazy=True)
# c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='to_df', new_column='df', lazy=False, drop=True)
# c.reload()
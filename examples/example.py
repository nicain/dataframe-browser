from dataframe_browser.client import Cursor

c = Cursor()

c.open(filename='/home/nicholasc/projects/dataframe-browser/data/example.csv')
# c.query('area in ["VISpm", "VISl", "VISal"]')
# c.keep(['area', 'dsi_dg', 'osi_dg', 'g_dsi_dg',])
c.groupby('a')
c.drop(frames=[0])
c.back()
c.reload()

# c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='dataframe_browser.mappers.widgets.xy_compare', new_column='bokeh', lazy=False)

# c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='to_df', new_column='df', lazy=False, drop=True)
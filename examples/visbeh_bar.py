from dataframe_browser.client import Cursor

c = Cursor()

c.open(filename='/home/nicholasc/projects/dataframe-browser/data/visbeh.csv')
c.fold(['driver1_name', 'LabTracks_ID'])

# c.apply(columns=['stage_name'], mapper='widgets.bar_chart', new_column='bokeh', lazy=True).reload()
c.apply(columns=['stage_name'], mapper='widgets.series_categorical', new_column='bokeh', lazy=True).reload()


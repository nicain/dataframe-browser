from dataframe_browser.client import Cursor
import pgpasslib
import sqlalchemy
import sqlparse

import allensdk.internal.core.lims_utilities as lu

c = Cursor()


# filename = '/home/nicholasc/projects/allensdk_internal/allensdk/internal/api/queries/pre_release_sql/processing_query.sql'
filename1 = '/home/nicholasc/projects/allensdk_internal/allensdk/internal/api/queries/pre_release_sql/container_pre_release_query.sql'
filename2 = '/home/nicholasc/projects/allensdk_internal/allensdk/internal/api/queries/pre_release_sql/experiment_pre_release_query.sql'

# c.read(uri='postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader')), 
#        filename=[filename1, filename2])

c.read(uri='postgresql://limsreader@limsdb2:5432/lims2',
       password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader'), 
       filename=[filename1, filename2])


# c.open(filename='/home/nicholasc/projects/dataframe-browser/data/example.csv')
# # c.query('a > 1')
# # c.keep(['area', 'dsi_dg', 'osi_dg', 'g_dsi_dg',])
# c.groupby('a')
# c.bookmark(name='example')
# c.drop(frames=[0])
# c.back()
# c.reload()

# c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='dataframe_browser.mappers.widgets.xy_compare', new_column='bokeh', lazy=False)

# c.apply(column=['dsi_dg', 'g_dsi_dg', 'osi_dg'], mapper='to_df', new_column='df', lazy=False, drop=True)
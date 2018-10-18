from dataframe_browser.client import Cursor
import pgpasslib
import sqlalchemy
import sqlparse

import allensdk.internal.core.lims_utilities as lu

c = Cursor()


filename1 = '/home/nicholasc/projects/allensdk_internal/allensdk/internal/api/queries/pre_release_sql/processing_query.sql'
filename2 = '/home/nicholasc/projects/allensdk_internal/allensdk/internal/api/queries/pre_release_sql/container_pre_release_query.sql'
filename3 = '/home/nicholasc/projects/allensdk_internal/allensdk/internal/api/queries/pre_release_sql/experiment_pre_release_query.sql'

c.read(uri='postgresql://limsreader@limsdb2:5432/lims2',
       password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader'), 
       filename=[filename1, filename2, filename3])

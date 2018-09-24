from dataframe_browser.client import Cursor
import pgpasslib

c = Cursor()

c.read(uri='postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader')), 
       query='''SELECT wkfnwb.storage_directory || wkfnwb.filename AS nwb_file, oe.experiment_container_id AS experiment_container_id, oe.ophys_session_id AS ophys_session_id
            FROM experiment_containers ec JOIN ophys_experiments oe ON oe.experiment_container_id=ec.id AND oe.workflow_state = 'passed'
            JOIN images mip ON mip.id=oe.maximum_intensity_projection_image_id
            JOIN well_known_files wkfnwb ON wkfnwb.attachable_id=oe.id JOIN well_known_file_types wkft ON wkft.id=wkfnwb.well_known_file_type_id AND wkft.name = 'NWBOphys'
            JOIN ophys_sessions os ON os.id=oe.ophys_session_id JOIN projects osp ON osp.id=os.project_id
            WHERE osp.code = 'C600' AND ec.workflow_state NOT IN ('failed')
            AND ec.workflow_state = 'published';''')

    # # dfb = DataFrameBrowser()
    # # dfb.read(query=query, uri='postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader')))

    # requests.post('http://localhost:5000/command', data={
    #     'command':'open',
    #     'filename':'/home/nicholasc/projects/dataframe-browser/tests/example.csv'
    #     })


    # requests.post('http://localhost:5000/command', data={
    #     'command':'read',
    #     'query':
    #     'uri':'postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader'))
    #     })


    # # dfb.apply(column='nwb_file', mapper='nwb_file_to_max_projection', mapper_library='dataframe_browser.mappers.brain_observatory', new_column='max_projection', lazy=True)
    # dfb = DataFrameBrowser()
    # dfb.read(query=query, uri='postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=password))
    # # dfb.apply(column='nwb_file', mapper='test_apply', mapper_library='dataframe_browser.mappers.load_test', new_column='test')
    # dfb.apply(column='nwb_file', mapper='nwb_file_to_dff_traces_heatmap', mapper_library='dataframe_browser.mappers.brain_observatory', new_column='max_projection', lazy=True)

    # # example_df_path = '/home/nicholasc/projects/dataframe-browser/tests/example.csv'
    # # example_df_path = '/home/nicholasc/projects/dataframe-browser/data/BOb_data.p'
    # # example2_df_path = '/home/nicholasc/projects/dataframe-browser/tests/example2.csv'
    # # dfb = DataFrameBrowser()
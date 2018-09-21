import requests
import pgpasslib
import json

requests.post('http://localhost:5000/command', json=json.dumps({
    'command':'open',
    # 'filename':'/home/nicholasc/projects/dataframe-browser/data/example2.csv',
    'filename':'/home/nicholasc/projects/dataframe-browser/data/cell_counting.csv',
    'reload':False
    }))

requests.post('http://localhost:5000/command', json=json.dumps({
    'command':'query',
    'query':'acronym=="root"',
    'reload':True
    }))

# requests.post('http://localhost:5000/command', json=json.dumps({
#     'command':'groupby',
#     'by':['Sex', 'creline'],
#     'reload':True
#     }))


# requests.post('http://localhost:5000/command', data={
#     'command':'read',
#     'query':'''SELECT wkfnwb.storage_directory || wkfnwb.filename AS nwb_file, oe.experiment_container_id AS experiment_container_id, oe.ophys_session_id AS ophys_session_id
#         FROM experiment_containers ec JOIN ophys_experiments oe ON oe.experiment_container_id=ec.id AND oe.workflow_state = 'passed'
#         JOIN images mip ON mip.id=oe.maximum_intensity_projection_image_id
#         JOIN well_known_files wkfnwb ON wkfnwb.attachable_id=oe.id JOIN well_known_file_types wkft ON wkft.id=wkfnwb.well_known_file_type_id AND wkft.name = 'NWBOphys'
#         JOIN ophys_sessions os ON os.id=oe.ophys_session_id JOIN projects osp ON osp.id=os.project_id
#         WHERE osp.code = 'C600' AND ec.workflow_state NOT IN ('failed')
#         AND ec.workflow_state = 'published';''',
#     'uri':'postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader'))
#     })
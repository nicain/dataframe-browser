from dataframe_browser.client import Cursor
import pgpasslib

c = Cursor(session_uuid='example')

c.read(uri='postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader')), 
       query='''SELECT wkfnwb.storage_directory || wkfnwb.filename AS nwb_file, oe.experiment_container_id AS experiment_container_id, oe.ophys_session_id AS ophys_session_id
            FROM experiment_containers ec JOIN ophys_experiments oe ON oe.experiment_container_id=ec.id AND oe.workflow_state = 'passed'
            JOIN images mip ON mip.id=oe.maximum_intensity_projection_image_id
            JOIN well_known_files wkfnwb ON wkfnwb.attachable_id=oe.id JOIN well_known_file_types wkft ON wkft.id=wkfnwb.well_known_file_type_id AND wkft.name = 'NWBOphys'
            JOIN ophys_sessions os ON os.id=oe.ophys_session_id JOIN projects osp ON osp.id=os.project_id
            WHERE osp.code = 'C600' AND ec.workflow_state NOT IN ('failed')
            AND ec.workflow_state = 'published';''')

# c.apply(columns='nwb_file', mapper='brain_observatory.nwb_file_to_max_projection', new_column='max_projection', lazy=True, drop=True)

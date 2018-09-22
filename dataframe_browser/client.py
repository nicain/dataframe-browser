import requests
import pgpasslib
import json


class Cursor(object):

    def __init__(self, port=5000, hostname='localhost'):

        self.port = port
        self.hostname = hostname
    
    @property
    def command(self):
        return 'http://{hostname}:{port}/command'.format(hostname=self.hostname, port=self.port)

    def run(self, **kwargs):
        result = requests.post(self.command, json=json.dumps(kwargs))
        if result.status_code != 200:
            result.raise_for_status()
        return self

    def open(self, filename=None, reload=False):
        return self.run(command='open', filename=filename, reload=reload)

    def query(self, query=None, reload=False):
        return self.run(command='query', query=query, reload=reload)

    def groupby(self, by=None, reload=False):
        return self.run(command='groupby', by=by, reload=reload)

    def groupfold(self, by=None, reload=False):
        return self.run(command='groupfold', by=by, reload=reload)

    def drop(self, columns=None, reload=False):
        return self.run(command='drop', columns=columns, reload=reload)

    def keep(self, columns=None, reload=False):
        return self.run(command='keep', columns=columns, reload=reload)

    def concat(self, how='vertical', reload=False):
        return self.run(command='concat', how=how, reload=reload)

    @property
    def help(self):
        print 'HALP' # TODO: rework CLI argparse to print meaningful help




if __name__ == "__main__":

    c = Cursor()

    c.open(filename='/home/nicholasc/projects/dataframe-browser/data/cell_counting.csv').query('acronym=="root"').groupby('Sex').concat()

# requests.post('http://localhost:5000/command', json=json.dumps({
#     'command':'query',
#     'query':'acronym=="root"',
#     'reload':False
#     }))

# requests.post('http://localhost:5000/command', json=json.dumps({
#     'command':'groupby',
#     'by':['creline'],
#     'reload':True
#     }))


# requests.post('http://localhost:5000/command', json=json.dumps({
#     'command':'groupfold',
#     'by':['Sex'],
#     'reload':True
#     }))



# requests.post('http://localhost:5000/command', json=json.dumps({
#     'command':'read',
#     'query':'''SELECT wkfnwb.storage_directory || wkfnwb.filename AS nwb_file, oe.experiment_container_id AS experiment_container_id, oe.ophys_session_id AS ophys_session_id
#         FROM experiment_containers ec JOIN ophys_experiments oe ON oe.experiment_container_id=ec.id AND oe.workflow_state = 'passed'
#         JOIN images mip ON mip.id=oe.maximum_intensity_projection_image_id
#         JOIN well_known_files wkfnwb ON wkfnwb.attachable_id=oe.id JOIN well_known_file_types wkft ON wkft.id=wkfnwb.well_known_file_type_id AND wkft.name = 'NWBOphys'
#         JOIN ophys_sessions os ON os.id=oe.ophys_session_id JOIN projects osp ON osp.id=os.project_id
#         WHERE osp.code = 'C600' AND ec.workflow_state NOT IN ('failed')
#         AND ec.workflow_state = 'published';''',
#     'uri':'postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader'))
#     }))
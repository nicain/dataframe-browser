import os

from utilities import create_class_logger
from model import Model
from view import FlaskViewServer as FlaskView
from controller import TextController
from customexceptions import BookmarkAlreadyExists

class DataFrameBrowser(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        model_kwargs = kwargs.get('model_kwargs', {})
        self.model = Model(app=self, **model_kwargs)
        
        view_kwargs = kwargs.get('view_kwargs', {})
        self.view = kwargs.get('view_class', FlaskView)(app=self, **view_kwargs)

        controller_kwargs = kwargs.get('controller_kwargs', {})
        self.controller = kwargs.get('controller_class', TextController)(app=self, **controller_kwargs)


    def open(self, filename=None, bookmark=None):

        self.controller.open_node_from_file(filename=filename, bookmark=bookmark)

    def info(self, bookmark=None):
    
        if bookmark is None:
            self.view.display_branch_info()
            self.view.display_tree()
            self.view.display_node_info(self.active)
        else:
            node = self.model.get_node_by_name(bookmark)
            if node is not None:
                self.view.display_node_info(node)

    def select(self, bookmark=None, key=None, quiet=True):

        if bookmark is not None:
            node = self.model.get_node_by_name(bookmark)
            self.model.set_active(node, name=bookmark, key=key)
        
        if quiet is False:
            self.info()

    def unbookmark(self, *bookmarks):

        for bookmark in bookmarks:
            self.controller.unbookmark(bookmark)

    def append(self, other_bookmark, new_bookmark=None, force=False):
        if other_bookmark == new_bookmark and force == False:
            raise BookmarkAlreadyExists('Force not requested')

        nodeframe_list = self.active.node_frames + self.model.get_node_by_name(other_bookmark).node_frames
        
        new_node = self.controller.create_node(nodeframe_list, self.active, name=new_bookmark, force=force)
        self.model.set_active(new_node)

    def bookmark(self, name):
        self.model.active.rename(name)
        self.view.display_active()

    def back(self):
        self.model.set_active(self.model.active.parent)
        self.view.display_active()

    def merge(self, on=None, how='inner'):

        new_node = self.active.merge(on=on, how=how)
        self.model.set_active(new_node)
        self.view.display_active()

    def query(self, query=None):
    
        new_node_list = self.active.query(query=query)
        self.model.set_active(new_node_list[0])
        self.view.display_active()

    def read(self, query=None, uri=None):
        
        self.controller.read_node_from_uri_query(query=query, uri=uri)

    def apply(self, column=None, mapper=None, new_column=None, lazy=False):

        new_node_list = self.active.apply(column=column, mapper=mapper, new_column=new_column, lazy=lazy)
        self.model.set_active(new_node_list[0])
        self.view.display_active()



    @property
    def active(self):
        return self.model.active

    def groupby(self, by=None):
        new_node_list = self.active.groupby(by=by)
        self.model.set_active(new_node_list[0])

    def groupfold(self, by=None):
        new_node = self.active.groupfold(by=by)
        self.model.set_active(new_node)

    def drop(self, columns=None):
        new_node = self.active.drop(columns=columns)
        self.model.set_active(new_node)

    def keep(self, columns=None):
        new_node = self.active.keep(columns=columns)
        self.model.set_active(new_node)

    def concat(self, how='vertical'):
        new_node = self.active.concat(how=how)
        self.model.set_active(new_node)


if __name__ == "__main__":    
    
    from dataframe_browser.dataframebrowser import DataFrameBrowser
    import pgpasslib



    # dfb = DataFrameBrowser()
    # dfb.read(query=query, uri='postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader')))

    requests.post('http://localhost:5000/command', data={
        'command':'open',
        'filename':'/home/nicholasc/projects/dataframe-browser/tests/example.csv'
        })


    requests.post('http://localhost:5000/command', data={
        'command':'read',
        'query':'''SELECT wkfnwb.storage_directory || wkfnwb.filename AS nwb_file, oe.experiment_container_id AS experiment_container_id, oe.ophys_session_id AS ophys_session_id
            FROM experiment_containers ec JOIN ophys_experiments oe ON oe.experiment_container_id=ec.id AND oe.workflow_state = 'passed'
            JOIN images mip ON mip.id=oe.maximum_intensity_projection_image_id
            JOIN well_known_files wkfnwb ON wkfnwb.attachable_id=oe.id JOIN well_known_file_types wkft ON wkft.id=wkfnwb.well_known_file_type_id AND wkft.name = 'NWBOphys'
            JOIN ophys_sessions os ON os.id=oe.ophys_session_id JOIN projects osp ON osp.id=os.project_id
            WHERE osp.code = 'C600' AND ec.workflow_state NOT IN ('failed')
            AND ec.workflow_state = 'published';''',
        'uri':'postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=pgpasslib.getpass('limsdb2', 5432, 'lims2', 'limsreader'))
        })


    # dfb.apply(column='nwb_file', mapper='nwb_file_to_max_projection', mapper_library='dataframe_browser.mappers.brain_observatory', new_column='max_projection', lazy=True)
    dfb = DataFrameBrowser()
    dfb.read(query=query, uri='postgresql://limsreader:{password}@limsdb2:5432/lims2'.format(password=password))
    # dfb.apply(column='nwb_file', mapper='test_apply', mapper_library='dataframe_browser.mappers.load_test', new_column='test')
    dfb.apply(column='nwb_file', mapper='nwb_file_to_dff_traces_heatmap', mapper_library='dataframe_browser.mappers.brain_observatory', new_column='max_projection', lazy=True)

    # example_df_path = '/home/nicholasc/projects/dataframe-browser/tests/example.csv'
    # example_df_path = '/home/nicholasc/projects/dataframe-browser/data/BOb_data.p'
    # example2_df_path = '/home/nicholasc/projects/dataframe-browser/tests/example2.csv'
    # dfb = DataFrameBrowser()
    # dfb.open(filename=example_df_path, bookmark='A')
    # dfb.open(filename=example2_df_path, bookmark='B')
    # dfb.append('A', force=True, new_bookmark='C')
    # dfb.groupby('c')
    # dfb.unbookmark('C')
    # dfb.select('C[0]', 'a')
    # dfb.append('A')
    # dfb.bookmark('new')
    # dfb.merge(['a', 'c'], how='right')
    # dfb.info()
    # dfb.query('a==2')


from utilities import create_class_logger, fn_timer, load_file
import os
import pandas as pd
from customexceptions import UnrecognizedFileTypeException
from nodeframe import NodeFrame
from node import Node

class TextController(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        self.app = kwargs['app']


    @fn_timer        
    def open_node_from_file(self, filename, bookmark=None, force=False, **kwargs):

        if not os.path.exists(filename):
            self.app.view.display_message('Source not found: {0}\n'.format(filename), type='error')
            return

        try:
            df, load_time = load_file(filename)
        except UnrecognizedFileTypeException:
                    
            self.app.view.display_message('File extension not in (csv/p): {0}\n'.format(filename), type='error')
            raise NotImplementedError

        node_frame = NodeFrame(df=df, load_time=load_time, metadata={'filename':filename})
        node = self.create_node((node_frame,), parent=self.app.model.root, name=bookmark, force=force)
        self.app.model.set_active(node)


    def create_node(self, nodeframe_list, parent, name=None, force=False):

        # TODO: consolidate use of root to top level
        assert name != 'root'

        if name in self.app.model.bookmarks:

            if force == True:
                node = Node(nodeframe_list, parent=parent, name=name)
            else: 
                raise NotImplementedError
        
        else:
            node = Node(nodeframe_list, parent=parent, name=name)

        return node

    def unbookmark(self, bookmark):
    
        node_to_unbookmark = self.app.model.get_node_by_name(bookmark)
        node_to_unbookmark.rename(None)
        if node_to_unbookmark is self.app.active:
            self.app.view.display_node(node_to_unbookmark)

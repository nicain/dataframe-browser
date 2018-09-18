# import pandas as pd
# import networkx as nx
# import sys
# import logging
# from collections import OrderedDict
# import json
# import traceback
import os
# import io
# import requests
# import warnings
# import readline
# import shlex
# import argcomplete
# import re
# import atexit
# import itertools
# from future.utils import raise_from


from utilities import create_class_logger
from model import Model
from view import FlaskView
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

    def merge(self, on=None, how='inner'):

        new_node = self.active.merge(on=on, how=how)
        self.model.set_active(new_node)


    @property
    def active(self):
        return self.model.active

    def groupby(self, by=None):

        new_node_list = self.active.groupby(by=by)
        self.model.set_active(new_node_list[0])


if __name__ == "__main__":    
    
    from dataframe_browser.dataframebrowser import DataFrameBrowser
    example_df_path = '/home/nicholasc/projects/dataframe-browser/tests/example.csv'
    example2_df_path = '/home/nicholasc/projects/dataframe-browser/tests/example2.csv'
    dfb = DataFrameBrowser()
    dfb.open(filename=example_df_path, bookmark='A')
    dfb.open(filename=example2_df_path, bookmark='B')
    dfb.append('A', force=True, new_bookmark='C')
    dfb.groupby('c')
    dfb.unbookmark('C')
    dfb.select('C[0]', 'a')
    dfb.append('A')
    dfb.bookmark('new')
    dfb.merge('a', how='right')


import pandas as pd
import networkx as nx
import sys
import logging
from collections import OrderedDict
import json
import os
import io
import warnings
import shlex

DEFAULT_PROMPT = 'df> '
COMMAND_SEP_CHAR = ';'
UNRECOGNIZED_INPUT_FORMAT = 'Unrecognized input: "{0}"\n'
UUID_LENGTH = 32

from dataframe_browser.exceptions import CommandParsingException, BookmarkAlreadyExists
from dataframe_browser.parsing import ArgumentParser, HelpAction
from utilities import generate_uuid

# import argparse
OPEN = 'open'
COMMAND = 'cmd'
main_parser = ArgumentParser(description='main_parser description', prog=DEFAULT_PROMPT.strip(), add_help=False)
main_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')
main_parser.add_argument(COMMAND, choices=[OPEN], nargs='?')

open_parser = ArgumentParser(description='open description', prog=DEFAULT_PROMPT.strip(), add_help=False)
open_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')
open_parser.add_argument("-f", nargs='*', default=[])

command_parser_dict = {OPEN:open_parser}

# subparsers = main_parser.add_subparsers(description='subparser descritption', help='subparsers help str', dest='cmd')
# a_parser = subparsers.add_parser("open", add_help=False)
# a_parser.add_argument("something", nargs='?')
# a_parser.add_argument('--help', action=HelpAction, help='OTHER HELP')
working_example = 'open -f '



# a_parser = subparsers.add_parser("A")
# b_parser = subparsers.add_parser("B")

# a_parser.add_argument("something", )







def create_class_logger(cls, **kwargs):

    level = kwargs.get('level', logging.INFO)
    name = kwargs.get('name', cls.__name__)
    handler = kwargs.get('handler', logging.StreamHandler())
    formatter = kwargs.get('formatter', logging.Formatter(logging.BASIC_FORMAT))

    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level) 

    return logger


class TextController(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']
        self.QUIT_VALS = kwargs.get('QUIT_VALS', ['exit()'])
        self.DEFAULT_PROMPT = kwargs.get('DEFAULT_PROMPT', DEFAULT_PROMPT)
        self.NEW_DF_NODE = kwargs.get('NEW_DF_NODE', 'o:')
        self.ADD_BOOKMARK = kwargs.get('ADD_BOOKMARK', 'b:')
        self.QUERY = kwargs.get('QUERY', 'q:')
        self.DISPLAY_ACTIVE_DF_INFO = kwargs.get('DISPLAY_ACTIVE_DF_INFO', ['i:', 'i'])
        self.LS = kwargs.get('LS', 'ls')
        self.sep = COMMAND_SEP_CHAR

        self.input_list = None

    def parse_single_command(self, command, parser=main_parser):
        split_command = shlex.split(command)
        try:
            arg_res, rem = parser.parse_known_args(split_command)
            arg_dict = vars(arg_res)

            if 'help' in arg_dict and arg_dict['help'] == True:

                if arg_dict[COMMAND] is not None:
                    # Unusual corner case:
                    raise CommandParsingException(command, parser)

                # recognized request for help:
                self.logger.info(json.dumps({command:arg_dict}))
                return (command, arg_dict)

            else:
                curr_command = arg_dict[COMMAND]
                if curr_command in command_parser_dict:
                    new_command = [x for x in split_command if x != curr_command]
                    arg_dict = {curr_command:vars(command_parser_dict[curr_command].parse_args(new_command))}
                    self.logger.info(json.dumps({command:arg_dict}))
                    return (command, arg_dict)

                else:
                    raise CommandParsingException(command, parser)

            self.logger.info(json.dumps({command:arg_dict}))
            return (command, arg_dict)
        except CommandParsingException as e:

            # Unrecognized command
            print 'Parsing Error: {0}'.format(str(e))
            e.parser.print_help(sys.stderr)
            self.logger.info(json.dumps({command:'Unrecognized'}))
            return (command,)

    def parse_text_clean_split(self, text_input, sep=None):
        if sep is None: sep = self.sep
        text_input_list = [input.strip() for input in text_input.split(sep)]
        if len(text_input_list) > 1:
            text_input_list = [x for x in text_input_list if len(x)>0]

        return [self.parse_single_command(single_command) for single_command in text_input_list]

    def parse_input_recursive(self, input):
        if isinstance(input, (str,)):
            input_list = self.parse_text_clean_split(input)

        elif isinstance(input, (list, tuple)):
            input_list = []
            for x in input:
                input_list += self.parse_input_recursive(x)
            return input_list
        
        else:
            raise NotImplementedError('Input not parsed: {0}'.format(input))

        return [self.input_mapper(input) for input in input_list]

    def initialize_input(self, input=''):

        self.input_list = self.parse_input_recursive(input)


    def input_mapper(self, input):

        # No-op for this command; either requested help, or unrecognized
        if len(input) == 1 or (len(input) == 1 and input[1]['help'] == True):
            return (lambda : None, {})

        if input in self.QUIT_VALS: 
            fcn, kwargs = self.quit, {}
        else:
            raise NotImplementedError(str(input))
        # elif input[:2] == self.NEW_DF_NODE: 
        #     fcn, kwargs = self.load_new_df, {'source': input[2:].strip()}
        # elif input[:2] == self.ADD_BOOKMARK: 
        #     fcn, kwargs = self.add_bookmark, {'input_value': input[2:].strip()}
        # elif len(input) == 0: 
        #     fcn, kwargs = self.app.view.display_active, {}
        # elif input[:2] == self.QUERY: 
        #     fcn, kwargs = self.query, {'query': input[2:].strip()}
        # elif input in self.DISPLAY_ACTIVE_DF_INFO: 
        #     fcn, kwargs = self.display_active_df_info, {}
        # elif input in self.LS: 
        #     fcn, kwargs = self.ls, {}
        # else: 
        #     fcn, kwargs = self.unrecognized, {'input_value':input.strip()}

        # self.logger.info(json.dumps({fcn.__name__:kwargs}))

        # return fcn, kwargs

    def ls(self, **kwargs):
        pass

    def display_active_df_info(self, **kwargs):
        buffer = io.StringIO()
        self.app.model.active.info(buf=buffer, **kwargs)
        self.app.view.display_active_df_info(buffer)


    def query(self, **kwargs):

        query_string = kwargs['query']
        parent_node = self.app.model.active_node
        result_df = self.app.model.active.query(query_string)
        active_node = self.add_node(result_df)
        self.add_edge(parent_node, active_node, query=query_string)

    def add_edge(self, source, target, **kwargs):
        self.app.model.graph.add_edge(source, target, **kwargs)


    def add_bookmark(self, **kwargs):
        
        bookmark_name = kwargs['input_value']
        try:
            self.app.model.add_bookmark(bookmark_name, self.app.model.active_node)
        except BookmarkAlreadyExists as e:
            self.app.view.display_message(str(e), type='error')

        self.app.view.display_message('Bookmark added: {0}'.format(bookmark_name), type='info')

            
    def load_new_df(self, **kwargs):

        file_name = kwargs['source']

        if not os.path.exists(file_name):
            print 'Source not found: {0}\n'.format(file_name)
            return

        if file_name[-4:] == '.csv':
            df = pd.read_csv(file_name)
        elif file_name[-2:] == '.p':
            df = pd.read_pickle(file_name)
        else:
            print 'File extension not in (csv/p): {0}\n'.format(file_name)
            return

        self.add_node(df, source=file_name)
        
    def add_node(self, df, **kwargs):

        uuid = generate_uuid(UUID_LENGTH)
        self.app.model.graph.add_node(uuid, df=df, **kwargs)
        self.set_active(uuid)
        self.app.view.display_active()
        return uuid

    def set_active(self, uuid):
        self.app.model.active_node = uuid
        

    def quit(self, **kwargs): 
        sys.exit(0)


    def get_input(self, prompt=None):
        if prompt is None: prompt = self.DEFAULT_PROMPT
        try:
            raw_input_string = raw_input(prompt)
        except EOFError:
            sys.exit(0)
        return raw_input_string


    def update(self, prompt=None):
        if prompt is None: prompt = self.DEFAULT_PROMPT
        
        if len(self.input_list) == 0:
            raw_input_string = self.get_input(prompt=prompt)
            self.input_list += self.parse_input_recursive(raw_input_string)


class TextControllerNonInteractive(TextController):

    def update(self, **kwargs):
        pass

class Model(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        
        self.app = kwargs['app']
        self.graph = nx.DiGraph()
        self._bookmarks = {}
        self.active_node = None

    @property
    def bookmarks(self):
        self.prune_bookmarks()
        return self._bookmarks

    def prune_bookmarks(self):

        drop_set = set(self.graph.nodes())-set(self._bookmarks.values())
        for key, val in self._bookmarks.items():
            if val in drop_set:
                del self._bookmarks[key]

    def add_bookmark(self, name, val):

        if name in self._bookmarks:
            raise BookmarkAlreadyExists('Bookmark name {0} already in use'.format(name))
        else:
            self._bookmarks[name] = val


    @property
    def active(self):
        return self.graph.nodes[self.active_node]['df']

class ConsoleView(object):

    def __init__(self, **kwargs):
        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']

    def display_active(self, **kwargs):
        self.display_message(self.app.model.active, **kwargs)

    def display_active_df_info(self, buffer):
        self.display_message(buffer.getvalue())

    def display_message(self, msg, type=None):
        print msg

class DataFrameBrowser(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        model_kwargs = kwargs.get('model_kwargs', {})
        self.model = Model(app=self, **model_kwargs)
        
        view_kwargs = kwargs.get('view_kwargs', {})
        self.view = kwargs.get('view_class', ConsoleView)(app=self, **view_kwargs)

        controller_kwargs = kwargs.get('controller_kwargs', {})
        self.controller = kwargs.get('controller_class', TextController)(app=self, **controller_kwargs)


    def run(self, input=['']):

        self.controller.initialize_input(input)
        while len(self.controller.input_list) > 0:

            curr_input, curr_input_kwargs = self.controller.input_list.pop(0)
            curr_input(**curr_input_kwargs)            
            self.controller.update()

        return self


if __name__ == "__main__":    
    df_file_name = os.path.join(os.path.dirname(__file__),'..', 'tests', 'example.csv')

    def get_dfbd():
        dfb = DataFrameBrowser(logging_settings={'handler':logging.StreamHandler()})
        return {'dataframe_browser':dfb}

    

    dataframe_browser_fixture = get_dfbd()
    dataframe_browser_fixture['dataframe_browser'].run(input=working_example)
    # try:
    #     dataframe_browser_fixture['dataframe_browser'].run(input=['o: {0}; b: TEST'.format(df_file_name), 'i:;ls;exit()'])
    # except SystemExit:
    #     pass
    # print dataframe_browser_fixture['dataframe_browser'].model.bookmarks

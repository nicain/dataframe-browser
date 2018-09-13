import pandas as pd
import networkx as nx
import sys
import logging
from collections import OrderedDict
import json
import os
import io
import requests
import warnings
import readline
import shlex
import argcomplete
import atexit
import itertools
from future.utils import raise_from


DEFAULT_PROMPT = 'df> '
COMMAND_SEP_CHAR = ';'
UNRECOGNIZED_INPUT_FORMAT = 'Unrecognized input: "{0}"\n'
UUID_LENGTH = 32

from dataframe_browser.exceptions import CommandParsingException, BookmarkAlreadyExists
from dataframe_browser.parsing import ArgumentParser, HelpAction
from utilities import generate_uuid

OPEN = 'open'
QUERY = 'query'
BOOKMARK = 'bookmark'
COMMAND = 'cmd'
main_parser = ArgumentParser(description='main_parser description', prog=DEFAULT_PROMPT.strip(), add_help=False)
main_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')

open_parser = ArgumentParser(description='open description', prog=DEFAULT_PROMPT.strip(), add_help=False)
open_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')
open_parser.add_argument("-f", "--file", nargs='+', dest='file_list', type=str, default=[])
open_parser.add_argument("--uri", nargs=1, dest='uri', type=str)
open_parser.add_argument("-q", "--quiet", dest='quiet', action='store_true')
open_parser.add_argument("--table", nargs='+', dest='table_list', type=str, default=[])

query_parser = ArgumentParser(description='query description', prog=DEFAULT_PROMPT.strip(), add_help=False)
query_parser.add_argument(nargs='*', dest='remainder_list', type=str)

bookmark_parser = ArgumentParser(description='Bookmark description', prog=DEFAULT_PROMPT.strip(), add_help=False)
bookmark_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')
bookmark_parser.add_argument('name', nargs=1, type=str)
bookmark_parser.add_argument('-f', '--force', dest='force', action='store_true')
bookmark_parser.add_argument('--rm', dest='remove', action='store_true')

command_parser_dict = {OPEN:open_parser, QUERY:query_parser, BOOKMARK:bookmark_parser}
main_parser.add_argument(COMMAND, choices=command_parser_dict.keys(), nargs='?')

def one(x, exc_tp=TypeError):
    try:
        val, = x
        return val
    except TypeError as e:
        raise_from(exc_tp, e)

def get_argcompletion_matches(argcompletion_finder, text):
    tmp = []
    for ii in itertools.count():
        res = argcompletion_finder.rl_complete(text, ii)
        if res is None:
            break
        else:
            tmp.append(res)
    return tmp


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

class DataFrameNode(object):

    def __init__(self, df=None, metadata=None, name=None, load_time=None):

        # TODO?
        # https://www.kaggle.com/arjanso/reducing-dataframe-memory-size-by-65
        self.df = df
        self.metadata = metadata
        self._name = name

        self.load_time = load_time # TODO
    
    @property
    def memory_usage(self):
        return self.df.memory_usage(deep=True).sum()

    @property
    def table(self):
        return self.df

    def to_html(self, *args, **kwargs):
        return self.df.to_html(*args, **kwargs)

    def __str__(self):
        return str(self.df)
    
    @property
    def name(self):
        return self._name

    def set_name(self, new_name):
        self._name = new_name

    

class CompletionFinder(object):
    
    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        self.controller = kwargs['controller']
        self.main_parser = self.controller.main_parser
        self.subparser_dict = self.controller.subparser_dict

        self.completion_finder_dict = {key:argcomplete.CompletionFinder(val) for key, val in self.subparser_dict.items()}
        self.main_completion_finder = argcomplete.CompletionFinder(self.main_parser)

    def initialize(self, **kwargs):

        self.set_history_file(kwargs.get('histfile', None))

        readline.set_completer(self.completer)
        readline.set_completer_delims("")
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind('"\e[B": history-search-forward')
        readline.parse_and_bind('"\e[A": history-search-backward') # https://github.com/donnemartin/gitsome/blob/master/xonsh/readline_shell.py

    def set_history_file(self, histfile):

        if histfile is None:
            histfile = os.path.join(os.path.expanduser("~"), ".dataframe-browser", 'default.history')
        history_file_dir = os.path.dirname(histfile)

        try:
            readline.read_history_file(histfile)
            readline.set_history_length(1000) # default history len is -1 (infinite), which may grow unruly
        except IOError:
            pass

        if not os.path.isdir(history_file_dir):
            os.makedirs(history_file_dir)

        atexit.register(readline.write_history_file, histfile)
        del histfile


    
    def get_options(self, startswith_text):
        '''Build a list of options, by considering each '''
        
        main_commands = ['{0}'.format(x) for x in get_argcompletion_matches(self.main_completion_finder, '')]

        if len(startswith_text) == 0:
            return main_commands

        subparser_command_dict = {}
        for cmd, completion_finder in self.completion_finder_dict.items():
            if cmd == QUERY:
                pass
            else:
                tmp = startswith_text[len(cmd)+1:]
                subparser_command_dict[cmd] = ['{0} {1}'.format(cmd, x) for x in get_argcompletion_matches(completion_finder, tmp)]
        


        ## INSERT CUSTOM MODIFICATION HERE: (START)

        ## INSERT CUSTOM MODIFICATION HERE: (END)

        subparser_commands = []
        for command_list in subparser_command_dict.values():
            subparser_commands += command_list

        all_option_list = [i for i in ['help']+subparser_commands+main_commands if i.startswith(startswith_text)]
        return all_option_list

    def completer(self, startswith_text, state):

        options = self.get_options(startswith_text)
        if state < len(options):
            return options[state]
        else:
            return None


class TextController(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']
        self.QUIT_VALS = kwargs.get('QUIT_VALS', ['exit()'])
        self.DEFAULT_PROMPT = kwargs.get('DEFAULT_PROMPT', DEFAULT_PROMPT)

        self.sep = COMMAND_SEP_CHAR
        self.input_list = None

        self.subparser_dict = command_parser_dict
        self.main_parser = main_parser

        self.completion_finder = CompletionFinder(controller=self)
        self.completion_finder.initialize(histfile=kwargs.get('histfile', None))
        
        self.prompt = raw_input

    def input_mapper(self, input):
    
        # No-op for this command; either requested help, or unrecognized
        if len(input) == 1 or (len(input) == 2 and input[1].get('help', None) == True):
            return (lambda : None, {})

        if input in self.QUIT_VALS: 
            fcn, kwargs = self.quit, {}
        elif OPEN in input[1]:
            return self.open_command, input[1][OPEN]
        elif QUERY in input[1]:
            query = ' '.join(input[1][QUERY]['remainder_list'])
            return self.query_command, {'query':query}
        elif BOOKMARK in input[1]:
            return self.bookmark_command, input[1][BOOKMARK]


        else:
            raise NotImplementedError(input)

    def parse_single_command(self, command, parser=main_parser):
        split_command = shlex.split(command)
        if split_command in (['help'], ['?']): split_command = ['--help']
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
                if curr_command in self.subparser_dict:
                    new_command = [x for x in split_command if x != curr_command]
                    arg_dict = {curr_command:vars(self.subparser_dict[curr_command].parse_args(new_command))}
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

    def bookmark_command(self, **kwargs):

        name = one(kwargs.pop('name'))

        if kwargs['remove']:
            self.remove_bookmark(name=name)
        else:
            self.add_bookmark(name=name, force=kwargs['force'])

    def remove_bookmark(self, **kwargs):
        name=kwargs['name']
        node = one(self.app.model.get_nodes_by_name(name=name))
        node.set_name(None)
        self.logger.info(json.dumps({'REMOVE_BOOKMARK':kwargs}, indent=4))


    def open_command(self, **kwargs):

        quiet = kwargs.get('quiet', False)

        for file_name in kwargs.get('file_list', []):
            self.load_new_df_from_file(file_name=file_name, quiet=quiet)


        for table in kwargs.get('table_list', []):
            uri = kwargs['uri'][0]
            self.load_new_df_from_uri(table=table, uri=uri, quiet=quiet)
            

    def load_new_df_from_uri(self, **kwargs):
        uri = kwargs['uri']
        table = kwargs['table']
        quiet = kwargs.get('quiet', False)
        df = pd.read_sql_table(table, uri)
        self.add_dataframe(df, parent=None, quiet=quiet, metadata={'uri':uri, 'table':table})

    def display_active_df_info(self, **kwargs):
        buffer = io.StringIO()
        self.app.model.active.info(buf=buffer, **kwargs)
        self.app.view.display_active_df_info(buffer)


    def query_command(self, **kwargs):

        query_string = kwargs['query']
        parent_node = self.app.model.active
        result_df = parent_node.table.query(query_string)
        self.add_dataframe(result_df, parent=parent_node, metadata={'query':query_string})
        self.logger.info(json.dumps({'QUERY':kwargs}, indent=4))


    def add_bookmark(self, **kwargs):
        
        bookmark_name = kwargs['name']
        msg = 'Bookmark added: {0}'.format(bookmark_name)
        try:
            self.app.model.active.set_name(bookmark_name)
            self.app.view.display_message(msg, type='info')
            self.logger.info(json.dumps({'ADD_BOOKMARK':kwargs}, indent=4))
        except BookmarkAlreadyExists as e:

            if kwargs.get('force', False):
                self.app.model.remove_bookmark(bookmark_name)
                self.app.model.active.set_name(bookmark_name)
                self.app.view.display_message(msg, type='info')
                self.logger.info(json.dumps({'ADD_BOOKMARK':kwargs}, indent=4))
            else:
                self.app.view.display_message(str(e), type='error')
                self.logger.error(json.dumps({'ADD_BOOKMARK':kwargs}, indent=4))
            
    def load_new_df_from_file(self, **kwargs):

        file_name = kwargs['file_name']
        quiet = kwargs.get('quiet', False)

        if not os.path.exists(file_name):
            self.app.view.display_message('Source not found: {0}\n'.format(file_name), type='error')
            return

        if file_name[-4:] == '.csv':
            df = pd.read_csv(file_name)
        elif file_name[-2:] == '.p':
            df = pd.read_pickle(file_name)
        else:
            self.app.view.display_message('File extension not in (csv/p): {0}\n'.format(file_name), type='error')
            return

        self.add_dataframe(df, parent=None, quiet=quiet, metadata={'file_name':file_name})


    def add_dataframe(self, df, quiet=False, metadata=None, set_active=True, parent=None):

        if metadata is None:
            metadata = {}

        new_node = self.app.model.add_dataframe(df=df, metadata=metadata, parent=parent)
        if set_active:
            self.set_active(new_node)
        if not quiet:
            self.app.view.display_active()

    def set_active(self, node):
        self.app.model.set_active(node)
        

    def quit(self, **kwargs): 
        sys.exit(0)


    def get_input(self, prompt_str=None):
        if prompt_str is None: prompt_str = self.DEFAULT_PROMPT
        try:
            raw_input_string = self.prompt(prompt_str)
        except EOFError:
            sys.exit(0)
        return raw_input_string


    def update(self, prompt_str=None):
        if prompt_str is None: prompt_str = self.DEFAULT_PROMPT
        
        if len(self.input_list) == 0:
            raw_input_string = self.get_input(prompt_str=prompt_str)
            self.input_list += self.parse_input_recursive(raw_input_string)


class TextControllerNonInteractive(TextController):

    def update(self, **kwargs):
        pass

class Model(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        
        self.app = kwargs['app']
        self.graph = nx.DiGraph()
        self._active = None

    @property
    def names(self):
        return [x.name for x in self.graph.nodes()]

    def set_name(self, new_name):
        one([x for x in self.graph.nodes() if x.name == new_name]).name = new_name

    # def remove_node_by_name(self, name):

    #     node_to_remove = one([x for x in self.graph.nodes() if x.name == name])

    def get_nodes_by_name(self, name=None, name_list=None):

        if name_list is None:
            name_list = []

        if name is not None:
            name_list += [name]

        return [x for x in self.graph.nodes() if x.name in name_list]

        
    def remove_node(self, node):
        self.graph.remove_node(node_to_remove)

    def add_dataframe(self, df=None, metadata=None, name=None, parent=None):
        if metadata is None:
            metadata = {}
        new_node = DataFrameNode(df=df, metadata=metadata, name=name)

        self.graph.add_node(new_node)

        if parent is not None:
            self.graph.add_edge(parent, new_node)

        return new_node

    def set_active(self, node_or_node_list):
        node_type_list = (DataFrameNode,)
        if isinstance(node_or_node_list, (set, list)):
            for x in node_or_node_list:
                assert isinstance(x, node_type_list)
        else:
            assert isinstance(node_or_node_list, node_type_list)

        self._active = node_or_node_list


    @property
    def active(self):
        return self._active

class ConsoleView(object):

    def __init__(self, **kwargs):
        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']

    def display_active(self, **kwargs):
        requests.post('http://localhost:5000/active', data={'header':[], 'data':self.app.model.active.to_html()})
        self.display_message(str(self.app.model.active), **kwargs)

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


    def run_hard_exit(self, input=['']):

        self.controller.initialize_input(input)
        while len(self.controller.input_list) > 0:

            curr_input, curr_input_kwargs = self.controller.input_list.pop(0)
            curr_input(**curr_input_kwargs)            
            self.controller.update()

        return self.model.active

    def run(self, *args, **kwargs):
        try:
            self.run_hard_exit(*args, **kwargs)
        except SystemExit as e:
            return self.model.active


    


if __name__ == "__main__":    
    df_file_name = os.path.join(os.path.dirname(__file__),'..', 'tests', 'example.csv')

    def get_dfbd():
        dfb = DataFrameBrowser(logging_settings={'handler':logging.StreamHandler()})
        return {'dataframe_browser':dfb}




    

    dataframe_browser_fixture = get_dfbd()
    dfb = dataframe_browser_fixture['dataframe_browser']

    input = []
    input.append('open -q -f {0}'.format(os.path.join(os.path.dirname(__file__),'..', 'tests', 'example.csv')))
    input.append('bookmark this-branch')
    input.append('query a>0')
    input.append('bookmark this-other_branch')
    input.append('bookmark --rm this-branch')



    last_active = dfb.run(input=input)
    print dfb.model.names

    print type(last_active)


import pandas as pd
import networkx as nx
import sys
import logging
from collections import OrderedDict
import json
import traceback
import os
import io
import requests
import warnings
import readline
import shlex
import argcomplete
import re
import atexit
import itertools
from future.utils import raise_from

from cssutils import parseStyle
from bs4 import BeautifulSoup as BeautifulSoupPre
def BeautifulSoup(*args, **kwargs):
    kwargs.setdefault('features', 'lxml')
    return BeautifulSoupPre(*args, **kwargs)

ANON_DEFAULT='<anon>'
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
ACTIVATE = 'select'
COMMAND = 'cmd'
INFO = 'info'

main_parser = ArgumentParser(description='main_parser description', prog=DEFAULT_PROMPT.strip(), add_help=False)
main_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')

open_parser = ArgumentParser(description='open description', prog=DEFAULT_PROMPT.strip(), add_help=False)
open_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')
open_parser.add_argument("-f", "--file", nargs='+', dest='file_list', type=str, default=[])
open_parser.add_argument("--uri", nargs=1, dest='uri', type=str)
open_parser.add_argument("-q", "--quiet", dest='quiet', action='store_true')
open_parser.add_argument("--table", nargs='+', dest='table_list', type=str, default=[])
open_parser.add_argument("--group-name", nargs='?', type=str)

activate_parser = ArgumentParser(description='activate description', prog=DEFAULT_PROMPT.strip(), add_help=False)
activate_parser.add_argument(nargs=1, dest='name', type=str)

query_parser = ArgumentParser(description='query description', prog=DEFAULT_PROMPT.strip(), add_help=False)
query_parser.add_argument(nargs='*', dest='remainder_list', type=str)

bookmark_parser = ArgumentParser(description='set-bookmark description', prog=DEFAULT_PROMPT.strip(), add_help=False)
bookmark_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')
bookmark_parser.add_argument('name', nargs='?', type=str)
bookmark_parser.add_argument('-f', '--force', dest='force', action='store_true')
bookmark_parser.add_argument('--rm', dest='remove', action='store_true')

info_parser = ArgumentParser(description='info description', prog=DEFAULT_PROMPT.strip(), add_help=False)
info_parser.add_argument('--help', '-h', action=HelpAction, help='show this help message')
# info_parser.add_argument('-b', dest='bookmark_info', action='store_true', help='List current bookmarks')
# info_parser.add_argument('-v', dest='verbose', action='store_true', help='verbose mode')

command_parser_dict = {OPEN:open_parser, QUERY:query_parser, BOOKMARK:bookmark_parser, ACTIVATE:activate_parser, INFO:info_parser}
main_parser.add_argument(COMMAND, choices=command_parser_dict.keys(), nargs='?')

import time
import functools

def fn_timer(function):
    @functools.wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        return result, t1-t0
    return function_timer

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

    def __init__(self, df=None, metadata=None):

        # TODO?
        # https://www.kaggle.com/arjanso/reducing-dataframe-memory-size-by-65
        self.df = df
        self.metadata = metadata

        self._load_time = None

    def set_load_time(self, t):
        self._load_time = t
    
    @property
    def load_time(self):
        return self._load_time
    
    @property
    def memory_usage(self):
        return self.df.memory_usage(deep=True).sum()

    @property
    def table(self):
        return self.df

    def to_html(self, columns=None):

        if columns is None:
            columns = self.df.columns
        
        table_class = "display"
        table_html = self.df[columns].to_html(classes=[table_class], index=False)
        table_html_bs = table_html_bs = BeautifulSoup(table_html).table
        style = parseStyle(table_html_bs.thead.tr['style'])
        style['text-align'] = 'center'
        table_html_bs.thead.tr['style'] = style.cssText

        return str(table_html_bs)

    def __str__(self):

        with pd.option_context('display.max_rows', 11, 'display.max_columns', 10):
            return str(self.df)
    
    @property
    def columns(self):
        return [str(x) for x in self.df.columns]

    def describe(self, **kwargs):
        return self.df.describe(**kwargs)

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
            if cmd == QUERY and self.controller.app.model.active is not None:
                subparser_command_dict[cmd] = ['{0} {1}'.format(cmd, x) for x in self.controller.app.model.all_active_columns]
            elif cmd == ACTIVATE:
                subparser_command_dict[cmd] = ['{0} {1}'.format(cmd, x) for x in self.controller.app.model.bookmarks if x is not None]
            else:
                tmp = startswith_text[len(cmd)+1:]
                subparser_command_dict[cmd] = ['{0} {1}'.format(cmd, x) for x in get_argcompletion_matches(completion_finder, tmp)]

        ## INSERT CUSTOM MODIFICATION HERE: (START)
        # print
        # print startswith_text, subparser_command_dict[ACTIVATE]

        # Add ACTIVATE option for iith elemend 
        tmp = []
        for key, val in self.controller.app.model.bookmark_dict.items():
            tmp += ['{cmd} {subcmd}[{ii}]'.format(cmd=ACTIVATE, subcmd=key, ii=ii) for ii in range(len(val)) if  startswith_text[:len('{cmd} {subcmd}'.format(cmd=ACTIVATE, subcmd=key))] == '{cmd} {subcmd}'.format(cmd=ACTIVATE, subcmd=key)]
        subparser_command_dict[ACTIVATE] += tmp
                        
        ## INSERT CUSTOM MODIFICATION HERE: (END)

        subparser_commands = []
        for command_list in subparser_command_dict.values():
            subparser_commands += command_list

        all_option_list = [i for i in ['help']+subparser_commands+main_commands if i.startswith(startswith_text)]

        # print 
        # print startswith_text, subparser_command_dict[ACTIVATE], all_option_list
        # print


        return all_option_list

    def completer(self, startswith_text, state):

        try:
            options = self.get_options(startswith_text)
        except Exception as e:
            traceback.print_exc()
            sys.exit(1)

        if state < len(options):
            return options[state]
        else:
            return None


class TextController(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']
        self._prompt = DEFAULT_PROMPT

        self.sep = COMMAND_SEP_CHAR
        self.input_list = None

        self.subparser_dict = command_parser_dict
        self.main_parser = main_parser

        self.completion_finder = CompletionFinder(controller=self)
        self.completion_finder.initialize(histfile=kwargs.get('histfile', None))
        
        self.prompt_fcn = raw_input

    @property
    def prompt(self):
        if self.app.model.active_name is None:
            return self._prompt
        else:
            return '({active_name}) {prompt}'.format(active_name=self.app.model.active_name, prompt=self._prompt)

    def input_mapper(self, input):

        # No-op for this command; either requested help, or unrecognized
        if len(input) == 1 or (len(input) == 2 and input[1].get('help', None) == True):
            return (lambda : None, {})

        # TODO: reorganize query, so that this becomes a loop

        if OPEN in input[1]:
            return self.open_command, input[1][OPEN]
        elif QUERY in input[1]:
            query = ' '.join(input[1][QUERY]['remainder_list'])
            return self.query_command, {'query':query}
        elif BOOKMARK in input[1]:
            return self.bookmark_command, input[1][BOOKMARK]
        elif ACTIVATE in input[1]:
            return self.activate_command, input[1][ACTIVATE]
        elif INFO in input[1]:
            return self.info_command, input[1][INFO]


        else:
            raise NotImplementedError(input)

    @fn_timer
    def info_command(self, **kwargs):
        self.logger.info(json.dumps({INFO:kwargs}, indent=4))
        
        print 'Bookmarked groups: ("*" means currently active)'
        for name in self.app.model.bookmarks:
            print '{name}{active} ({num_df})'.format(name=name, active='*' if name == self.app.model.active_name else '', num_df=len(self.app.model.bookmark_dict[name]))

        
        print '\nActive group: ({anon} if not bookmarked)'.format(anon=ANON_DEFAULT)

        if self.app.model.active_name in self.app.model.bookmarks:
            name_prefix = self.app.model.active_name
        else:
            name_prefix = '<anon>'.format(anon=ANON_DEFAULT)

        if self.app.model.active is not None:
            if len(self.app.model.active) == 1:
                describe_df = one(self.app.model.active).describe(include='all')
                describe_df.columns.name = '{name_prefix}'.format(name_prefix=name_prefix)
                print describe_df
            else:
                describe_df_list = [x.describe(include='all') for x in self.app.model.active]
                for ii, df in enumerate(describe_df_list):
                    df.columns.name = '{name_prefix}[{ii}]'.format(name_prefix=name_prefix, ii=ii)
                zipped_row_list = zip(*[str(x).split('\n') for x in describe_df_list])
                print '\n'.join(['  |  '.join(row) for row in zipped_row_list])

        # # Print information about bookmarks:
        # if kwargs.pop('bookmark_info'):
        #     print 'Bookmarks:'
        #     for name in self.app.model.bookmarks:
        #         if verbose_mode:
        #             for ii, node in enumerate(self.app.model.bookmark_dict[name]):
        #                 name_str = '{name}{active}[{ii}]'.format(name=name, active='*' if name == self.app.model.active_name else '', ii=ii)
        #                 info_df = node.describe(include='all')
        #                 info_df.index.rename(name_str, inplace=True)
        #                 print info_df
        #         else:
        #             name_str = '{name}{active} ({num_df})'.format(name=name, active='*' if name == self.app.model.active_name else '', num_df=len(self.app.model.bookmark_dict[name]))
        #             print name_str
        #         # print 'hello', name

        # Makes sure I implemented everything
        # assert len(kwargs) == 0

    @fn_timer
    def activate_command(self, **kwargs):
        self.logger.info(json.dumps({ACTIVATE:kwargs}, indent=4))
        name_pre = one(kwargs['name'])
        split_name = re.split("\[[0-9]+[0-9]*\]$", name_pre)
        if len(split_name) == 1:
            full_name = one(split_name)
            node_list = self.app.model.bookmark_dict[full_name]
        else:
            assert len(split_name) == 2
            assert len(split_name[1]) == 0
            part_name = split_name[0]
            idx = int(name_pre.replace(part_name,'')[1:-1])
            node_list = [self.app.model.bookmark_dict[part_name][idx]]
            full_name = '{part_name}[{idx}]'.format(part_name=part_name, idx=idx)
        
        self.set_active(node_list, name=full_name)

    def parse_single_command(self, command, parser=main_parser):
        split_command = shlex.split(command)
        if split_command in (['help'], ['?']): 
            split_command = ['--help']
        if len(split_command) == 0:
            return ('',)

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

    @fn_timer
    def bookmark_command(self, **kwargs):

        name = kwargs.pop('name')

        if kwargs['remove']:
            self.remove_bookmark(name=name)
        else:
            self.add_bookmark(name=name, force=kwargs['force'])

    def remove_bookmark(self, **kwargs):
        name=kwargs['name']
        node = one(self.app.model.get_nodes_by_name(name=name))
        node.set_name(None)
        self.logger.info(json.dumps({'REMOVE_BOOKMARK':kwargs}, indent=4))

    @fn_timer
    def open_command(self, **kwargs):

        quiet = kwargs.get('quiet', False)
        bookmark = kwargs.get('bookmark', None)
        set_active = kwargs.get('set-active', True)
        new_node_list = []
        for file_name in kwargs.get('file_list', []):
            new_node, load_time = self.load_new_df_from_file(file_name=file_name, quiet=quiet, set_active=False)
            new_node.set_load_time(load_time)
            self.logger.info(json.dumps({'LOAD_TIME':load_time}, indent=4))
            if new_node is not None: new_node_list.append(new_node)

        for table in kwargs.get('table_list', []):
            uri = kwargs['uri'][0]
            new_node = self.load_new_df_from_uri(table=table, uri=uri, quiet=quiet, set_active=False)
            if new_node is not None: new_node_list.append(new_node)
        
        if set_active:
            self.set_active(new_node_list)
            if bookmark is not None:
                self.set_bookmark_to_current_active(name=bookmark)
        
    def set_bookmark_to_current_active(self, **kwargs):
        self.app.model.set_bookmark_to_current_active(**kwargs)

    def load_new_df_from_uri(self, **kwargs):
        uri = kwargs['uri']
        table = kwargs['table']
        quiet = kwargs.get('quiet', False)
        set_active = kwargs.get('set_active', True)
        df = pd.read_sql_table(table, uri)
        return self.add_dataframe(df, parent=None, quiet=quiet, metadata={'uri':uri, 'table':table}, set_active=set_active)

    def display_active_df_info(self, **kwargs):
        buffer = io.StringIO()
        self.app.model.active.info(buf=buffer, **kwargs)
        self.app.view.display_active_df_info(buffer)

    @fn_timer
    def query_command(self, **kwargs):
        raise NotImplementedError
        # query_string = kwargs['query']
        # parent_node = self.app.model.active
        # result_df = parent_node.table.query(query_string)
        # # self.add_dataframe(result_df, parent=parent_node, metadata={'query':query_string})
        # self.logger.info(json.dumps({'QUERY':kwargs}, indent=4))
        # return self.add_dataframe(df, parent=None, quiet=quiet, metadata={'uri':uri, 'table':table}, set_active=set_active)


    def add_bookmark(self, **kwargs):

        if 'name' not in kwargs:
            kwargs['name'] = self.app.model.active_name # IT IS POSSIBLE TO BE ACTIVE AND NOT BOOKMARKED!!!
        
        msg = 'Bookmark added: {0}'.format(kwargs['name'])
        try:
            if self.set_bookmark_to_current_active(**kwargs):
                self.app.view.display_message(msg, type='info')
                self.app.view.display_active()
                self.logger.info(json.dumps({'ADD_BOOKMARK':kwargs}, indent=4))
        except BookmarkAlreadyExists as e:

            if kwargs.get('force', False):
                if self.set_bookmark_to_current_active(**kwargs):
                    self.app.view.display_message(msg, type='info')
                    self.app.view.display_active()
                    self.logger.info(json.dumps({'ADD_BOOKMARK':kwargs}, indent=4))
            else:
                self.app.view.display_message(str(e), type='error')

    @fn_timer        
    def load_new_df_from_file(self, **kwargs):

        file_name = kwargs['file_name']
        quiet = kwargs.get('quiet', False)
        set_active = kwargs.get('set_active', True)

        if not os.path.exists(file_name):
            self.app.view.display_message('Source not found: {0}\n'.format(file_name), type='error')
            return

        if file_name[-4:] == '.csv':
            df = pd.read_csv(file_name, index_col=kwargs.get('index_col', 0))
        elif file_name[-2:] == '.p':
            df = pd.read_pickle(file_name)
        else:
            self.app.view.display_message('File extension not in (csv/p): {0}\n'.format(file_name), type='error')
            return

        return self.add_dataframe(df, parent=None, quiet=quiet, metadata={'file_name':file_name}, set_active=set_active)


    def add_dataframe(self, df, quiet=False, metadata=None, set_active=True, parent=None):

        if metadata is None:
            metadata = {}

        new_node = self.app.model.add_dataframe(df=df, metadata=metadata, parent=parent)
        if set_active:
            self.set_active([new_node], quiet=quiet)

        return new_node

    def set_active(self, node_list, quiet=False, name=None):

        self.logger.info(json.dumps({'SET_ACTIVE':str(node_list)}, indent=4))
        self.app.model.set_active(node_list, name=name)
        if not quiet:
            self.app.view.display_active()
        

    def quit(self, **kwargs): 
        sys.exit(0)


    def get_input(self):
        try:
            raw_input_string = self.prompt_fcn(self.prompt)
        except EOFError:
            sys.exit(0)
        return raw_input_string


    def update(self):
        
        if len(self.input_list) == 0:
            raw_input_string = self.get_input()
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
        self._active_name = None
        self.bookmark_dict = {}

    @property
    def active_name(self):
        return self._active_name

    @property
    def bookmarks(self):
        return self.bookmark_dict.keys()

    def set_bookmark_to_current_active(self, name=None, force=False, append=False):

        if name is None:
            name = self._active_name
            if name is None:
                self.logger.info('No name given for bookmark, and no active name')
                return False

        if name in self.bookmarks and not force==True:
            raise BookmarkAlreadyExists()

        if append == True:
            if len(self.active) == 1:
                self.bookmark_dict[name].append(one(self.active))
            else: 
                self.bookmark_dict[name] += self.active
        else:
            self.bookmark_dict[name] = [x for x in self.active]
        self._active_name = name

        return True
        
    def _remove_node(self, node):
        self.graph.remove_node(node)

    def add_dataframe(self, df=None, metadata=None, parent=None):
        if metadata is None:
            metadata = {}

        new_node = DataFrameNode(df=df, metadata=metadata)

        self.graph.add_node(new_node)

        if parent is not None:
            self.graph.add_edge(parent, new_node)

        return new_node

    def set_active(self, node_list, name=None):
        self.logger.info(json.dumps({'SET_ACTIVE':str(node_list)}, indent=4))
        self._active = [x for x in node_list]
        self._active_name = name
    
    def activate_bookmark(self, name):
        self.set_active(self.bookmark_dict[name], name=name)

    @property
    def common_active_columns(self):
        return sorted(set.intersection(*[set(node.columns) for node in self.active]))

    @property
    def all_active_columns(self):
        return sorted(set.union(*[set(node.columns) for node in self.active]))

    @property
    def active(self):
        return self._active

class ConsoleView(object):

    def __init__(self, **kwargs):
        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        self.app = kwargs['app']

    def display_active(self, **kwargs):

        if len(self.app.model.active) < 1:
            response = requests.post('http://localhost:5000/multi', json=json.dumps([]))

        else:
            if 'page_length' not in kwargs:
                page_length = 5 if len(self.app.model.active) > 1 else 20

            uuid_table_list = []
            for ni, node in enumerate(self.app.model.active):

                if self.app.model.active_name is None:
                    active_name = ANON_DEFAULT
                else:
                    if len(self.app.model.active) > 1:
                        active_name = '{active_name}[{ni}]'.format(active_name=self.app.model.active_name, ni=ni)
                    else:
                        active_name = self.app.model.active_name
                common_col_list = self.app.model.common_active_columns
                table_html = node.to_html(columns=common_col_list + [c for c in node.columns if c not in common_col_list])
                table_html_bs = BeautifulSoup(table_html).table
                table_uuid = generate_uuid()
                table_html_bs['id'] = table_uuid
                uuid_table_list.append((table_uuid, str(table_html_bs), page_length, active_name))

            response = requests.post('http://localhost:5000/multi', json=json.dumps(uuid_table_list))
        self.logger.info(json.dumps({'DISPLAY_ACTIVE':{'response':str(response)}}, indent=4))

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

        if 'df' in kwargs:
            
            node_list = []
            bookmark = kwargs.get('bookmark', None)
            if isinstance(kwargs['df'], (tuple, list)):
                for df in kwargs['df'][::-1]:
                    node = self.controller.add_dataframe(df, set_active=False)
                    node_list.append(node)
                self.controller.set_active(node_list)
                if bookmark is not None:
                    self.controller.set_bookmark_to_current_active(name=bookmark)

            elif isinstance(kwargs['df'], (pd.DataFrame)):
                node = self.controller.add_dataframe(kwargs['df'], set_active=False)
                self.controller.set_active([node])
                if bookmark is not None:
                    self.controller.set_bookmark_to_current_active(name=bookmark)

            



            # def add_dataframe(self, df, quiet=False, metadata=None, set_active=True, parent=None):


    def run_hard_exit(self, input=[''], interactive=True):

        self.controller.initialize_input(input)
        while len(self.controller.input_list) > 0:

            curr_input, curr_input_kwargs = self.controller.input_list.pop(0)
            res = curr_input(**curr_input_kwargs)      
            
            if res is not None:
                res, exec_time = res

            if interactive == True:
                self.controller.update()



        return self.model.active

    def run(self, *args, **kwargs):
        try:
            self.run_hard_exit(*args, **kwargs)
        except SystemExit as e:
            return self

    @property
    def active(self):
        return self.model.active

    def info(self, **kwargs):
        info, exec_time = self.controller.info_command(**kwargs)
        return info


    


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
    input.append('bookmark other-branch')
    input.append('activate this-branch')



    active = dfb.run(input=input)

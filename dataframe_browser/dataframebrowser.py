import pandas as pd
import networkx as nx
import sys
import logging
from collections import OrderedDict
import json
import os
import uuid
import warnings

DEFAULT_PROMPT = 'df> '
COMMAND_SEP_CHAR = ';'
UNRECOGNIZED_INPUT_FORMAT = 'Unrecognized input: "{0}"\n'
UUID_LENGTH = 32

def generate_uuid(length=UUID_LENGTH):
    '''https://gist.github.com/admiralobvious/d2dcc76a63df866be17f'''

    u = uuid.uuid4()
    return u.hex[:length]

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
        self.sep = COMMAND_SEP_CHAR

    def parse_text_input(self, text_input, sep=None):
        if sep is None: sep = self.sep
        text_input_list = [input.strip() for input in text_input.split(sep)]
        if len(text_input_list) > 1:
            text_input_list = [x for x in text_input_list if len(x)>0]

        return text_input_list

    def parse_input(self, input):
        if isinstance(input, (str,)):
            input_list = self.parse_text_input(input)

        elif isinstance(input, (list, tuple)):
            input_list = []
            for x in input:
                input_list += self.parse_input(x)
            return input_list
        
        else:
            raise NotImplementedError('Input not parsed: {0}'.format(input))

        return [self.input_mapper(input) for input in input_list]


    def input_mapper(self, input):

        if input in self.QUIT_VALS: 
            fcn, kwargs = self.quit, {}
        elif input[:2] == self.NEW_DF_NODE: 
            fcn, kwargs = self.load_new_df, {'source': input[2:].strip()}
        elif input[:2] == self.ADD_BOOKMARK: 
            fcn, kwargs = self.add_bookmark, {'input_value': input[2:].strip()}
        elif len(input) == 0: 
            fcn, kwargs = self.display_active, {}
        elif input[:2] == self.QUERY: 
            fcn, kwargs = self.query, {'query': input[2:].strip()}
        else: 
            fcn, kwargs = self.unrecognized, {'input_value':input.strip()}

        self.logger.info(json.dumps({fcn.__name__:kwargs}))

        return fcn, kwargs

    def query(self, **kwargs):

        query_string = kwargs['query']
        parent_node = self.app.model.active_node
        result_df = self.app.model.active.query(query_string)
        active_node = self.add_node(result_df)
        self.add_edge(parent_node, active_node, query=query_string)

    def add_edge(self, source, target, **kwargs):
        self.app.model.graph.add_edge(source, target, **kwargs)


    def user_message(self, message):
        print message


    def add_bookmark(self, **kwargs):
        
        bookmark_name = kwargs['input_value']
        if bookmark_name in self.app.model.bookmarks:
            self.user_message('Bookmark name {0} already in use'.format(bookmark_name))

        else:
            self.app.model.bookmarks[bookmark_name] = self.app.model.active
            self.user_message('Bookmark added: {0}'.format(bookmark_name))
            

        

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

        uuid = generate_uuid()
        self.app.model.graph.add_node(uuid, df=df, **kwargs)
        self.set_active(uuid)
        self.display_active()
        return uuid

    def set_active(self, uuid):
        self.app.model.active_node = uuid

    def display_active(self, **kwargs):
        print self.app.model.active

        

    def quit(self, **kwargs): 
        sys.exit(0)


    def unrecognized(self, **kwargs):
        print UNRECOGNIZED_INPUT_FORMAT.format(kwargs['input_value'])

    def get_input(self, prompt=None):
        if prompt is None: prompt = self.DEFAULT_PROMPT
        try:
            raw_input_string = raw_input(prompt)
        except EOFError:
            sys.exit(0)
        return raw_input_string


    def update(self, parsed_input_list, prompt=None):
        if prompt is None: prompt = self.DEFAULT_PROMPT
        
        if len(parsed_input_list) == 0:
            raw_input_string = self.get_input(prompt=prompt)
            parsed_input_list += self.parse_input(raw_input_string)


class TextControllerNonInteractive(TextController):

    def update(self, parsed_input_list, **kwargs):
        pass

class Model(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        
        self.app = kwargs['app']
        self.graph = nx.DiGraph()
        self.bookmarks = {}
        self.active_node = None

    @property
    def active(self):
        return self.graph.nodes[self.active_node]['df']

class DataFrameBrowser(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))

        model_kwargs = kwargs.get('model_kwargs', {})
        self.model = Model(app=self, **model_kwargs)

        controller_kwargs = kwargs.get('controller_kwargs', {})
        self.controller = kwargs.get('controller_class', TextController)(app=self, **controller_kwargs)

    def run(self, input=['']):

        parsed_input_list = self.controller.parse_input(input)
        while len(parsed_input_list) > 0:

            curr_input, curr_input_kwargs = parsed_input_list.pop(0)
            curr_input(**curr_input_kwargs)            
            self.controller.update(parsed_input_list)

        return self


if __name__ == "__main__":    
    df_file_name = os.path.join(os.path.dirname(__file__),'..', 'tests', 'example.csv')

    def get_dfbd():
        dfb = DataFrameBrowser(logging_settings={'handler':logging.StreamHandler()})
        return {'dataframe_browser':dfb}

    

    dataframe_browser_fixture = get_dfbd()
    dataframe_browser_fixture['dataframe_browser'].run(input=['o: {0}; b: TEST'.format(df_file_name), 'q: a>1'])
    G = dataframe_browser_fixture['dataframe_browser'].model.graph
    assert len(dataframe_browser_fixture['dataframe_browser'].model.active) == 7
    assert len(G.nodes) == 2
    assert len(G.edges) == 1
    assert len(dataframe_browser_fixture['dataframe_browser'].model.active) == 5


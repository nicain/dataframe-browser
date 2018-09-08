import pandas as pd
import networkx as nx
import sys
import logging
from collections import OrderedDict
import json


PROMPT = 'df> '
COMMAND_SEP_CHAR = ';'
UNRECOGNIZED_INPUT_FORMAT = 'Unrecognized input: "{0}"\n'

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
        self.QUIT_VALS = kwargs.get('QUIT_VALS', ['q:', 'exit()'])
        self.PROMPT = kwargs.get('PROMPT', PROMPT)

    def parse_text_input(self, text_input):
        return [input.strip() for input in text_input.split(COMMAND_SEP_CHAR)]


    def parse_input(self, input):
        if isinstance(input, (str,)):
            input_list = self.parse_text_input(input)

        elif isinstance(input, (list, tuple)):
            input_list = input
        
        else:
            raise NotImplementedError

        return [self.input_mapper(input) for input in input_list]


    def input_mapper(self, input):

        if input in self.QUIT_VALS: 
            fcn, kwargs = self.quit, {}
        else: 
            fcn, kwargs = self.unrecognized, {'input_value':input}

        self.logger.info(json.dumps({fcn.__name__:kwargs}))

        return fcn, kwargs


    def quit(self, **kwargs): 
        sys.exit(0)


    def unrecognized(self, **kwargs):
        print UNRECOGNIZED_INPUT_FORMAT.format(kwargs['input_value'])

    def update(self, parsed_input_list):
        if len(parsed_input_list) == 0:

            try:
                raw_input_string = raw_input(self.PROMPT)
                parsed_input_list += self.parse_input(raw_input_string)
            except EOFError:
                sys.exit(0)


class TextControllerNonInteractive(TextController):

    def update(self, parsed_input_list):
        pass

class Model(object):

    def __init__(self, **kwargs):

        self.logger = create_class_logger(self.__class__, **kwargs.get('logging_settings', {}))
        
        self.app = kwargs['app']
        self.graph = nx.DiGraph()


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


if __name__ == "__main__":

    controller_stream = None
    app_stream = None
    formatter = None

    import pytest
    pytest.main(['-q', '-x', '/home/nicholasc/projects/dataframe-browser'])
    
    
    
    controller_kwargs = {'logging_settings':{'handler':logging.StreamHandler(stream=controller_stream),
                                             'formatter': formatter}}
    DataFrameBrowser(controller_class=TextController, 
                     controller_kwargs=controller_kwargs, 
                     logging_settings={'handler':logging.StreamHandler(stream=app_stream)}).run(input='blah blah; q:')
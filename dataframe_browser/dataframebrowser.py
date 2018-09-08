import pandas as pd
import networkx as nx
import sys



PROMPT = '>>>'
COMMAND_SEP_CHAR = ';'



class TextController(object):

    def __init__(self, **kwargs):
        self.QUIT_VALS = kwargs.get('QUIT_VALS', ['q:'])
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
            return self.quit
        else: 
            return self.unrecognized


    def quit(self, **kwargs): 
        sys.exit(0)


    def unrecognized(self, **kwargs):
        print 'Unrecognized input: {0}'.format(kwargs['input_value'])

    def update(self, parsed_input_list):
        if len(parsed_input_list) == 0:
            raw_input_string = raw_input(self.PROMPT)
            parsed_input_list += self.parse_input(raw_input_string)

class TextControllerNonInteractive(TextController):

    def update(self, parsed_input_list):
        pass

class Model(object):

    def __init__(self, **kwargs):

        self.graph = nx.DiGraph()


class DataFrameBrowser(object):

    def __init__(self, **kwargs):

        model_kwargs = kwargs.get('model_kwargs', {})
        self.model = Model(**model_kwargs)

        controller_kwargs = kwargs.get('controller_kwargs', {})
        self.controller = kwargs.get('controller_class', TextController)(**controller_kwargs)

    def run(self, input=['']):

        parsed_input_list = self.controller.parse_input(input)
        while len(parsed_input_list) > 0:
            curr_input = parsed_input_list.pop(0)
            curr_input()
            raise


if __name__ == "__main__":

    import pytest
    pytest.main(['-s', '-x', '-v', '/home/nicholasc/projects/dataframe-browser'])

    DataFrameBrowser().run(input=['', 'q:'])
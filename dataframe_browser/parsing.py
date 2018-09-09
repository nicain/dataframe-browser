

import argparse
import sys
from .exceptions import CommandParsingException

class ArgumentParser(argparse.ArgumentParser):
    
    def error(self, message):
        raise CommandParsingException(message, parser=self)



class HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        setattr(namespace, self.dest, True)

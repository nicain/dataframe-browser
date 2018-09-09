

import argparse
import sys
from .exceptions import CommandParsingException

class ArgumentParser(argparse.ArgumentParser):
    
    def error(self, message):
        self.print_help(sys.stderr)
        raise CommandParsingException()
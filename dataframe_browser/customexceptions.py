from six import PY3

if PY3:
    pass
else:
     FileNotFoundError = IOError

class BookmarkAlreadyExists(Exception):
    pass

class UnrecognizedFileTypeException(Exception):
    pass

class CommandParsingException(Exception):
    
    def __init__(self, message, parser):

        super(CommandParsingException, self).__init__(message)
        self.parser = parser


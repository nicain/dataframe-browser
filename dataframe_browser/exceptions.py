

class BookmarkAlreadyExists(Exception):
    pass


class CommandParsingException(Exception):
    
    def __init__(self, message, parser):

        super(CommandParsingException, self).__init__(message)
        self.parser = parser


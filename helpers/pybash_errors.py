class NoImportFound(Exception):
    """ Raised when a user tries to import a nonexistent library """
    pass

class TooManyArguments(Exception):
    """ Raised when a user tries to give too many arguments to a function """
    pass

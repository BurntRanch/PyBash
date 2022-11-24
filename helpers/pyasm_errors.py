

class InvalidVariableName(Exception):
    """ Raised when a user tries to set PyAsm runtime variables """
    pass

class NoImportFound(Exception):
    """ Raised when a user tries to import a nonexistent library """
    pass

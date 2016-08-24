class ATARException(Exception):
    def __init__(self, message, *, expireIn=0):
        self.message = message
        self.expireIn = expireIn

    @property
    def message(self):
        return self.message

    @property
    def messageNoFormat(self):
        return self.message

# Error during command processing
class CommandError(ATARException):
    pass

class PermissionsError(CommandError):
    @property
    def message(self):
        return "You don't have permission to use that command: " + self.message

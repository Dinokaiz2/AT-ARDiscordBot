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

class HelpfulError(ATARException):
    def __init__(self, issue, solution, *, preface="Encountered an error:\n", expire_in=0):
        self.issue = issue
        self.solution = solution
        self.preface = preface
        self.expire_in = expire_in

    @property
    def message(self):
        return ("\n{}\n{}\n{}\n").format(
            self.preface,
            self._pretty_wrap(self.issue,    "  Problem:  "),
            self._pretty_wrap(self.solution, "  Solution: "))

    @property
    def message_no_format(self):
        return "\n{}\n{}\n{}\n".format(
            self.preface,
            self._pretty_wrap(self.issue,    "  Problem:  ", width=None),
            self._pretty_wrap(self.solution, "  Solution: ", width=None))

    @staticmethod
    def _pretty_wrap(text, pretext, *, width=-1):
        if width is None:
            return pretext + text
        elif width == -1:
            width = shutil.get_terminal_size().columns

        l1, *lx = textwrap.wrap(text, width=width - 1 - len(pretext))

        lx = [((' ' * len(pretext)) + l).rstrip().ljust(width) for l in lx]
        l1 = (pretext + l1).ljust(width)

        return ''.join([l1, *lx])

# Base class for control signals
class Signal(Exception):
    pass

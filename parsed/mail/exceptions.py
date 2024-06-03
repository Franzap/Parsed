class ParseError(Exception):
    ...


class HeaderDefect(ParseError):
    ...


class BodyDefect(ParseError):
    ...


class MessageDefect(ParseError):
    ...

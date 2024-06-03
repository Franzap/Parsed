from enum import Enum

# TODO WE SHOULD CONFIGURE THE ENUM FOR KEYWORD IN A MAIL MESSAGE

"""
    From: ...
    Sent: ...
    To: ...
    Cc: ...
    Subject: ...
"""


class MailBoundsITA(Enum):
    SUBJECT = [(None, "\n")]
    TO = [("A: ", "Cc"), ("A: ", "Oggetto: ")]
    FROM = [("Da: ", "Inviato: ")]
    CC = [("Cc", "Oggetto: ")]
    BODY = [("\n", None)]
    RECEIVED = [("Inviato: ", "A: ")]
    SUB_BODY = [("Oggetto: ", None)]


class MailBoundsENG(Enum):
    SUBJECT = [(None, "\n")]
    TO = [("To: ", "Cc"), ("To: ", "Subject: ")]
    FROM = [("From: ", "Sent: ")]
    CC = [("Cc", "Subject: ")]
    BODY = [("\n", None)]
    RECEIVED = [("Sent: ", "To: ")]
    SUB_BODY = [("Subject", None)]


class MailLangBounds(Enum):
    ITA = MailBoundsITA
    ENG = MailBoundsENG

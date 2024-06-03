from typing import Optional, List
from .enums import MailLangBounds
from .model import MailThread
from parsed.mail import MailObject, Body, BodyParts, Header
from parsed.mail.parser import get_body, get_email_address
from parsed.utils import strp_ita_string


def substring_from_guardians(
        first: Optional[str],
        second: Optional[str],
        string: str
):
    if first is not None:
        first_index = string.find(first)
        if first_index == -1:
            return None
        string = string[first_index + (len(first)):]
    if second is None:
        return string
    second_index = string.find(second)
    if second_index == -1:
        return None
    return string[:second_index]


def get_bounded_value(
        text: str,
        bounds: MailLangBounds
) -> Optional[str]:
    bounded_value = ""
    for bound_tuple in bounds.value:
        bounded_value = substring_from_guardians(
            *bound_tuple,
            string=text
        )
        if bounded_value:
            return bounded_value
    return bounded_value


def mail_from_string(
        mail_str: str
) -> MailObject:
    bounds = MailLangBounds.ENG.value if mail_str[:5] == "From:" else MailLangBounds.ITA.value

    sender = get_bounded_value(
        mail_str,
        bounds.FROM
    )
    sender = get_email_address(sender)

    received = get_bounded_value(
        mail_str,
        bounds.RECEIVED
    )

    if received:
        received = received.strip()
        try:
            received = strp_ita_string(received)
        except Exception:
            received = strp_ita_string(received, "%A, %B %d, %Y %I:%M:%S %p")

    to = get_bounded_value(
        mail_str,
        bounds.TO
    )
    to = get_email_address(to)

    cc = get_bounded_value(
        mail_str,
        bounds.CC
    )
    cc = get_email_address(cc)

    subject_and_body = get_bounded_value(
        mail_str,
        bounds.SUB_BODY
    )
    subject = get_bounded_value(
        subject_and_body,
        bounds.SUBJECT
    )

    body = get_bounded_value(
        subject_and_body,
        bounds.BODY
    )

    body = Body(
        content=[BodyParts(
            content=body,
            content_type="text/plain"
        )]
    )

    header = Header(
        From=sender,
        To=to,
        Received=received,
        Subject=subject,
        Cc=cc
    )

    return MailObject(
        header=header,
        body=body
    )


def thread_from_string(
        mail_text: str
) -> Optional[MailThread]:
    """
        Parses a mail string and if the text is valid, returns a MailThread object
        :param mail_text: text of the mail
        :return: MailThread object or None if text does not contain thread information
    """
    splitted_text = split_thread_text(mail_text)
    if splitted_text:
        thread = MailThread()
        for str_token in splitted_text:
            if str_token != "":
                mail = mail_from_string(str_token)
                if mail is not None:
                    thread.add_mail(mail)
        return thread


def thread_from_mail(
        mail: MailObject
) -> Optional[MailThread]:
    mail_thread = MailThread()
    mails = mail.body.mails()
    mails.append(mail)
    for mail in mails:
        mail_thread.add_mail(mail)
        text: str = get_body(mail, "text/plain")
        thread = thread_from_string(text)
        if thread:
            mail_thread.add_mails(thread.thread)
    return mail_thread


def split_thread_text(
        text: str
) -> Optional[List[str]]:

    confronto = [text.find("Da:"), text.find("From:")]
    confronto = list(filter(lambda x: x >= 0, confronto))

    if not confronto:
        return

    confronto = min(confronto)
    i = confronto + 1
    text_len = len(text)
    splitted_text = []
    while i < text_len:
        j = [text.find("Da:", i), text.find("From:", i)]
        j = list(filter(lambda x: x >= 0, j))
        j = min(j) if j else text_len
        splitted_text.append(text[i - 1:j])
        i = j + 1
    return splitted_text

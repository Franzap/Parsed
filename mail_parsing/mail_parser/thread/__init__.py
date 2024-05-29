from typing import Optional

from .enums import MailLangBounds
from .model import *
from .. import BodyParts, get_body, substring_from_guardians, get_email_address, Body, Header


def create_mail_from_text(mail_str: str):
    def get_bounded_value(text, bounds: MailLangBounds):
        bounded_value = ""
        for bound_tuple in bounds.value:
            bounded_value = substring_from_guardians(
                *bound_tuple,
                string=text
            )
            if bounded_value:
                return bounded_value
        return bounded_value
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
    to = get_bounded_value(
        mail_str,
        bounds.TO
    )
    if to:
        to = to.strip()
        to = to.split(";")
        to = list(map(get_email_address, to))
    cc = get_bounded_value(
        mail_str,
        bounds.CC
    )
    if cc:
        cc = cc.split(";")
        cc = list(map(get_email_address, cc))

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
    body = body.replace("C1 Confidential", "").strip()

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


def create_thread_from_text(mail_text: str) -> Optional[MailThread]:
    """
        Da: ...text...
        Inviato: ...text...
        A: ...text...
        Cc: ...text...
        Oggetto: ...text...
    """
    thread = MailThread()
    splitted_text = split_thread_text(mail_text)
    for str_token in splitted_text:
        if str_token != "":
            thread.add_mail(create_mail_from_text(str_token))

    return thread


def create_thread_from_mail(mail: MailObject) -> Optional[MailThread]:
    mail_thread = MailThread()
    mails = [mail]
    if mail.body.attachments:
        for attachment in mail.body.attachments:
            if isinstance(attachment, MailFile):
                mails.append(attachment.mail_obj)
    for mail in mails:
        mail_thread.add_mail(mail)
        text: str = get_body(mail, "text/plain")
        try:
            thread = create_thread_from_text(text)
            if thread:
                mail_thread.add_mail(thread.thread)
        except Exception as e:
            continue
    return mail_thread


def split_thread_text(text: str) -> List[str]:
    confronto = [text.find("Da:"), text.find("From:")]
    confronto = list(filter(lambda x: x >= 0, confronto))
    if confronto:
        confronto = min(confronto)
    else:
        raise Exception
        return text
    i = confronto + 1
    text_len = len(text)
    splitted_text = []
    while i < len(text):
        j = [text.find("Da:", i, text_len), text.find("From:", i, text_len)]
        j = list(filter(lambda x: x >= 0, j))
        j = min(j) if j else text_len
        splitted_text.append(text[i - 1:j])
        i = j + 1
    return splitted_text

from email.message import EmailMessage, Message
from email.policy import default
from email.utils import parseaddr, parsedate_to_datetime
from email.header import decode_header
from email import message_from_bytes
from .enums import FileExtension
from .exceptions import ParseError
from .model import *
from .thread.model import MailThread
from .utils import flatten_attachment, substring_from_guardians


def get_body(mail: MailObject | BodyParts, tipe: ...):
    if isinstance(mail, MailObject):
        for elem in mail.body.content:
            if isinstance(elem, BodyParts):
                return get_body(elem, tipe)
    else:
        if isinstance(mail.content, list):
            for elem in mail.content:
                return get_body(elem, tipe)
        else:
            if mail.content_type == tipe:
                return mail.content
            else:
                return get_body(mail, tipe)


def get_email_address(target: str):
    address = target.strip()
    address = parseaddr(address)

    return EmailAddress(
        nickname=address[0],
        address=address[1]
    )




def parse_mail_byte(mail_byte: bytes):
    mime = message_from_bytes(mail_byte, policy=default)
    return mime2Model(mime)


def get_address(
        mime_header
) -> Union[List[EmailAddress], EmailAddress]:
    if mime_header is not None:
        addresses = []
        for address in mime_header.split(", "):
            address = parseaddr(address)
            addresses.append(
                EmailAddress(
                    nickname=address[0],
                    address=address[1]
                )
            )
        if len(addresses) == 1:
            return addresses[0]
        else:
            return addresses


def get_subject(
        subject_header
) -> str:
    try:
        subject = ""
        if subject_header:
            # tupla byte, econding
            encoded_tuple = decode_header(subject_header)[0]
            byte_subject = encoded_tuple[0]
            encoding = encoded_tuple[1]
            if encoding:
                subject = byte_subject.decode(encoding)
            else:
                subject = str(byte_subject)
        return subject
    except Exception as e:
        raise e


def get_date(
        mime: Union[Message, EmailMessage]
):
    date = mime.get("date") or mime.get("Date")
    if date:
        return parsedate_to_datetime(date)
    else:
        return ""


def parse_mail_header(mime: Union[Message, EmailMessage]):
    try:
        sender = get_address(
            mime.get("From")
        )
        if not sender:
            raise Exception
        receivers = get_address(
            mime.get("To")
        )
        cc = get_address(
            mime.get("Cc")
        )
        subject = get_subject(
            mime.get("Subject")
        )
        received = get_date(
            mime
        )

        return Header(
            From=sender,
            To=receivers,
            Cc=cc,
            Subject=subject,
            Received=received
        )
    except Exception as e:
        raise ParseError(str(e))


def mime2dict(
        mime: Union[EmailMessage, Message]
):
    mime_dict = dict(mime)
    if mime.is_multipart():
        intern = []
        for part in mime.iter_parts():
            intern.append(mime2dict(part))
        mime_dict.update(
            intern=intern
        )
        return mime_dict
    else:
        # attachment, testo
        mime_dict.update(
            dict(
                content=mime.get_content()
            )
        )
        return mime_dict


def get_attachment_and_body_parts(mime):
    content, attachments = [], []
    for part in mime.iter_parts():
        part = mime2Model(part)
        if isinstance(part, BodyParts):
            content.append(part)
        elif isinstance(part, (File, MailFile)):
            attachments.append(part)
        elif isinstance(part, list):
            attachments.extend(part)

    return content, attachments


def get_mail_obj(mime: Union[EmailMessage, Message]):
    header = parse_mail_header(mime)
    content, attachments = get_attachment_and_body_parts(mime)
    # vedere se questa è una mail
    obj = MailObject(
        header=header,
        body=Body(
            content=content,
            attachments=attachments
        )
    )
    return obj


def get_mail(
        mime: Union[EmailMessage, Message]
):
    try:
        filename = mime.get_filename(failobj="")
        if "eml" in filename or mime.get_content_type() == "message/rfc822":
            if mime.get_content_disposition() == "attachment":
                mail_byte = mime.get_content()
                if isinstance(mail_byte, bytes):
                    mime = message_from_bytes(mail_byte, policy=default)
                else:
                    mime = mail_byte
            mail_obj = get_mail_obj(mime)
            return MailFile(
                filename=filename or "email.eml",
                content=mime.as_bytes(),
                mail_obj=mail_obj,
                encoding=mime.get("Content-Transfer-encoding")
            )
        return get_mail_obj(mime)
    except ParseError as pe:
        return
    except Exception as e:
        raise e


def mime2Model(
        mime: Union[EmailMessage, Message]
):
    obj = get_mail(mime)
    if obj:
        return obj
    elif mime.is_multipart() and not obj:
        return BodyParts(
            content=[
                mime2Model(part)
                for part in mime.iter_parts()
            ],
            content_type=mime.get_content_type()
        )
    else:
        filename = mime.get_filename("")
        try:
            content = mime.get_content()
        except KeyError:
            content = mime.get_payload(decode=True)

        if mime.get_content_disposition() == "attachment" or filename:
            obj = flatten_attachment(
                File(
                    filename=filename,
                    content=content,
                    encoding=mime.get("Content-Transfer-Encoding")
                )
            )
            if isinstance(obj, list):
                for i, attachment in enumerate(obj):
                    if attachment.extension == FileExtension.MAIL.value:
                        obj[i] = parse_mail_byte(attachment.content)
        else:
            obj = BodyParts(
                content=content,
                content_type=mime.get_content_type()
            )
        return obj

from email import message_from_bytes, message_from_string
from email.errors import HeaderDefect
from email.header import decode_header
from email.message import Message, EmailMessage
from email.policy import default, EmailPolicy
from email.utils import parseaddr, parsedate_to_datetime
from typing import Union, List, Optional
from parsed.mail.model import MailObject, BodyParts, EmailAddress, Header, MailFile, Body
from parsed.file.model import File
from parsed.mail.exceptions import ParseError
from parsed.enums import FileExtension
from parsed.utils import unzip_attachments, extract_p7m


def parse_mail_byte(
        mail_byte: bytes,
        policy: EmailPolicy = default
) -> Optional[MailObject]:
    """
        Parse a mime mail byte and return a MailObject
        :param mail_byte: the mail byte to parse
        :param policy: an email policy
        :return: a MailObject or None

        The policy keyword specifies a policy object that controls a number of
        aspects of the parser's operation.  The default policy maintains
        backward compatibility.

    """
    mime = message_from_bytes(mail_byte, policy=policy)
    return mime2Model(mime)


def parse_mail_string(
        mail_string: str,
        policy: EmailPolicy = default
) -> Optional[MailObject]:
    """
        Parse a mime mail byte and return a MailObject
        :param mail_string: the mail byte to parse
        :param policy: an email policy
        :return: a MailObject or None

        The policy keyword specifies a policy object that controls a number of
        aspects of the parser's operation.  The default policy maintains
        backward compatibility.

    """
    mime = message_from_string(mail_string, policy=policy)
    return mime2Model(mime)


def flatten_attachment(
        attachment: Union[File, list]
) -> Union[File, List[File]]:
    if isinstance(attachment, list):
        return list(map(flatten_attachment, attachment))
    match attachment.extension:
        case FileExtension.XML.value:
            content = attachment.content
            if isinstance(content, bytes):
                attachment.content = content.decode()
            return attachment
        case FileExtension.ZIP.value:
            return flatten_attachment(
                unzip_attachments(
                    attachment
                )
            )
        case FileExtension.P7M.value:
            return flatten_attachment(
                extract_p7m(
                    attachment
                )
            )
        case _:
            return attachment


def get_body(
        mail: Union[MailObject, BodyParts],
        tipe: str = "text/plain"
) -> Union[bytes, str]:
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


def transform_address(
        address: str
):
    address = parseaddr(address)
    return EmailAddress(
        nickname=address[0],
        address=address[1]
    )


def get_email_address(
        target: str
):
    if not target:
        return
    target = target.strip()
    target = target.replace("&lt;", "<").replace("&gt;", ">")
    addresses = target.split(";")
    addresses = list(map(transform_address, addresses))
    if len(addresses) == 1:
        return addresses[0]
    return addresses


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
    subject = ""
    if subject_header:
        encoded_tuple = decode_header(subject_header)[0]
        byte_subject = encoded_tuple[0]
        encoding = encoded_tuple[1]
        if encoding:
            subject = byte_subject.decode(encoding)
        else:
            subject = str(byte_subject)
    return subject


def get_date(
        mime: Union[Message, EmailMessage]
):
    date = mime.get(
        "date",
        mime.get("Date")
    )
    if date:
        return parsedate_to_datetime(date)


def parse_mail_header(
        mime: Union[Message, EmailMessage]
):
    sender = get_address(
        mime.get("From")
    )
    if not sender:
        raise HeaderDefect

    receivers = get_address(
        mime.get("To")
    )
    if not receivers:
        raise HeaderDefect

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


def get_attachment_and_body_parts(
        mime
):
    content, attachments = [], []
    if mime.is_multipart():
        for part in mime.get_payload():
            part = mime2Model(part)
            if isinstance(part, BodyParts):
                content.append(part)
            elif isinstance(part, (File, MailFile)):
                attachments.append(part)
            elif isinstance(part, list):
                attachments.extend(part)
    else:
        content.append(
            BodyParts(
                content=mime.get_content(),
                content_type=mime.get_content_type()
            )
        )
    return content, attachments


def get_mail_obj(
        mime: Union[EmailMessage, Message]
):
    header = parse_mail_header(mime)
    content, attachments = get_attachment_and_body_parts(mime)
    body = Body(
        content=content,
        attachments=attachments
    )
    return MailObject(
        header=header,
        body=body
    )


def get_mail(
        mime: Union[EmailMessage, Message]
) -> Optional[Union[MailObject, MailFile]]:
    try:
        filename = mime.get_filename(failobj="")
        if "eml" in filename or mime.get_content_type() == "message/rfc822":
            if mime.get_content_disposition() == "attachment":
                mime = mime.get_payload(0)
            mail_obj = get_mail_obj(mime)
            return MailFile(
                filename=filename or "email.eml",
                content=mime.as_bytes(),
                mail_obj=mail_obj,
                encoding=mime.get("Content-Transfer-encoding")
            )
        return get_mail_obj(mime)
    except ParseError:
        return
    except Exception:
        return


def mime_content(
        mime: Union[Message, EmailMessage],
        decode=True,
        **kwargs
) -> Optional[Union[EmailMessage, Message, str, bytes]]:
    try:
        return mime.get_content(**kwargs)
    except KeyError:
        return mime.get_payload(decode=decode, **kwargs)


def mime2Model(
        mime: Union[EmailMessage, Message]
) -> Optional[Union[list, MailObject, BodyParts]]:
    obj = get_mail(mime)
    if obj:
        return obj
    if mime.is_multipart() and not obj:
        return BodyParts(
            content=[
                mime2Model(part)
                for part in mime.get_payload()
            ],
            content_type=mime.get_content_type()
        )
    filename = mime.get_filename("")
    content = mime_content(mime)
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

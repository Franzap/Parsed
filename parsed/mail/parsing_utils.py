from email.header import decode_header
from email.message import Message, EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from typing import Union, List, Optional

from parsed.enums import FileExtension
from parsed.file.model import File
from parsed.mail.model import MailObject, BodyParts, EmailAddress
from parsed.utils import unzip_attachments, extract_p7m


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
                    name=address[0],
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


def mime_content(
        mime: Union[Message, EmailMessage],
        decode: bool = True,
        **kwargs
) -> Optional[Union[EmailMessage, Message, str, bytes]]:
    try:
        return mime.get_content(**kwargs)
    except (KeyError, AttributeError):
        return mime.get_payload(decode=decode, **kwargs)


def _has_surrogates(s):
    """Return True if s contains surrogate-escaped binary data."""
    # This check is based on the fact that unless there are surrogates, utf8
    # (Python's default encoding) can encode any string.  This is the fastest
    # way to check for surrogates, see issue 11454 for timings.
    try:
        s.encode()
        return False
    except UnicodeEncodeError:
        return True


def decode_payload(mime, payload):
    if _has_surrogates(payload):
        b_payload = payload.encode('ascii', 'surrogateescape')
        try:
            payload = b_payload.decode(mime.get_param('charset', 'ascii'), 'replace')
        except LookupError:
            payload = b_payload.decode('ascii', 'replace')
    return payload


def is_attachment(
        mime: Union[Message, EmailMessage]
) -> bool:
    c_d = mime.get_content_disposition()
    f_n = mime.get_filename()
    return c_d == 'attachment' or f_n

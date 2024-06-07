from email import message_from_bytes, message_from_string
from parsed.mail.exceptions import HeaderDefect
from email.header import decode_header
from email.message import Message, EmailMessage
from email.policy import default, EmailPolicy
from email.utils import parseaddr, parsedate_to_datetime
from typing import Union, List, Optional

from parsed.enums import FileExtension
from parsed.file.model import File
from parsed.mail.model import MailObject, BodyParts, EmailAddress, Header, MailFile, Body, FlattedBody
from parsed.utils import unzip_attachments, extract_p7m


def parse_mail_byte(
        mail_byte: bytes,
        policy: EmailPolicy = default,
        **kwargs
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
    return parse_mail_message(mime, **kwargs)


def parse_mail_string(
        mail_string: str,
        policy: EmailPolicy = default,
        **kwargs
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
    mime = message_from_string(mail_string, policy=policy, **kwargs)
    return parse_mail_message(mime, **kwargs)


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
        mime: Union[Message, EmailMessage],
        flatted: bool = False
):
    content, attachments = [], []
    for part in mime._payload:
        if part.is_multipart():
            if is_attachment(part):
                attachments.append(
                    parse_mail_attachment(part)
                )
            else:
                if not flatted:
                    content.append(
                        parse_multipart_mime(part)
                    )
                else:
                    parse_multipart_mime(part, ref=content)
        else:
            if is_attachment(part):
                attachments.append(
                    parse_mime_attachment(part)
                )
            else:
                content.append(
                    BodyParts(
                        content=mime_content(part),
                        content_type=part.get_content_type()
                    )
                )
    return content, attachments


def parse_mail_message(
        mime: Union[EmailMessage, Message],
        flatted: bool = False
) -> Optional[Union[MailObject, MailFile]]:
    """
        Parse a Message or EmailMessage object to a MailObject or MailFile object
        :param mime: Message or EmailMessage object
        :param flatted: Boolean indicating if the MailObject created must be flatted or in full depths
        :return: MailObject or MailFile object
    """

    header = parse_mail_header(mime)
    content, attachments = get_attachment_and_body_parts(mime, flatted)
    text_body = ""
    html_body = ""
    inline_file = []
    for element in content:
        if isinstance(element, (File, MailFile)):
            inline_file.append(element)
        elif element.content_type == "text/plain":
            text_body += element.content
        elif element.content_type == "text/html":
            html_body += element.content

    body = FlattedBody(
        text_body=text_body,
        html_body=html_body,
        inline_file=inline_file,
        attachments=attachments
    )
    return MailObject(
        header=header,
        body=body
    )


def parse_mail_attachment(
        mime: Union[Message, EmailMessage]
):
    filename = mime.get_filename(failobj="email.eml")
    mime = mime._payload[0]
    mail_obj = parse_mail_message(mime)
    return MailFile(
        filename=filename,
        content=mime.as_bytes(),
        parsed_obj=mail_obj,
        encoding=mime.get("Content-Transfer-encoding")
    )


def mime_content(
        mime: Union[Message, EmailMessage],
        decode: bool = True,
        **kwargs
) -> Optional[Union[EmailMessage, Message, str, bytes]]:
    try:
        return mime.get_content(**kwargs)
    except KeyError:
        return mime.get_payload(decode=decode, **kwargs)


def parse_multipart_mime(
        mime: Union[Message, EmailMessage],
        ref: Optional[list] = None
) -> Optional[BodyParts]:
    if ref is not None:
        for part in mime._payload:
            model = mime_to_model(part, ref=ref)
            if model:
                ref.append(model)
    else:
        return BodyParts(
            content=list(
                map(mime_to_model, mime._payload)
            ),
            content_type=mime.get_content_type()
        )


def parse_mime_attachment(
        mime: Union[Message, EmailMessage],
        fold_attachment: bool = True
):
    filename = mime.get_filename(failobj="")
    content = mime_content(mime)
    obj = flatten_attachment(
        File(
            filename=filename,
            content=content,
            encoding=mime.get("Content-Transfer-Encoding")
        )
    )
    if fold_attachment and isinstance(obj, list):
        for i, attachment in enumerate(obj):
            if attachment.extension == FileExtension.MAIL.value:
                obj[i] = parse_mail_byte(attachment.content)
    return obj


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


def mime_to_model(
        mime: Union[EmailMessage, Message],
        fold_attachment: bool = True,
        ref: Optional[list] = None
):
    if mime.is_multipart():
        # Multipart-mime but not a mail
        return parse_multipart_mime(mime, ref)

    # Not multipart-mime

        # Case attachment or inline file
    if is_attachment(mime):
        return parse_mime_attachment(mime, fold_attachment)

        # str or html-str type
    return BodyParts(
        content=mime_content(mime),
        content_type=mime.get_content_type()
    )


def is_attachment(
        mime: Union[Message, EmailMessage]
) -> bool:
    c_d = mime.get_content_disposition()
    f_n = mime.get_filename()
    return c_d == 'attachment' or f_n

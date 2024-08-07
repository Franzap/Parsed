from email import message_from_bytes, message_from_string

from parsed.mail import Body
from parsed.mail.exceptions import HeaderDefect
from email.message import Message, EmailMessage
from email.policy import default, EmailPolicy
from typing import Union, Optional

from parsed.enums import FileExtension
from parsed.file.model import File
from parsed.mail.model import MailObject, BodyParts, Header, MailFile, FlattedBody
from parsed.mail.parsing_utils import mime_content, flatten_attachment, is_attachment, get_address, get_subject, \
    get_date


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


def parse_mail_header(
        mime: Union[Message, EmailMessage]
):
    sender = get_address(
        mime.get("From")
    )
    if not sender:
        raise HeaderDefect

    receivers = get_address(
        mime.get("To", mime.get("Delivered-To"))
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
    if mime.is_multipart():
        for part in mime._payload:
            if is_attachment(part):
                parsed_atts = parse_mime_attachment(part)
                if isinstance(parsed_atts, list):
                    attachments.extend(parsed_atts)
                else:
                    attachments.append(parsed_atts)
            else:
                if part.is_multipart():
                    if not flatted:
                        content.append(
                            parse_multipart_mime(part)
                        )
                    else:
                        parse_multipart_mime(part, ref=content)
                else:
                    content.append(
                        BodyParts(
                            content=mime_content(part),
                            content_type=part.get_content_type()
                        )
                    )
    else:
        if is_attachment(mime):
            att = parse_mime_attachment(mime)
            if isinstance(att, list):
                attachments.extend(att)
            else:
                attachments.append(att)
        else:
            content.append(
                BodyParts(
                    content=mime_content(mime),
                    content_type=mime.get_content_type()
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
    if flatted:
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
    else:
        body = Body(
            content=content,
            attachments=attachments
        )
    return MailObject(
        header=header,
        body=body
    )


def parse_mail_attachment(
        mime: Union[Message, EmailMessage]
) -> MailFile:
    filename = mime.get_filename(failobj="email.eml")
    mime = message_from_bytes(mime_content(mime))
    mail_obj = parse_mail_message(mime)
    return MailFile(
        filename=filename,
        content=mime.as_bytes(),
        parsed_obj=mail_obj,
        encoding=mime.get("Content-Transfer-encoding")
    )


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
) -> Union[list[Union[File, MailFile]], MailFile, File]:
    filename = mime.get_filename(failobj="")

    if "eml" in filename:
        obj = parse_mail_attachment(mime)
    else:
        obj = flatten_attachment(
            File(
                filename=filename,
                content=mime_content(mime),
                encoding=mime.get("Content-Transfer-Encoding")
            )
        )
    if fold_attachment and isinstance(obj, list):
        attachments = []
        for attachment in obj:
            if isinstance(attachment, list):
                attachments.extend(attachment)
        for attachment in attachments:
            if attachment.extension == FileExtension.MAIL.value:
                parse_mail_byte(attachment.content)
    return obj


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

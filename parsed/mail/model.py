from datetime import datetime
from typing import Optional, Union, List

from pydantic import BaseModel

from parsed.enums import FileExtension
from parsed.file.model import File, ParsableFile


class BodyParts(BaseModel):
    content: Union[List[Union['BodyParts', File, str]], str, bytes]
    content_type: Optional[str] = None


class Body(BaseModel):
    content: List[Union[BodyParts, File]]
    attachments: List[Union[File, 'MailFile']] = []

    def attachments_of_extension(self, extension: str) -> List['MailFile']:
        if self.attachments:
            return list(filter(lambda attachment: attachment.extension == extension, self.attachments))
        return []

    def mails(
            self,
            convert: bool = True
    ) -> Union[List['MailObject'], List['MailFile']]:
        mails = self.attachments_of_extension(FileExtension.MAIL.value)
        if mails:
            if convert:
                return list(map(lambda mail: mail.parsed_obj, mails))
        return mails


class FlattedBody(BaseModel):
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    inline_file: Optional[List[Union[File, 'MailFile']]] = []
    attachments: Optional[List[Union[File, 'MailFile']]] = []


class EmailAddress(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

    def __str__(self):
        return self.address


class Header(BaseModel):
    From: EmailAddress
    To: Union[List[EmailAddress], EmailAddress]
    Cc: Optional[Union[List[EmailAddress], EmailAddress]] = None
    Received: Optional[Union[datetime, str]] = None
    Subject: Optional[str] = None


class MailObject(BaseModel):
    """
    # HEADER
        FROM:
            the person sending the mail **the mail comes from a single person **
        TO:
            list of people who can receive the mail
        CC:
            list of people who can be cc'd on the mail
        SUBJECT:
            Subject of the mail
        RECEIVED:
            date and time when the email was received

    # MAIL
        BODY:
            text with inline images (select whether to include or not)
        ATTACHMENTS:
            these are the attachments of the mail, which can vary between mail, zip, encrypted files, etc.

    # THREAD_ID:
        if a mail is part of a thread of mails, then thread_id will be set equals to the id of thread
        this means that every mail in thread will have the same ID
    """
    header: Header
    body: Union[Body, FlattedBody]
    thread_id: Optional[Union[str, int]] = None

    def __lt__(self, other):
        return self.header.Received < other.header.Received

    def __gt__(self, other):
        return self.header.Received > other.header.Received

    def __le__(self, other):
        return self.header.Received <= other.header.Received

    def __ge__(self, other):
        return self.header.Received >= other.header.Received

    def __eq__(self, other):
        return self.header.Received == other.header.Received

    def __ne__(self, other):
        return self.header.Received != other.header.Received


class MailFile(ParsableFile):
    parsed_obj: MailObject

    def __init__(self, file: Optional[File] = None, **kwargs) -> None:
        if file is None:
            super().__init__(**kwargs)
        else:
            super().__init__(**file.dict(), **kwargs)


BodyParts.update_forward_refs()
Body.update_forward_refs()

"""
MAIL

######### HEADER DELLA MAIL
    FROM: PERSONA CHE INVIA LA MAIL **LA MAIL PROVIENE DA UNA E UNA SOLA PERSONA **
    TO: LISTA DI PERSONE CHE PUO RICEVERE O MENO LA MAIL INVIATA
    CC: LISTA DI PERSONE CHE PUÒ ESSERE IN CC ALLA MAIL INVIATA
    SUBJECT: SOGGETTO DELLA MAIL
    RECEIVED: DATETIME CHE RAPPRESENTA QUANDO L'EMAIL È RICEVUTA

######### BODY DELLA MAIL

BODY: TESTUALE CON IMMAGINI INLINE (SCELTA TRA INCLUDERE O MENO LE IMMAGINI)

ATTACHMENTS: SONO ALLEGATI DELLA MAIL, CHE POSSONO VARIARE TRA MAIL, ZIP, FILE CRIPTATI ECC

OPTIONAL

THREAD: OGGETTO ESTERNO CHE CONTIENE TUTTE LE MAIL CHE FANNO PARTE DI UN DETERMINATO THREAD
"""

from datetime import datetime
from typing import Optional, Union, List
from pydantic import BaseModel, computed_field
from os.path import splitext
from parsed.enums import FileExtension


class File(BaseModel):
    filename: str
    content: Optional[Union[str, bytes]] = None
    encoding: Optional[str] = None

    @computed_field
    @property
    def extension(self) -> str:
        return splitext(self.filename)[-1].lower()


class BodyParts(BaseModel):
    content: Union[List[Union['BodyParts', File, str]], str, bytes]
    content_type: Optional[str] = None


class Body(BaseModel):
    content: List[BodyParts]
    attachments: Optional[List[Union[File, 'MailFile']]] = None

    def attachments_of_extension(self, extension: str) -> List['MailFile']:
        if self.attachments:
            return list(filter(lambda attachment: attachment.extension == extension, self.attachments))
        return []

    def mails(self, convert: bool = True) -> Union[List['MailObject'], List['MailFile']]:
        mails = self.attachments_of_extension(FileExtension.MAIL.value)
        if mails:
            if convert:
                return list(map(lambda mail: mail.mail_obj, mails))
        return mails


class EmailAddress(BaseModel):
    name: Optional[str] = None
    address: str

    def __str__(self):
        return self.address


class Header(BaseModel):
    From: EmailAddress
    To: Union[List[EmailAddress], EmailAddress]
    Cc: Optional[Union[List[EmailAddress], EmailAddress]] = None
    Received: Optional[Union[datetime, str]] = None
    Subject: Optional[str] = None


class MailObject(BaseModel):
    header: Header
    body: Body
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


class MailFile(File, BaseModel):
    mail_obj: MailObject

    def __init__(self, file: Optional[File] = None, **kwargs) -> None:
        if file is None:
            super().__init__(**kwargs)
        else:
            super().__init__(**file.dict(), **kwargs)


BodyParts.update_forward_refs()
Body.update_forward_refs()

from typing import Union, List, Optional
from pydantic import BaseModel
from parsed.mail import MailObject, MailFile


class MailThread(BaseModel):
    """
        Represents a mail thread
    """
    thread: List[Union[MailObject, MailFile]] = []
    ordered: bool = False
    id: Optional[Union[str, int]] = None

    def sort(self, reverse: bool = False):
        self.thread.sort(reverse=reverse)
        self.ordered = True

    def __len__(self):
        return len(self.thread)

    def add_mail(self, mail: Union[MailObject, MailFile]):
        mail.thread_id = self.id
        self.thread.append(mail)

    def add_mails(self, mails: List[MailObject]):
        for mail in mails:
            mail.thread_id = self.id
        self.thread.extend(mails)

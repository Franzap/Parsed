from typing import Union, List

from pydantic import BaseModel

from mail_parsing.mail_parser import MailObject, MailFile


class MailThread(BaseModel):
    thread: List[Union[MailObject, MailFile]] = []
    ordered: bool = False

    def sort(self, reverse: bool = False):
        self.thread.sort(
            reverse=reverse
        )
        self.ordered = True

    def __len__(self):
        return len(self.thread)

    def add_mail(self, mail: Union[List[MailObject], MailObject,MailFile]):
        if isinstance(mail, list):
            self.thread.extend(mail)
        else:
            self.thread.append(mail)

from email.headerregistry import Address
from email.message import EmailMessage

from parsed.mail import MailObject, EmailAddress
from parsed.mail.model import FlattedBody


class ConverterToEmailMessage:
    def convert(self, mail: MailObject) -> EmailMessage:
        email_message = EmailMessage()
        email_message["To"] = self.convertAddressHeader(mail.header.To)
        email_message["From"] = self.convertAddressHeader(mail.header.From)
        email_message["Subject"] = mail.header.Subject
        # email_message["Cc"] = self.convertAddressHeader(mail.header.Cc)
        if isinstance(mail.body, FlattedBody):
            email_message.set_content(mail.body.text_body)
            email_message.add_alternative(mail.body.html_body)
        else:
            email_message.set_content(mail.body)
        return email_message

    def convertAddressHeader(self, header):
        if isinstance(header, list):
            return [self._EmailAddressToAddress(address)
                    for address in header
                    ]
        else:
            return self._EmailAddressToAddress(header)

    def _EmailAddressToAddress(self, addr: EmailAddress) -> Address:
        username, domain = addr.address.split("@")
        return Address(
            display_name=addr.name or "",
            username=username,
            domain=domain
        )

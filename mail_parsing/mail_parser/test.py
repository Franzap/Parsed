import os

from mail_parsing.mail_parser import parse_mail_byte, MailFile, FileExtension
from mail_parsing.mail_parser.thread import create_thread_from_mail

if __name__ == '__main__':
    archive = "../../esempi_mail_full"
    for mail_dir in os.listdir(archive):
        mail_dir = os.path.join(archive, mail_dir)
        for file in os.listdir(mail_dir):
            if os.path.splitext(file)[-1] == FileExtension.MAIL.value:
                with open(os.path.join(mail_dir, file), mode="rb") as eml:
                    byte = eml.read()
                mail = parse_mail_byte(byte)
                mail_thread = create_thread_from_mail(mail)

                print()

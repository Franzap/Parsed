import os

from parsed.enums import FileExtension
from parsed.thread import create_thread_from_mail
from parsed.mail.parser import parse_mail_byte

if __name__ == '__main__':
    archive = "../resources/esempi_mail_full"
    for mail_dir in os.listdir(archive):
        mail_dir = os.path.join(archive, mail_dir)
        for file in os.listdir(mail_dir):
            if os.path.splitext(file)[-1] == FileExtension.MAIL.value:
                with open(os.path.join(mail_dir, file), mode="rb") as eml:
                    byte = eml.read()
                mail = parse_mail_byte(byte)
                mail_thread = create_thread_from_mail(mail)
                print()

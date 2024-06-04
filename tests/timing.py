import os
import time
import timeit
from parsed.enums import FileExtension
from parsed.mail.parser import parse_mail_byte
from parsed.thread import thread_from_mail

if __name__ == '__main__':
    archive = "../resources/esempi_mail_full"
    for mail_dir in os.listdir(archive):
        mail_dir = os.path.join(archive, mail_dir)
        for file in os.listdir(mail_dir):
            if os.path.splitext(file)[-1] == FileExtension.MAIL.value:
                with open(os.path.join(mail_dir, file), mode="rb") as eml:
                    byte = eml.read()
                t1 = time.perf_counter()
                mail = parse_mail_byte(byte)
                t2 = time.perf_counter()
                print("time: {:.2f}s".format(t2 - t1))
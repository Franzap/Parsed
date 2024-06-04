import math
import os
import pickle
import time
import timeit
from statistics import mean

from parsed.enums import FileExtension
from parsed.mail.parser import parse_mail_byte
from parsed.thread import thread_from_mail

if __name__ == '__main__':
    archive = "../resources/esempi_mail_full"
    with open(
        "/home/franzap/Desktop/Parsed/resources/ATTI_MIME.pkl",
        "rb"
    ) as f:
        data= pickle.load(f)
    times = []
    for byte in data:
        t1 = time.perf_counter()
        mail = parse_mail_byte(byte)
        t2 = time.perf_counter()
        times.append(t2-t1)
    print(min(times), max(times), mean(times))
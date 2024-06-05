import io
import os
import subprocess
from datetime import datetime
from os.path import splitext as os_split_extension
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from parsed.file.model import File


def extract_p7m(
        attachment: File
):
    with NamedTemporaryFile(suffix=attachment.extension) as temp_file:
        temp_file.write(attachment.content)
        command = f"openssl smime -verify -noverify -in {temp_file.name} -inform DER"
        out = subprocess.run(command, shell=True, check=True, capture_output=True)
    attachment.content = out.stdout or ""
    attachment.filename = os_split_extension(attachment.filename)[0]
    return attachment


def unzip_attachments(
        attachment: File
):
    attachments = []
    with ZipFile(io.BytesIO(attachment.content)) as zip_ref:
        for sub_file in zip_ref.filelist:
            extraction_path = zip_ref.extract(sub_file)
            # @TODO WE HAVE TO HANDLE WHEN THEN EXTRACTED ELEMENT IS A DIRECTORY AND
            #  TAKE ALL THE FILE OUT OF IT
            if os.path.isdir(extraction_path):
                # the extracted element is a directory and we have to visit it
                ...
            else:
                with open(
                        extraction_path,
                        "rb"
                ) as f:
                    content = f.read()

                attachments.append(
                    File(
                        filename=sub_file.filename,
                        content_type=f"application/{sub_file.filename.split('.')[-1]}",
                        content=content,
                        encoding=None
                    )
                )
                os.remove(extraction_path)
    return attachments


weekday = {
    "lunedì": "monday",
    "martedì": "tuesday",
    "mercoledì": "wednesday",
    "giovedì": "thursday",
    "venerdì": "friday",
    "sabato": "saturday",
    "domenica": "sunday"
}
months = {
    "gennaio": "january",
    "febbraio": "february",
    "marzo": "march",
    "aprile": "april",
    "maggio": "may",
    "giugno": "june",
    "luglio": "july",
    "agosto": "august",
    "settembre": "september",
    "ottobre": "october",
    "novembre": "november",
    "dicembre": "december"
}


def replace_datetime_piece(datetime_string: str):
    for mesi in months.items():
        datetime_string = datetime_string.replace(*mesi)
    for giorni in weekday.items():
        datetime_string = datetime_string.replace(*giorni)
    return datetime_string


def strp_ita_string(datetime_string: str, _format: str = "%A %d %B %Y %H:%M"):
    datetime_string = replace_datetime_piece(datetime_string)
    return datetime.strptime(datetime_string, _format)

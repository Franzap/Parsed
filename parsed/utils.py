import subprocess
from tempfile import NamedTemporaryFile
from typing import List, Union, Optional
from zipfile import ZipFile
import io
import os
from os.path import splitext as os_split_extension
from parsed.enums import FileExtension
from parsed.mail.model import File
from datetime import datetime


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


def flatten_attachment(
        attachment: Union[File, list]
) -> Union[File, List[File]]:
    if isinstance(attachment, list):
        return [
            flatten_attachment(att)
            for att in attachment
        ]
    match attachment.extension:
        case FileExtension.XML.value:
            content = attachment.content
            if isinstance(content, bytes):
                attachment.content = content.decode()
            return attachment
        case FileExtension.ZIP.value:
            return flatten_attachment(
                unzip_attachments(
                    attachment
                )
            )
        case FileExtension.P7M.value:
            return flatten_attachment(
                extract_p7m(
                    attachment
                )
            )
        case _:
            return attachment


def substring_from_guardians(
        first: Optional[str],
        second: Optional[str],
        string: str
):
    if first is not None:
        first_index = string.find(first)
        if first_index == -1:
            return None
        string = string[first_index + (len(first)):]
    if second is None:
        return string
    second_index = string.find(second)
    if second_index == -1:
        return None
    return string[:second_index]



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

from enum import Enum


class FileExtension(Enum):
    MAIL = ".eml"
    P7M = ".p7m"
    PDF = ".pdf"
    TXT = ".txt"
    XML = ".xml"
    ZIP = ".zip"


class MimeTypes(Enum):
    PLAIN = "text/plain"
    HTML = "text/html"
    JPG = "image/jpeg"
    JPEG = "image/jpeg"
    PNG = "image/png"
    TIFF = "image/tiff"
    WEBP = "image/webp"
    WEBPX = "image/webpx"
    TIFFX = "image/tiffx"
    PNGX = "image/pngx"
    JPEGX = "image/jpegx"

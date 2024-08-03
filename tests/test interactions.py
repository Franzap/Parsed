import smtplib
from parsed.converters.toEmailMessage import ConverterToEmailMessage
from parsed.mail.parser import parse_mail_byte

# Configurazione dei dettagli del server SMTP
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = "tuoindirizzo@gmail.com"
smtp_password = "tuapassword"

with open(
    r"C:\Users\franc\Desktop\Parsed\tests\resources\Prontobus - Conferma prenotazione.eml",
    "rb"
)as f:
    byte = f.read()


msg = parse_mail_byte(byte, flatted=True)
msg1 = ConverterToEmailMessage().convert(msg)

# Connessione al server SMTP
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()  # Avvio della modalità TLS (sicurezza)
    server.login(smtp_user, smtp_password)  # Login al server
    server.sendmail(msg["From"], msg["To"], msg.as_string())  # Invio dell'email

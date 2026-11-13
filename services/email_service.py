from config import Config


def send_security_code_via_email(to_email, code):
    # TODO: integrar un servicio real de correo electrónico como SendGrid, Mailgun o SMTP
    print(f"Enviar código {code} a {to_email}")


def send_security_code_via_sms(phone_number, code):
    if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN or not Config.TWILIO_PHONE_NUMBER:
        print('Twilio no configurado. Usar terminal para ver código.')
        print(f"Código de verificación {code} para {phone_number}")
        return False

    try:
        from twilio.rest import Client
    except ImportError:
        print('La librería twilio no está instalada. Instala twilio con pip.')
        print(f"Código de verificación {code} para {phone_number}")
        return False

    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=f'Tu código de verificación es {code}',
            from_=Config.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
        print(f'SMS enviado a {phone_number}, SID {message.sid}')
        return True
    except Exception as exc:
        print(f'Error enviando SMS a {phone_number}: {exc}')
        print(f"Código de verificación {code} para {phone_number}")
        return False

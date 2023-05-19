import smtplib

from email.message import EmailMessage
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)


def send_email(request, email_msg):
    msg = EmailMessage()
    msg['Subject'] = email_msg['subject']
    msg['From'] = config('SENDER_MAIL', default='')
    msg['To'] = email_msg['to']
    msg.set_content(email_msg['message'])

    # Send the mail

    server = smtplib.SMTP_SSL(host=config('EMAIL_HOST', default=''), port=config('EMAIL_PORT', default=''))
    server.login(config('EMAIL_HOST_USER', default=''), config('EMAIL_HOST_PASSWORD', default=''))
    # server.sendmail(FROM, TO, message.encode('utf-8'))
    server.send_message(msg)
    server.quit()

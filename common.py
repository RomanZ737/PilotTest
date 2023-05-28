import smtplib

from email.message import EmailMessage
from email.utils import make_msgid
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
import os

krs_mail_list = ['pomanz@mail.ru', 'roman.v@zfamily.aero']  #  Список адресов для рассылки сообщений КРС


def send_email(request, email_msg):
    # email_msg: словарь с содержанием: {'subject': subject, 'message': message, 'to': request.user.email}
    msg = EmailMessage()
    msg['Subject'] = email_msg['subject']
    msg['From'] = config('SENDER_MAIL', default='')
    msg['To'] = email_msg['to']
    msg.set_content(email_msg['message'])

    # Делаем альтернативную версию HTML
    logo_cid = make_msgid()
    msg.add_alternative("""
    <html>
        <head>
            <img src="cid:{nws_logo}" width="270" height="80">
      </head>
      <body>
        <p>{message}</p>
      </body>
    </html>
    """.format(message=email_msg['message'], nws_logo=logo_cid[1:-1]), subtype='html')
    # note that we needed to peel the <> off the msgid for use in the html.

    # Now add the related image to the html part.
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    with open(dir_path + '/PilotTest/static/nws_logo_white.jpg', 'rb') as img:
        msg.get_payload()[1].add_related(img.read(), 'image', 'jpg',
                                         cid=logo_cid)

    # Send the mail

    server = smtplib.SMTP_SSL(host=config('EMAIL_HOST', default=''), port=config('EMAIL_PORT', default=''))
    server.login(config('EMAIL_HOST_USER', default=''), config('EMAIL_HOST_PASSWORD', default=''))
    # server.sendmail(FROM, TO, message.encode('utf-8'))
    server.send_message(msg)
    server.quit()

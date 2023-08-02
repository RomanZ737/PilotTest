import smtplib, ssl

from email.message import EmailMessage
from email.utils import make_msgid
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
import os


krs_mail_list = ['pomanz@mail.ru', '733.roman@gmail.com']
#krs_mail_list = ['r.zaychenko@nordwindairlines.ru', 'd.dolgov@nordwindairlines.ru', 'p.leshchinskiy@nordwindairlines.ru', 's.samoylov@nordwindairlines.ru']  #  Список адресов для рассылки сообщений КРС
fixed_groups = ['KRS', 'ВП B737', 'КВС B737', 'ПИ B737', 'Редактор', 'ВП B777', 'КВС B777', 'ПИ B777', 'ВП A32X', 'КВС A32X', 'ПИ A32X', 'ВП A33X', 'КВС A33X', 'ПИ A33X']  # Фиксированные группы, пользователи не могут удалять
days_left_notify = 5  # Количество дней за которое информировать пользователя до истечения срока сдачи теста


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
    <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=koi8-r">
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns="http://www.w3.org/TR/REC-html40">

        <head>
            <meta name=Generator content="Microsoft Word 15 (filtered medium)">
            <xml>
                <o:shapedefaults v:ext="edit" spidmax="1026" />
            </xml><![endif]--><!--[if gte mso 9]>
            <xml>
                <o:shapelayout v:ext="edit">
                <o:idmap v:ext="edit" data="1" />
                </o:shapelayout>
            </xml><![endif]-->
        </head>
      <body lang=RU link="#0563C1" vlink="#954F72" style='word-wrap:break-word'>
        <div class=WordSection1>
                <div><p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;">
                    {message}
                    <p class=MsoNormal>
                    <span style='font-size:10.0pt'>&nbsp;</span><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;"><b>
                    <span style='font-size:10.0pt;font-family:"Arial",sans-serif;color:gray'>&nbsp;</span></b><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;"><b>
                    <span style='font-size:10.0pt;font-family:"Arial",sans-serif;color:gray'>Pilot Test</span></b><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif; 'line-height:115%';">
                    <span style='font-size:10.0pt;line-height:115%;font-family:"Arial",sans-serif;color:gray'>Система тестирования лётного состава</span><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;"><b><span lang=EN-US style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'>LLC Nordwind&nbsp;</span></b><b>
                    <span style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'> |</span></b><b>
                    <span lang=EN-US style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'>&nbsp;&nbsp;</span></b>
                    <a href="http://www.nordwindairlines.ru/" target="_BLANK">
                        <span lang=EN-US style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'>nordwindairlines</span>
                        <span style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'>.</span>
                        <span lang=EN-US style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'>ru</span>
                    </a>
                    <span lang=EN-US style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'>&nbsp;&nbsp;</span>
                    <span style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#747678'>| </span><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;"><span lang=EN-US style='font-size:10.0pt;font-family:"Arial",sans-serif;color:#1F497D'>&nbsp;</span>
                    <span style='color:#1F497D'><img border=0 width=399 height=38 style='width:4.1583in;height:.4in' src="cid:{nws_logo}"></span><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;"><span style='font-size:8.0pt;font-family:"Arial",sans-serif;color:gray'>&nbsp;</span><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;" 'background:white';"><span style='font-size:8.0pt;font-family:"Arial",sans-serif;color:#999999'>ООО &laquo;Северный Ветер&raquo;</span><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;"><span style='font-size:8.0pt;font-family:"Arial",sans-serif;color:#999999'>125319, г. Москва, вн. тер. г. Муниципальный округ Аэропорт, ул. Коккинаки, д. 4, помещ. 2/1</span><o:p></o:p></p>
                <p style="margin:0cm; font-size:11.0pt; font-family:'Calibri',sans-serif;">&nbsp;<o:p></o:p></p>
            </div>
        </div>
    </body>
    </html>
    """.format(message=email_msg['message'], nws_logo=logo_cid[1:-1]), subtype='html')
    # note that we needed to peel the <> off the msgid for use in the html.

    # Now add the related image to the html part.
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    with open(dir_path + '/PilotTest/static/letter_logo.png', 'rb') as img:
        msg.get_payload()[1].add_related(img.read(), 'image', 'jpg',
                                         cid=logo_cid)

    # Send the mail
    context = ssl.create_default_context()
    server = smtplib.SMTP(host=config('EMAIL_HOST', default=''), port=config('EMAIL_PORT', default=''))
    server.connect(host=config('EMAIL_HOST', default=''), port=config('EMAIL_PORT', default=''))
    server.ehlo()  # Can be omitted
    server.starttls()  # Secure the connection
    server.ehlo()  # Can be omitted
    #-----------------------
    #server = smtplib.SMTP_SSL(host=config('EMAIL_HOST', default=''), port=config('EMAIL_PORT', default=''))
    # -----------------------
    server.login(config('EMAIL_HOST_USER', default=''), config('EMAIL_HOST_PASSWORD', default=''))
    # server.sendmail(FROM, TO, message.encode('utf-8'))
    server.send_message(msg)
    server.quit()

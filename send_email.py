import smtplib, ssl
import config

from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText


def verification_code(receiver_email, code):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = config.sender_email  # Enter your address
    password = config.email_password
    msg = MIMEText(str(code))

    msg['Subject'] = "Verification Code"
    msg['From'] = formataddr((str(Header(config.name, 'utf-8')), config.sender_email))
    msg['To'] = receiver_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Successfully sent email")
    except:
        print("Error: unable to send email")


def registered(receiver_email):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = config.sender_email  # Enter your address
    password = config.email_password
    msg = MIMEText(str('Thank you for joining our community and registering with us. \n \nBest regards!\nThe {} team'.format(config.name)))

    msg['Subject'] = "Welcome to TEA"
    msg['From'] = formataddr((str(Header(config.name, 'utf-8')), config.sender_email))
    msg['To'] = receiver_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Successfully sent email")
    except:
        print("Error: unable to send email")


def changed_password(receiver_email):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = config.sender_email  # Enter your address
    password = config.email_password
    msg = MIMEText(str('Your password has been changed, if you did not change it, please contact us via this email: {}. \n \nBest regards!\nThe {} team'.format(
                    config.sender_email, config.name)))

    msg['Subject'] = "Your password has been changed"
    msg['From'] = formataddr((str(Header(config.name, 'utf-8')), config.sender_email))
    msg['To'] = receiver_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Successfully sent email")
    except:
        print("Error: unable to send email")

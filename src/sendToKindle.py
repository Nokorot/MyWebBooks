#!/usr/bin/python3

import smtplib #importing the module
import sys, os

from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def sendToKindle(sender='lisathelibrarian2000@gmail.com', receiver=None, file=None, target_filename=None):
    load_dotenv()
    if not receiver or not file:
        return

    password = os.environ.get("GMAIL_PASSWORD")
    print(password)

    message = constructMessage(sender, receiver, file, target_filename)
    sendEmail(sender, password, receiver, message)


def constructMessage(sender_add, receiver_add, file, target_filename=None):
    message = MIMEMultipart()

    if not target_filename:
        target_filename = file

    message["From"] = sender_add
    message['To'] = receiver_add
    message['Subject'] = f"Your book {target_filename} has arrived!"

    attach = open(file, "rb")

    obj = MIMEBase('application','octet-stream')

    obj.set_payload((attach).read())
    encoders.encode_base64(obj)
    obj.add_header('Content-Disposition',"attachment; filename= "+target_filename)

    message.attach(obj)
    attach.close()
    return message.as_string()

def sendEmail(sender_add, password, receiver_add, message):
    #creating the SMTP server object by giving SMTP server address and port number
    smtp_server=smtplib.SMTP_SSL("smtp.gmail.com",465)

    smtp_server.login(sender_add,password)

    smtp_server.sendmail(sender_add, receiver_add, message)
    print('Successfully the mail is sent')

    smtp_server.quit() #terminating the server

def usage(prg):
    print(f"Usage: {prg} <file>")
    print("")
    print("Send a file to my kinlde using email!")


if __name__ == '__main__':
    if (sys.argv[1] == '--help'):
        usage(sys.argv[0])
        sys.exit(0)

    if len(sys.argv) < 2:
        print("ERR: No enough arguments!")
        usage()
        sys.exit(1)

    sendToKindle(sys.argv[1])

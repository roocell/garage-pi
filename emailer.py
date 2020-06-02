import smtplib
#import multiprocessing
import os, sys
#multiprocessing.set_start_method('spawn')

#Email Variables
SMTP_SERVER = 'smtp.gmail.com' #Email Server (don't change!)
SMTP_PORT = 587 #Server Port (don't change!)
GMAIL_USERNAME = 'XXXXXXX@gmail.com' #change this to match your gmail account
GMAIL_PASSWORD = 'XXXXXXXX'  #change this to match your gmail password

DEFAULT_DESTINATION = "xxxx@gmail.com"


class Emailer:
    def sendmail_subprocess(self, recipient, subject, content):

        #Create Headers
        headers = ["From: " + GMAIL_USERNAME, "Subject: " + subject, "To: " + recipient,
                   "MIME-Version: 1.0", "Content-Type: text/html"]
        headers = "\r\n".join(headers)

        #Connect to Gmail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()

        #Login to Gmail
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)

        #Send Email & Exit
        session.sendmail(GMAIL_USERNAME, recipient, headers + "\r\n\r\n" + content)
        session.quit

    # there's a bug using smtplib with eventlet
    # TypeError: wrap_socket() got an unexpected keyword argument '_context'
    # spawning off another process is work around
    # choose spawn instead of fork - otherwise the eventlet monkeypatch gets inherited
    def sendmail(self, recipient, subject, content):
        #thread = multiprocessing.Process(target=Emailer.sendmail_subprocess, args=(self, recipient, subject, content,))
        #thread.start()

        if (recipient == ""):
            recipient = DEFAULT_DESTINATION
        # smtplib doesn't seem to work - just use msmtp on the command line
        cmd = "printf \"To: " + recipient + "\nFrom: pigarage-pi@gmail.com\nSubject: " + subject + "\n\n" + content + "\" | msmtp -a default " + recipient
        print(cmd)
        os.system(cmd)

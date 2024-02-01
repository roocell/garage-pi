import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess

#Email Variables
SMTP_SERVER = 'smtp.gmail.com' #Email Server (don't change!)
SMTP_PORT = 465 #Server Port (don't change!)
GMAIL_USERNAME = 'xxxx.xxxx@gmail.com' #change this to match your gmail account
GMAIL_PASSWORD = "xxxx"
#change this to match your gmail password

DEFAULT_DESTINATION = "xxxx@gmail.com"


class Emailer:

    def sendmail_smtp(self, subject, body, sender, recipients, password):
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = ', '.join(recipients)
        message['Subject'] = subject

        message.attach(MIMEText(body, 'plain'))

        try:
            smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipients, message.as_string())
            smtp_server.quit()
            print("Email sent successfully")
        except Exception as e:
            print("error ", e)

    # issues using smtplib with eventlet - so need to use command line
    def sendmail_cmd(self, sender, recipient, subject, body, password):
        # Construct the email content
        email_content = f"From: {sender}\nTo: {recipient}\nSubject: {subject}\n\n{body}"

        # Construct the curl command
        curl_command = [
            'curl',
            '--url', 'smtps://smtp.gmail.com:465',
            '--ssl-reqd',
            '--mail-from', sender,
            '--mail-rcpt', recipient,
            '--user', f'{sender}:{password}',
            '--upload-file', '-'
        ]

        # Execute the curl command and pass the email content as stdin
        try:
            subprocess.run(curl_command, input=email_content, text=True, check=True)
            print("Email sent successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error sending email: {e}")

    def sendmail(self, recipient, subject, body):
        self.sendmail_cmd(GMAIL_USERNAME, DEFAULT_DESTINATION, subject, body, GMAIL_PASSWORD)


if __name__ == '__main__':
  sender = Emailer()
  sender.sendmail("", "test subject", "test content")
   

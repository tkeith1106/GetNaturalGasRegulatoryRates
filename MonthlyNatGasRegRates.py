import pandas as pd
import os
import requests
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, body):

    # setup email
    message = MIMEMultipart()
    message["To"] = 'tkeith1106@gmail.com'
    message["From"] = 'RegulateRateEmailer@noreply.com'
    message["Subject"] = f'{subject}'

    messageText = MIMEText(body, 'html')
    message.attach(messageText)

    email = 'tkeith1106@gmail.com'
    password = 'zandunnepeedgtgt'

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo('Gmail')
    server.starttls()
    server.login(email, password)
    fromaddr = 'Python Script'
    toaddrs = 'tkeith1106@gmail.com'
    server.sendmail(fromaddr, toaddrs, message.as_string())

    server.quit()


# init variables
tables = []
regulated_rates = None

# create the requests
url = 'https://ucahelps.alberta.ca/regulated-rates.aspx'
r = requests.get(url, verify=False)

# create the pandas df
all_tables = pd.read_html(r.text)

# export tables to dictionaries
for item in all_tables:
    tables.append(item.to_dict(orient="index"))

# parse through dictionaries for the current year natural gas rate
for table in tables:
    # look for current months value
    if f"{datetime.datetime.now().strftime('%Y')} Natural Gas".lower() in table[0][0].lower():
        rate_type = table[0][0]
        month = table[(len(table) -1)][0]
        value = table[(len(table) -1)][1]
        regulated_rates = f"{rate_type} for {month} is {value}"

        rate_sent_file = f"C:\\Users\\tkeith\\Documents\\Python\\GetNatGasRegRate\\{month}_{value.replace('.', '_')}.txt"
        if not os.path.exists(rate_sent_file):
            send_email(subject=regulated_rates, body=regulated_rates)

            with open(rate_sent_file, 'w') as file:
                file.write(regulated_rates)
                file.close()
if regulated_rates:
    print(regulated_rates)
else:
    print("No rates added to website yet!")
import pandas as pd
import os
import requests
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config

class GetNatGasRates:
    # init class variables
    def __init__(self, url: str=None, send_email: bool=False):

        # turn user args in vars
        self.url = url
        self.send_email = send_email

        # these are hidden behind a config file for privacy and security reasons
        self.email_to = config.email_to
        self.email_sender = config.email_sender
        self.email_secret_pass = config.email_secret_pass

        # derived vars and logic to set them up
        self.temp_data_loc = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\GetNatGasRates"
        if not os.path.exists(self.temp_data_loc):
            os.makedirs(self.temp_data_loc)

    # init print out when object is printed
    def __str__(self):
        string = ""
        for k, v in self.__dict__.items():
            if k != "email_secret_pass":
                string += f"{k}='{v}';"
        return string

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        pass

    def run_tool(self):
        """
        The methods drive the main execution of the script
        :return: None
        """

        # get the rate_tables from user provided URL
        rate_tables = self.get_published_tables(self.url)

        # TODO: this could be made more dynamic for any URL with tables
        # parse through dictionaries for the current year natural gas rate
        for table in rate_tables:
            # look for current months value
            if f"{datetime.datetime.now().strftime('%Y')} Natural Gas".lower() in table[0][0].lower():
                rate_type = table[0][0]
                month = table[(len(table) - 1)][0]
                value = table[(len(table) - 1)][1]
                regulated_rates = f"{rate_type} for {month} is {value}"

                rate_sent_file = f"{self.temp_data_loc}\\{month}_{value.replace('.', '_')}.txt"
                if not os.path.exists(rate_sent_file):

                    if self.send_email:
                        self.emailer(subject=regulated_rates, body=regulated_rates)

                    with open(rate_sent_file, 'w') as file:
                        file.write(regulated_rates)
                        file.close()
        if regulated_rates:
            print(regulated_rates)
        else:
            print("No rates added to website yet!")

    def emailer(self, subject: str, body: str):
        """

        :param subject:
        :param body:
        :return:
        """

        # setup email
        message = MIMEMultipart()
        message["To"] = self.email_to
        message["From"] = self.email_sender
        message["Subject"] = f'{subject}'

        messageText = MIMEText(body, 'html')
        message.attach(messageText)

        email = self.email_to
        password = self.email_secret_pass

        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(email, password)
        server.sendmail(self.email_sender, self.email_to, message.as_string())
        server.quit()

    @staticmethod
    def get_published_tables(url: str):
        """
        This method returns all html tables from a given url
        :return:
        """
        # init variables
        tables = []
        regulated_rates = None

        # create the requests do not verify ssl TODO I should figure the SLL piece out
        r = requests.get(url, verify=False)

        # create the pandas df
        all_tables = pd.read_html(r.text)

        # export tables to dictionaries
        for item in all_tables:
            tables.append(item.to_dict(orient="index"))

        return tables

    def purge_temp_folder(self):
        """
        This method empties the temporary folder
        :return: None
        """

        if os.path.exists(self.temp_data_loc):
            os.removedirs(self.temp_data_loc)
            os.makedirs(self.temp_data_loc)


if __name__ == "__main__":

    with GetNatGasRates(
            url=r'https://ucahelps.alberta.ca/regulated-rates.aspx',
            send_email=False,
    ) as tool:
        tool.purge_temp_folder()
        tool.run_tool()
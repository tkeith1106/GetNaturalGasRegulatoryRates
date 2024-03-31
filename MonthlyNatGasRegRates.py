import pandas as pd
import os
import requests
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config
import argparse

# cli arguments
parser = argparse.ArgumentParser()
parser.add_argument('--purgeTempData', action='store_false', dest='purgeTempData', help='This argument will purge any temporary files.')
parser.set_defaults(purgeTempData=False)
args = parser.parse_known_args()[0]


class GetNatGasRates:
    # init class variables
    def __init__(self, url: str = None, send_email: bool = False):

        # turn user args in vars
        self.url = url
        self.send_email = send_email

        # these are hidden behind a config file for privacy and security reasons
        self.email_bcc_to = config.email_bcc_to
        self.email_main = config.email_main
        self.email_sender = config.email_sender
        self.email_secret_pass = config.email_secret_pass

        # derived vars and logic to set them up
        self.temp_data_loc = "./TempFiles"
        self.create_temp_folder()

    # init print out when object is printed
    def __str__(self) -> str:
        string = ""
        for k, v in self.__dict__.items():
            if k != "email_secret_pass":
                string += f"{k}='{v}';"
        return string

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace) -> None:
        # haven't decided what I want to do on exit yet
        pass

    def run_tool(self) -> None:
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
            if f"{datetime.datetime.now().strftime('%Y')}" and "Natural Gas".lower() in table[0][0].lower():
                rate_type = table[0][0]
                month = table[(len(table) - 1)][0]
                value = table[(len(table) - 1)][1]
                regulated_rates = f"{rate_type} for {month} is {value}"

                rate_sent_file = os.path.join(self.temp_data_loc, f"{month}_{value.replace('.', '_')}.txt")
                if not os.path.exists(rate_sent_file):

                    if self.send_email:
                        self.emailer(subject=regulated_rates, body=regulated_rates)

                    with open(rate_sent_file, 'w') as file:
                        file.write(regulated_rates)
                        file.close()
                else:
                    print("No emails sent")
                break
        if 'regulated_rates' in locals():
            print(regulated_rates)
        else:
            print(f"No new rates parsed from website yet!")

    def emailer(self, subject: str, body: str) -> None:
        """
        This method sets up the email and sends it to the emails in the imported config file
        :param subject: string representing the email subject
        :param body: string representing the email body
        :return:None
        """

        # setup email
        message = MIMEMultipart()
        message["Bcc"] = ','.join(self.email_bcc_to)
        message["From"] = self.email_sender
        message["Subject"] = f'{subject}'

        message_text = MIMEText(body, 'html')
        message.attach(message_text)

        email = self.email_main
        password = self.email_secret_pass

        # # use below for gmail smtp
        # server = smtplib.SMTP('smtp.gmail.com:587')
        # server.ehlo('Gmail')

        # use below for iCloud SMTP
        server = smtplib.SMTP('smtp.mail.me.com:587')
        server.ehlo()

        server.starttls()
        server.login(email, password)
        server.sendmail(self.email_sender, self.email_bcc_to, message.as_string())
        server.quit()

    @staticmethod
    def get_published_tables(url: str) -> list:
        """
        This method returns all html tables from a given url
        :return:
        """
        # init variables
        tables = []

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

    def create_temp_folder(self) -> None:
        """
        This method ensures the temp folder exists anywhere it is run from
        :return: None
        """

        if not os.path.exists(self.temp_data_loc):
            os.makedirs(self.temp_data_loc)


if __name__ == "__main__":

    with GetNatGasRates(
            url=r'https://ucahelps.alberta.ca/regulated-rates.aspx',
            send_email=True,
    ) as tool:
        # if cli argument is flagged then it will delete all temp folder files and rebuild temp folder
        if args.purgeTempData:
            tool.purge_temp_folder()
        tool.run_tool()

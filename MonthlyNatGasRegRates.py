import argparse
import config
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
import os
import pandas as pd
import requests
import smtplib
from typing import Optional

# cli arguments
parser = argparse.ArgumentParser()
parser.add_argument('--purgeTempData', action='store_false', dest='purgeTempData', help='This argument will purge any temporary files.')
parser.set_defaults(purgeTempData=False)
args = parser.parse_known_args()[0]


class GetNatGasRates:
    # init class variables
    def __init__(self, send_email: bool = False):

        # turn user args in vars
        self.auc_rates_url = r"https://ucahelps.alberta.ca/regulated-rates.aspx"
        self.enmax_rates = r"https://www1.enmax.com/sign-up/build-my-plan"
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

    def execute(self) -> None:
        """
        The methods drive the main execution of the script
        :return: None
        """
        rate_sent_file = os.path.join(self.temp_data_loc, f"{datetime.datetime.now().strftime("%B").lower()}_rates.txt")
        if os.path.exists(rate_sent_file):
            print(f"No rate updates")
            return

        # get the rate_tables from user provided URL
        rate_tables = self.get_published_tables(self.auc_rates_url)
        if isinstance(rate_tables, list) and len(rate_tables) > 1:
            # generate the tables
            html_tables = self.generate_html_tables(rate_tables)

            if html_tables is not None:
                # create email body
                regulated_rates = f"""
                <body>
                <p>This months updated Electricity and Natural Gas Rates are Below:</p>
                {"".join(html_tables)}
                <br>
                <p>
                Visit Enmax for the most current Enmax Rates: <a href="{self.enmax_rates}">Current Enmax Easymax Rates</a>
                <br><br>
                Cheers, 
                <br>
                Python Automator
                </p>
                """

                if self.send_email:
                    self.emailer(subject=f"Updated energy rates as of {datetime.datetime.now().strftime("%B %d, %Y")}", body=regulated_rates)

                    with open(rate_sent_file, 'w') as file:
                        file.write(f"{regulated_rates}\n\n{"#"*25}\n{"#"*25}\n{"#"*25}\n\n")
                        file.close()
            else:
                print("No emails sent")

    @staticmethod
    def generate_html_tables(rate_tables: list[dict]) -> Optional[list[str]]:
        """
        This method generates the rates tables to be inserted in the email to the users
        :param rate_tables: a dictionary of rates scraped from the AUC
        :return: a List of html tables to be used in the email to be sent
        """

        html_tables = []

        year = f"{datetime.datetime.now().strftime('%Y')}"
        month = f"{datetime.datetime.now().strftime('%B')}"

        tbls_by_yr = []
        tbls_by_month = []

        for table in rate_tables:
            # look for current months nat gas value
            if year in table[0][0]:
                tbls_by_yr.append(table)

        for table in tbls_by_yr:
            if month in table[len(table)-1][0]:
                tbls_by_month.append(table)

        if len(tbls_by_month) != 2:
            return None

        for table in tbls_by_month:
            title = table[0][0]
            table.pop(0)
            html = "<h2>{title}</h2>\n<table style='border: 3px solid black; border-collapse: collapse;'>\n".format(
                title=title.encode('ascii', 'xmlcharrefreplace').decode())
            for key, row in table.items():
                if key in [0, 1, 2]:
                    html += "\t<tr style='border: 1px solid black'>\n\t"
                    if str(row[0]) == "nan":
                        continue
                    for index, data in row.items():
                        table_data = str(data).replace('nan', '').encode('ascii', 'xmlcharrefreplace').decode()
                        html += f"\t\t<td style='border: 1px solid black'>{table_data}</td>\n\t"
                    html += "</tr>\n"

            for key, row in reversed(table.items()):
                if key not in [0, 1, 2]:
                    html += "\t<tr style='border: 1px solid black'>\n\t"
                    if str(row[0]) == "nan":
                        continue
                    for index, data in row.items():
                        table_data = str(data).replace('nan', '').encode('ascii', 'xmlcharrefreplace').decode()
                        html += f"\t\t<td style='border: 1px solid black'>{table_data}</td>\n\t"
                    html += "</tr>\n"

            html += "</table>\n<br><br>"

            html_tables.append(html)

        return html_tables

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
        This method returns all html tables from a given auc_rates_url
        :return:
        """
        # init variables
        tables = []

        # create the requests do not verify ssl TODO I should figure the SLL piece out
        r = requests.get(url, verify=False)

        # create the pandas df
        all_tables = pd.read_html(StringIO(r.text))

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
            for files in os.listdir(self.temp_data_loc):
                os.remove(os.path.join(self.temp_data_loc, files))
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
            send_email=True,
    ) as tool:
        # if cli argument is flagged then it will delete all temp folder files and rebuild temp folder
        if args.purgeTempData:
            tool.purge_temp_folder()
        tool.execute()

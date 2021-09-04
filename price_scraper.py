from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from time import strftime
from apscheduler.schedulers.background import BackgroundScheduler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
import requests
import smtplib, ssl
import os
import time

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
email_password = ''

def send_email(game_title, game_price_data):
    port = 465 # SSL port
    email_from = 'melz.devacct@gmail.com'
    email_to = 'melz8bit@gmail.com'

    message = MIMEMultipart("alternative")
    message['Subject'] = game_title
    message['From'] = email_from
    message['To'] = email_to

    plaintext = MIMEText(game_price_data, 'plain')
    message.attach(plaintext)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as server:
        server.login(email_from, email_password)
        server.sendmail(email_from, email_to, message.as_string())
    
    print('Email sent\n')


def save_prices_to_file(game_title, price_list, lowest_prices_list):
    #game_title = game_title[:-13].replace(':', ' -')
    with open(os.path.join(FILE_DIRECTORY, f'{game_title}.txt'), 'w') as f:
        f.write(f'{game_title}\n\n')

        f.write('All Time Lowest Prices\n')
        f.write('--------------------------------------------\n')
        for version, price in lowest_prices_list.items():
            f.write(f'{version}:\t{price}\n')

        f.write('\nCurrent Prices\n')
        f.write('--------------------------------------------\n')
        for store, price in price_list.items():
            f.write(f'{store: <30}\t{price: >8}\n')
        f.write('\n')

    with open(os.path.join(FILE_DIRECTORY, f'{game_title}.txt'), 'r') as f:
        return f.read()


def get_prices():
    urls = [
        'https://www.dekudeals.com/items/tales-of-vesperia-definitive-edition',
    ]

    for url in urls:
        price_list = {}
        lowest_prices_list = {}

        result = requests.get(url)
        doc = BeautifulSoup(result.text, 'html.parser')

        game_title = doc.find('title').text[:-13].replace(':', ' -')

        all_time_low = doc.find_all('strong', text='All time low')[
            0].find_all_next('td', colspan=True)
        for td in all_time_low:
            game_version = td.text.strip()

            if game_version == 'Digital':
                lowest_prices_list[f'{game_version}'] = f'{td.find_next("td", class_=True).text.strip()}'
            else:
                lowest_prices_list[f'{game_version}'] = f'{td.find_next("td", class_=True).find_next("td", class_=True).text.strip()}'

        prices = doc.find_all(text='Current prices')[0].find_all_next('img', alt=True)
        for img in prices:
            if img['alt'] != 'Screenshot' and img['alt'] != '' and img['alt'] is not None:

                game_version = img.find_next('td', class_='version').text

                # Physical version
                for price in img.find_all_next('div', class_='btn btn-block btn-outline-secondary'):
                    price_list[f'{img["alt"].strip()} ({game_version.strip()})'] = f'{price.text.split("-", 1)[0].strip()}'

                # Digital version
                for price in img.find_all_next('div', class_='btn btn-block btn-primary'):
                    price_list[f'{img["alt"].strip()} ({game_version.strip()})'] = f'{price.text.split("-", 1)[0].strip()}'

        saved_file = save_prices_to_file(game_title, price_list, lowest_prices_list)
        send_email(game_title, saved_file)

def main():

    get_prices()

    scheduler = BackgroundScheduler()
    scheduler.add_job(get_prices, 'interval', hours=12)
    scheduler.start()

    print(f'Next price check: {(datetime.now() + timedelta(hours=12)).strftime("%m/%d/%Y at %H:%M")}')

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()

    # send_email()


if __name__ == '__main__':
    print('Running...\n')
    email_password = getpass.getpass(prompt='Enter email password:', stream=None)
    print('Press Ctrl+{0} to exit\n'
          .format('Break' if os.name == 'nt' else 'C'))

    main()

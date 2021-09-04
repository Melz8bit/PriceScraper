from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import date, datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import smtplib
import os
import time

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

""" def send_email():
    email_from = 'melz8bit@gmail.com'
    email_to = 'melz8bit@gmail.com'

    with open(os.path.join(FILE_DIRECTORY, 'prices.txt'), 'r') as f:
        msg = MIMEText(f.read())

    msg['Subject'] = f'{game_title} - Prices as of {date.today}'
    msg['From'] = f'{email_from}'
    msg['To'] = f'{email_to}'

    s = smtplib.SMTP('localhost')
    s.sendmail(email_from, email_to, msg.as_string())
    s.quit() """


def save_prices_to_file(game_title, price_list, lowest_prices_list):

    with open(os.path.join(FILE_DIRECTORY, f'{game_title}.txt'), 'w') as f:
        f.write(f'{game_title}\n\n')

        f.write('All Time Lowest Prices\n')
        f.write('----------------------\n')
        for version, price in lowest_prices_list.items():
            f.write(f'{version}:\t{price}\n')

        f.write('\nCurrent Prices\n')
        f.write('--------------\n')
        for store, price in price_list.items():
            f.write(f'{store}:\n\t\t\t{price}\n')
        f.write('\n')


def get_prices():
    urls = [
        'https://www.dekudeals.com/items/tales-of-vesperia-definitive-edition',
        'https://www.dekudeals.com/items/spiritfarer',
    ]

    for url in urls:
        price_list = {}
        lowest_prices_list = {}

        result = requests.get(url)
        doc = BeautifulSoup(result.text, 'html.parser')

        game_title = doc.find('title').text

        all_time_low = doc.find_all('strong', text='All time low')[0].find_all_next('td', colspan=True)
        for td in all_time_low:
            game_version = td.text.strip()

            if game_version == 'Digital':
                lowest_prices_list[f'{game_version}'] = f'{td.find_next("td", class_=True).text.strip()}'
            else:
                lowest_prices_list[f'{game_version}'] = f'{td.find_next("td", class_=True).find_next("td", class_=True).text.strip()}'

        prices = doc.find_all(text='Current prices')[
            0].find_all_next('img', alt=True)
        for img in prices:
            if img['alt'] != 'Screenshot' and img['alt'] != '' and img['alt'] is not None:

                game_version = img.find_next('td', class_='version').text

                # Physical version
                for price in img.find_all_next('div', class_='btn btn-block btn-outline-secondary'):
                    price_list[f'{img["alt"].strip()} ({game_version.strip()})'] = f'{price.text.split("-", 1)[0].strip()}'

                # Digital version
                for price in img.find_all_next('div', class_='btn btn-block btn-primary'):
                    price_list[f'{img["alt"].strip()} ({game_version.strip()})'] = f'{price.text.split("-", 1)[0].strip()}'
        
        save_prices_to_file(game_title, price_list, lowest_prices_list)

    #return(game_title, price_list, lowest_prices_list)

def main():
    print('Running...')

    get_prices()

    scheduler = BackgroundScheduler()
    scheduler.add_job(get_prices, 'interval', hours=12)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
    
    # send_email()


if __name__ == '__main__':
    main()

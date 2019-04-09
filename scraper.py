from bs4 import BeautifulSoup as bs
import requests
import re
import numpy as np
import datetime
import pandas as pd
from urllib.parse import urljoin
from collections import defaultdict
import time
import pickle


def load_urls():
    """ Returns dictionary of mountain urls saved a pickle file """

    with open('/Users/andres/Documents/Data Science/Scrape Mountain Forecast/mountain_10_urls.pickle', 'rb') as file:
        urls = pickle.load(file)
    return urls


def dump_urls(urls):
    """ Saves dictionary of mountain urls as a pickle file """

    with open('/Users/andres/Documents/Data Science/Scrape Mountain Forecast/mountain_10_urls.pickle', 'wb') as file:
        pickle.dump(urls, file)


def get_urls_by_elevation(url):
    """ Given a mountain url it returns a list or its urls by elevation """

    base_url = 'https://www.mountain-forecast.com/'
    full_url = urljoin(base_url, url)

    time.sleep(1) # Delay to not bombard the website with requests
    page = requests.get(full_url)
    soup = bs(page.content, 'html.parser')

    elevation_items = soup.find('ul', attrs={'class':'b-elevation__container'}).find_all('a', attrs={'class':'js-elevation-link'})
    
    return [urljoin(base_url, item['href']) for item in elevation_items]


def get_mountain_urls():
    """  """

    directory = 'https://www.mountain-forecast.com/countries/United-States?top100=yes'

    page = requests.get(directory)
    soup = bs(page.content, 'html.parser')

    mountain_items = soup.find('ul', attrs={'class':'b-list-table'}).find_all('li')
    mountain_urls = {item.find('a').get_text() : get_urls_by_elevation(item.find('a')['href']) for item in mountain_items}
 
    dump_urls(mountain_urls)


def clean(text):
    """ Returns a string with leading and trailing spaces removed """
    
    return re.sub('\s+', ' ', text).strip()  # Is there a way to use only REGEX?


def save_data(rows, columns):
    """ Saves the collected forecasts into a CSV file
    
    If the file already exists then it updates the old forecasts
    as necessary and/or appends new ones.
    """

    today = datetime.date.today()
    dataset_name = '~/Documents/Data Science/Scrape Mountain Forecast/mountain_weather_forecasts_dataset_{}_{}.csv'.format(today.month, today.year)

    try:
        new_df = pd.DataFrame(rows, columns=columns)
        old_df = pd.read_csv(dataset_name, dtype=object)

        new_df.set_index(columns[:4], inplace=True)
        old_df.set_index(columns[:4], inplace=True)

        old_df.update(new_df)
        only_include = ~old_df.index.isin(new_df.index)
        combined = pd.concat([old_df[only_include], new_df])
        combined.to_csv(dataset_name)

    except FileNotFoundError:
        new_df.to_csv(dataset_name, index=False)


def scrape_forecasts():
    """ """

    column_names = ['Mountain', 'Date', 'Elevation', 'Time', 'Wind', 'Summary', 'Rain', 'Snow', 'Max Temperature', 'Min Temperature', 'Chill', 'Freezing Level', 'Sunrise', 'Sunset']

    mountain_urls = load_urls()
    rows = []

    for mountain_name, urls in mountain_urls.items():

        for url in urls:

            # Request Web Page
            page = requests.get(url)
            soup = bs(page.content, 'html.parser')

            # Get data from header
            forecast_table = soup.find('table', attrs={'class': 'forecast__table forecast__table--js'})
            days = forecast_table.find('tr', attrs={'data-row': 'days'}).find_all('td')

            # Get rows from body
            times = forecast_table.find('tr', attrs={'data-row': 'time'}).find_all('td')
            winds = forecast_table.find('tr', attrs={'data-row': 'wind'}).find_all('img')  # Use "img" instead of "td" to get direction of wind
            summaries = forecast_table.find('tr', attrs={'data-row': 'summary'}).find_all('td')
            rains = forecast_table.find('tr', attrs={'data-row': 'rain'}).find_all('td')
            snows = forecast_table.find('tr', attrs={'data-row': 'snow'}).find_all('td')
            max_temps = forecast_table.find('tr', attrs={'data-row': 'max-temperature'}).find_all('td')
            min_temps = forecast_table.find('tr', attrs={'data-row': 'min-temperature'}).find_all('td')
            chills = forecast_table.find('tr', attrs={'data-row': 'chill'}).find_all('td')
            freezings = forecast_table.find('tr', attrs={'data-row': 'freezing-level'}).find_all('td')
            sunrises = forecast_table.find('tr', attrs={'data-row': 'sunrise'}).find_all('td')
            sunsets = forecast_table.find('tr', attrs={'data-row': 'sunset'}).find_all('td')

            # Iterate over days
            for i, day in enumerate(days):
                current_day = clean(day.get_text())
                elevation = url.rsplit('/', 1)[-1]
                num_cols = int(day['data-columns'])

                if current_day != '': # What if day is empty in the middle? Does it affect the count?

                    date = str(datetime.date(datetime.date.today().year, datetime.date.today().month, int(current_day.split(' ')[1])))  # Avoid using date format. Pandas adds 00:00:00 for some reason. Figure out better way to format

                    # Iterate over forecast
                    for j in range(i, i + num_cols):    

                        time_cell = clean(times[j].get_text())
                        wind = clean(winds[j]['alt'])
                        summary = clean(summaries[j].get_text())
                        rain = clean(rains[j].get_text())
                        snow = clean(snows[j].get_text())
                        max_temp = clean(max_temps[j].get_text())
                        min_temp = clean(min_temps[j].get_text())
                        chill = clean(chills[j].get_text())
                        freezing = clean(freezings[j].get_text())
                        sunrise = clean(sunrises[j].get_text())
                        sunset = clean(sunsets[j].get_text())

                        rows.append(np.array([mountain_name, date, elevation, time_cell, wind, summary, rain, snow, max_temp, min_temp, chill, freezing, sunrise, sunset]))

            time.sleep(1)  # Delay to not bombard the website with requests

    save_data(rows, column_names)


if __name__ == '__main__':

    start = time.time()
    scrape_forecasts()
    print(time.time() - start)
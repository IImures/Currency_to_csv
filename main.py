from datetime import datetime, timedelta
import threading
from time import sleep
import requests
import pandas as pd

# Dictionary to store dataframes
rates = {}


# Fetch currency data from API
def fetch_currency_data():
    currency_list = ['EUR', 'USD', 'CHF']

    # Defining period of 60 days
    last_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')

    for currency in currency_list:
        get = "http://api.nbp.pl/api/exchangerates/rates/a/{}/{}/{}".format(currency, start_date, last_date)
        response = requests.get(get)
        name = f"{currency}/PLN"
        # Store data into dataframe
        rates[name] = pd.DataFrame(response.json()['rates']).drop(columns=['no'])
        rates[name]['currency'] = f"{currency}/PLN"

    # Calculate additional data
    calculate_other_rates(convert=['EUR', 'CHF'], target='USD')

    # Change positions of columns for better look
    for pair in rates:
        rates[pair] = rates[pair][['currency', 'effectiveDate', 'mid']]


# Calculate additional data
def calculate_other_rates(convert, target):
    for currency in convert:
        name = f"{currency}/{target}"

        rates[name] = pd.DataFrame()
        # Copying dates
        rates[name]['effectiveDate'] = rates[f"{currency}/PLN"]['effectiveDate']
        # Calculating rate and round to 5 decimals
        rates[name]['mid'] = round(rates[f"{currency}/PLN"]['mid'] / rates[f"{target}/PLN"]['mid'], 4)
        rates[name]['currency'] = name


# Showing data about chosen currencies
def show_selected_data(input):
    # Format user input
    currency_pairs = [pair.strip().upper() for pair in input.split(",")]
    # Filter user input
    filtered_pairs = [pair for pair in currency_pairs if pair in rates]

    for pair in filtered_pairs:
        print(f"Data for {pair}:")
        print(rates[pair])

    # Find how much wrong pairs was in user input
    wrong_names = list(set(currency_pairs) - set(filtered_pairs))
    if len(wrong_names) != 0:
        display_message(f"Data for {wrong_names} swasn't find")
    if len(filtered_pairs) != 0:
        return ask_to_save(filtered_pairs)
    return


# Asks user if to save shown data into another file
def ask_to_save(filtered_pairs):
    user_input = input('Do you want to save this data?[Y/N]')
    if user_input.upper() == 'Y':
        # Save data
        save_fetched_data(data=filtered_pairs, user_defined=True)
    elif user_input.upper() == 'N':
        # Prints two lines just for better look and ends this function
        display_message('')
        return
    else:
        display_message('Don\'t understand you try again')
        # Calls this method again until user write y or n
        ask_to_save(filtered_pairs=filtered_pairs)
    return


# Saves fetched data and data selected by user
# if user_defined = false it will save data that in rates dict
# variable data stores pairs of currencies written by user
def save_fetched_data(data=None, user_defined=False):
    # Saves all fetched data
    if not user_defined:
        data = rates.keys()

        to_save = pd.DataFrame()
        for pair in data:
            to_save = pd.concat([to_save, rates[pair]], ignore_index=True)

        to_save.to_csv('all_currency_data.csv', index=False)
    # Saves user defined pairs
    else:
        # Reads values from file all_currency_data.csv
        from_file = pd.read_csv('all_currency_data.csv')
        # Getting only user defined currencies
        filtered = from_file[from_file['currency'].isin(data)]
        # Save into selected_currency_data.csv
        filtered.to_csv('selected_currency_data.csv', index=False)

        display_message(f"Data for {data} has been saved!")


# Calculate of user defined pair currencies
# Returns dict of calculated statistic
# if such pair doesn't exists returns 'No such pair'
def calculate_statistics(user_input):
    pair = user_input.upper().split(' ')[1]
    if pair not in rates:
        return 'No such pair'

    statistics = {
        'Average': rates[pair]['mid'].mean(),
        'Median': rates[pair]['mid'].median(),
        'Minimum': rates[pair]['mid'].min(),
        'Maximum': rates[pair]['mid'].max()
    }
    return statistics


# Setups timer that will run daily at 12.00 PM and fetch new data
def timer():
    display_message("Timer started")
    while True:
        now = datetime.now()

        # Calculate time until 12:00 PM
        target_time = datetime(now.year, now.month, now.day, 12, 0)
        if now > target_time:
            # If it's already past 12:00 PM, move to the next day
            target_time += timedelta(days=1)
        time_diff = target_time - now

        sleep_seconds = time_diff.total_seconds()

        fetch_currency_data()
        save_fetched_data()

        sleep(sleep_seconds)


# Function to display the main menu and handle user input
def display_menu():
    user_input = input(
        "Enter the currency pair you want to analyze (e.g., EUR/PLN) \n" +
        "In order to show statistic print 'stat (EUR/PLN)'"
        "In order to stop program print 'exit' \n" +
        "Your input: ")
    if user_input.lower() == 'exit':
        display_message('Bye')
        exit()
    elif user_input.lower().split(' ')[0] == 'stat':
        display_message(calculate_statistics(user_input).__str__())
    else:
        show_selected_data(user_input)


# Displays formatted text
def display_message(text):
    print(
        '-' * 20 +
        '\n' + text + '\n' +
        '-' * 20 + '\n'
    )


if __name__ == '__main__':
    # Fetch data and save it into CSV file
    fetch_currency_data()
    save_fetched_data()

    # Starts thread for periodic fetching
    thread = threading.Thread(target=timer)
    thread.daemon = True
    thread.start()

    # Display main menu
    while True:
        display_menu()

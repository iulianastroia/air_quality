import pandas as pd


def extract_needed_dates(start_day, start_month, start_year, end_day, end_month, end_year):
    data = pd.read_csv("https://raw.githubusercontent.com/iulianastroia/csv_data/master/april_dataframe.csv")
    print(data.head())
    data['day'] = pd.to_datetime(data['day'], format="%d/%m/%Y")
    data = data.loc[(data['day'] >= (start_year + "-" + start_month + "-" + start_day)) & (
            data['day'] <= (end_year + "-" + end_month + "-" + end_day))]
    print("HEAD of dataframe is", data.head())
    return data


def split_date(dates):
    start_date, end_date = dates.split(', ', 1)
    start_month, start_day, start_year = start_date.split('/', 2)
    end_month, end_day, end_year = end_date.split('/', 2)
    start_day, start_month, start_year = str(start_day), str(start_month), str(start_year)
    end_day, end_month, end_year = str(end_day), str(end_month), str(end_year)
    return start_day, start_month, start_year, end_day, end_month, end_year


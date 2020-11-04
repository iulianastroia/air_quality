from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import datetime
from selenium.webdriver.support.ui import Select
import os

# automatic downloads
options = webdriver.ChromeOptions()
profile = {"profile.default_content_setting_values.automatic_downloads": 1}
options.add_experimental_option("prefs", profile)

prefs = {"download.default_directory": "D:\\Licenta\\anomaly\\prediction_csv"}

options.add_experimental_option("prefs", prefs)


## If file exists, delete it ##
def delete_old_data(path):
    if os.path.isfile(path):
        os.remove(path)
    else:  ## Show an error ##
        print("Error: %s file not found" % path)


def connect_and_download(sensor_name):
    driver = webdriver.Chrome(executable_path=r'D:\drivers\chromedriver\chromedriver.exe', options=options)
    driver.get("http://anomalydetection.pythonanywhere.com/login")
    temperature_data = "D:/Licenta/anomaly/prediction_csv/" + sensor_name + ".csv"

    delete_old_data(temperature_data)

    # input username
    username_input = driver.find_element_by_id("username")
    username_input.send_keys('admin')

    # input password
    password_input = driver.find_element_by_id("password")
    password_input.send_keys('admin')

    #submitLogin
    loginSubmit = driver.find_element_by_id('login')
    loginSubmit.click()

    # go to Dashboard
    dashboard = driver.find_element_by_partial_link_text('Dashboard')
    dashboard.click()

    # go to Data section
    data = driver.find_element_by_partial_link_text('Time Series')
    data.click()

    def wait_load_page(id_name):
        try:
            option = WebDriverWait(driver, 100).until(
                EC.element_to_be_clickable((By.ID, id_name)))
            option.click()
        except TimeoutException  as e:
            print("EXCEPTION TIMEOUT ", e)

    download_checkbox = "true"
    driver.execute_script("document.getElementById('download_checkbox').checked = " + download_checkbox + ";")

    current_date = datetime.datetime.now()

    start_year = current_date.year
    start_month = current_date.month - 1
    start_day = 1

    select_start_date = driver.find_element_by_id("d1")
    driver.execute_script(
        "arguments[0].value = '" + str(start_year) + "-0" + str(start_month) + "-0" + str(start_day) + "';",
        select_start_date)

    def wait_for_select(select_name):
        select = Select(driver.find_element_by_id('sensors'))  # Brasov sensor data
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "option[value=" + select_name + "]")))
        if select_name == 'temperature' or select_name == 'pressure' or select_name == 'humidity':
            select.select_by_visible_text(select_name.capitalize())  # pressure,temperature,humidity
        elif select_name == 'co2':
            select.select_by_visible_text('Carbon Dioxide')
        elif select_name == 'ch2o':
            select.select_by_visible_text('Formaldehyde')
        elif select_name == 'o3':
            select.select_by_visible_text('Ozone')
        elif select_name == 'pm1':
            select.select_by_visible_text('PM1.0')
        elif select_name == 'pm25':
            select.select_by_visible_text('PM2.5')
        elif select_name == 'pm10':
            select.select_by_visible_text('PM10')


    def select_and_push(select_name):
        wait_for_select(select_name)  # select pressure, temperature...

    def wait_for_download():
        wait = WebDriverWait(driver, 100)

        # wait for data to be downloaded
        wait.until(EC.text_to_be_present_in_element((By.ID, "status"), "Data was downloaded"))

        # download data
        data = driver.find_element_by_id('visualize_btn')
        data.click()

    select_and_push(sensor_name)

    wait_for_download()


connect_and_download("temperature")
connect_and_download("pressure")
connect_and_download("humidity")
connect_and_download("co2")
connect_and_download("ch2o")
connect_and_download("o3")
connect_and_download("pm1")
connect_and_download("pm25")
connect_and_download("pm10")

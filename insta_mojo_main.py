import json
import os
import traceback
from time import sleep

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import db_class


def get_json_data(browser: webdriver):
    html_txt = browser.page_source
    soup = BeautifulSoup(html_txt, 'lxml')
    j_data = soup.select_one('body>script').text.replace('window.__INITIAL_STATE__ = ', '').strip()
    soup.decompose()
    current_url = browser.current_url
    return j_data, current_url


def insta_mojo_profile(browser: webdriver, db_connection):
    html_txt = browser.page_source
    soup = BeautifulSoup(html_txt, 'lxml')
    j_str_data = soup.select_one('[type="application/ld+json"]').text.strip()
    soup.decompose()
    j_data = json.loads(j_str_data)
    if not db_connection['instamojo_profile'].find_one({'url': j_data['url']}):
        db_conn['instamojo_profile'].insert_one(j_data)
        print(f'Successfully added. {j_data}')
    else:
        print(f"Data already exists into db. {j_data}")
    return j_data


if __name__ == "__main__":

    db_name = 'CosmoLeads'
    collection_common = "myinstamojo_full_details"
    conn = db_class.get_connection(os.getenv('MONGODB_USR'), os.getenv('MONGODB_PWD'))
    db_conn = conn[db_name]

    with open("clean_url.txt", 'r', encoding="utf8") as file:
        url_list = file.readlines()

    options = Options()
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--no-sandbox")
    # just some options passing in to skip annoying popups
    options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option("windowTypes", ["webview"])
    options.add_argument("--start-maximized")
    options.add_argument("--headless")

    # starting service for Chrome web driver
    service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))

    # initiating and returning Chrome web driver
    main_browser = webdriver.Chrome(service=service, options=options)

    for index, urll in enumerate(url_list, start=1):
        result = {}
        print()
        print(f'{str(index)} Scraping for: {urll.strip()}')

        main_browser.get(urll.strip())
        main_browser.implicitly_wait(60)
        p_title = main_browser.title

        if 'https://www.instamojo.com/@' in urll.strip():

            if p_title == "404: Page Not Found — Instamojo":
                print(f'{urll.strip()}: {p_title}')
                continue
            else:
                insta_mojo_profile(main_browser, db_conn)
        else:
            if p_title == "Instamojo":
                print(f'{urll.strip()}: {p_title}')
                continue
            else:
                try:
                    return_list = get_json_data(main_browser)
                    j_d = json.loads(return_list[0])

                    if list(j_d.keys())[0] == "category":
                        result['URL'] = urll.strip()
                        result['Name'] = j_d.get('storeInfo').get('storeInfo').get('storename')
                        result['UserName'] = j_d.get('storeInfo').get('storeInfo').get('username')
                        result['Number'] = j_d.get('storeInfo').get('storeInfo').get('contactInfo').get('number')
                        result['Email'] = j_d.get('storeInfo').get('storeInfo').get('contactInfo').get('email')
                        result['Social'] = j_d.get('storeInfo').get('storeInfo').get('social')
                        result['Location'] = j_d.get('storeInfo').get('storeInfo').get('contactInfo').get('address')
                        result['current_url'] = return_list[1]

                    elif list(j_d.keys())[0] == "profile":
                        result['URL'] = urll.strip()
                        result['Name'] = j_d.get('profile').get('fullName')
                        result['UserName'] = j_d.get('profile').get('username')
                        result['Number'] = j_d.get('profile').get('phone')
                        result['Email'] = j_d.get('profile').get('email')
                        result['Website'] = j_d.get('profile').get('website')
                        result['Social'] = j_d.get('profile').get('socialLinks')
                        result['Location'] = j_d.get('profile').get('location')
                        result['current_url'] = return_list[1]
                    if not db_conn[collection_common].find_one({'URL': urll.strip()}):
                        insert_row = db_conn[collection_common].insert_one(result)
                        print(f"Data saved successfully. {insert_row.inserted_id} {result}")
                    else:
                        print(f"Data already exists into db. {result}")
                except Exception as e:
                    print('Exception', e.with_traceback(traceback.print_exc()))
        sleep(0.7)
    main_browser.quit()

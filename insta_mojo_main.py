import json
import os
import traceback
from time import sleep

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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
        print(f"Data already exists into db.")
    return j_data


def my_instamojo_ngif(browser: webdriver):
    soup = BeautifulSoup(browser.page_source, 'lxml')
    email = soup.select_one('[ng-if="mc.email"]').text
    contact = soup.select_one('[ng-if="mc.contact"]').text
    address = soup.select_one('[ng-if="mc.address"]').text

    soup.decompose()
    return [email, contact, address]


def get_myinstamojo_latest(browser: webdriver):
    try:
        returned_dict = {}
        script_text = browser.find_element(By.XPATH, '//head/script[@type="text/javascript"][last()]').get_attribute('innerHTML').lstrip(' ')
        script_split = [x.strip() for x in script_text.splitlines()]
        for x in script_split:
            if 'var username = ' in x:
                returned_dict['UserName'] = x.replace('var username = "', '').replace('";', '').strip()
            elif 'var contact = ' in x:
                returned_dict['Number'] = x.replace('var contact = "', '').replace('";', '').strip()
            elif 'var email = ' in x:
                returned_dict['Email'] = x.replace('var email = "', '').replace('";', '').strip()
            elif 'var address = ' in x:
                returned_dict['Location'] = x.replace('var address = "', '').replace('";', '').replace('<p>',
                                                                                                       '').replace(
                    '</p>', '').strip()
            elif 'var shop_name = ' in x:
                returned_dict['Name'] = x.replace('var shop_name = "', '').replace('";', '').strip()
        return returned_dict
    except:
        print(f'Exception: get_myinstamojo_latest {browser.current_url}')
        return None


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
        if not db_conn[collection_common].find_one({'URL': urll.strip()}):
            try:
                main_browser.get(urll.strip())
                main_browser.implicitly_wait(60)
                sleep(0.5)
                p_title = main_browser.title
                if 'https://www.instamojo.com/@' in urll.strip():
                    if p_title == "404: Page Not Found ??? Instamojo":
                        print(f'{urll.strip()}: {p_title}')
                        continue
                    else:
                        try:
                            insta_mojo_profile(main_browser, db_conn)
                        except:
                            print(f'{urll.strip()}: {p_title}')
                            continue
                else:
                    if p_title == "Instamojo":
                        print(f'{urll.strip()}: {p_title}')
                        continue
                    elif p_title == "404: Page Not Found ??? Instamojo":
                        print(f'{urll.strip()}: {p_title}')
                        continue
                    elif p_title == "Oops!":
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
                                print(f"Data already exists into db.")
                        except Exception as e:
                            print('Exception', e)
                            # print('Exception', e.with_traceback(traceback.print_exc()))
                            result_dict = get_myinstamojo_latest(main_browser)
                            if result_dict is not None:
                                result = result_dict
                                result['URL'] = urll.strip()
                                result['Website'] = ''
                                result['Social'] = ''
                                result['current_url'] = main_browser.current_url

                                if not db_conn[collection_common].find_one({'URL': urll.strip()}):
                                    insert_row = db_conn[collection_common].insert_one(result)
                                    print(f"Data saved successfully. {insert_row.inserted_id} {result}")
                                else:
                                    print(f"Data already exists into db.")

                sleep(0.5)
            except Exception as e:
                print('Exception', e.with_traceback(traceback.print_exc()))
                continue
        else:
            print(f"Data already exists into db.")
    main_browser.quit()

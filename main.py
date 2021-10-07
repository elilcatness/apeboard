import json
import os
from datetime import datetime

from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.support.ui import WebDriverWait

MONTH_NAME_TO_INT = {'jan': 0,
                     'feb': 1,
                     'mar': 2,
                     'apr': 3,
                     'may': 4,
                     'jun': 5,
                     'jul': 6,
                     'aug': 7,
                     'sep': 8,
                     'oct': 9,
                     'nov': 10,
                     'dec': 11}


def get_driver():
    options = ChromeOptions()
    # options.add_argument('--headless')
    return Chrome(options=options)


def convert_str_to_dt(dt_str: str):
    try:
        date_section, time_section = dt_str.split(', ')
        day, month, year = date_section.split()
    except ValueError:
        return print(f'Failed to convert {dt_str}')
    try:
        day = int(day)
    except ValueError:
        return print(f'Failed to convert {day} into day INT')
    try:
        month = MONTH_NAME_TO_INT[month.lower()]
    except KeyError:
        return print(f'Failed to convert {month} into INT')
    try:
        year = int(f'20{year}')
    except ValueError:
        return print(f'Failed to convert {year} into year INT')
    try:
        time, state = time_section.split()
        assert state.lower() in ('am', 'pm')
        hours, minutes = map(int, time.split(':'))
    except (ValueError, AssertionError):
        return print(f'Failed to convert {time_section}')
    if state.lower() == 'pm':
        hours += 12
    return datetime(year=year, month=month, day=day, hour=hours, minute=minutes)


def parse_metadata(driver):
    driver.execute_script('window.scroll(0, 1000)')
    data = {block.find_element_by_tag_name('span').text: block.find_element_by_tag_name('h3').text
            for block in WebDriverWait(driver, 5).until(
            exp_cond.presence_of_element_located(
                (By.XPATH, '//div[@class="css-1gozys9 e12g3vhd1"]'))).find_elements_by_tag_name('div')}
    return data


def process_hash_link(elem, xpath):
    link = WebDriverWait(elem, 10).until(exp_cond.presence_of_element_located((By.XPATH, xpath))).get_attribute('href')
    return link.split('/')[-1].split('?')[0], link


def parse_table(driver: Chrome):
    headers = [h.text for h in WebDriverWait(driver, 10).until(exp_cond.presence_of_element_located(
        (By.XPATH, './/tr[@class="MuiTableRow-root MuiTableRow-head"]'))).find_elements_by_tag_name('th')]
    rows = driver.find_elements_by_xpath('//tr[@class="MuiTableRow-root css-kr9zws e1a9tldx0"]')
    output = []
    for row in rows:
        blocks = row.find_elements_by_xpath('.//td')
        data = {}
        for i in range(len(blocks)):
            header = headers[i]
            if header.lower() == 'date':
                hash_, link = process_hash_link(blocks[i], './/a')
                data[header] = {'inner_hash': hash_,
                                'inner_link': link}
            elif header.lower() == 'interacted with':
                block = blocks[i].find_element_by_xpath('.//div/div')
                try:
                    operation = block.find_element_by_xpath('.//p').text
                except NoSuchElementException:
                    operation = None
                hash_, link = process_hash_link(blocks[i], './/a')
                data[header] = {'operation': operation,
                                'others_hash': hash_,
                                'others_link': link}
            elif header.lower() == 'transfer':
                data[header] = []
                for a in blocks[i].find_elements_by_xpath('.//a'):
                    data[header].append({'payload': a.text, 'link': a.get_attribute('href')})
            elif header.lower() == 'gas fee':
                dollars_span = blocks[i].find_element_by_xpath('.//*[@class="MuiTypography-root MuiTypography-caption '
                                                               'MuiTypography-colorTextSecondary"]')
                data[header] = {'source fee': blocks[i].find_element_by_xpath(
                    './/*[@class="MuiTypography-root MuiTypography-body2 MuiTypography-colorTextPrimary"]').text,
                                '$ fee': dollars_span.text,
                                'source/$ course': dollars_span.get_attribute('title')}
            else:
                try:
                    data[header] = blocks[i].find_element_by_xpath('.//p').text.strip()
                except NoSuchElementException:
                    data[header] = None
        output.append(data)
    with open('response.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(output, indent=4))


def get_data(dt_from, dt_to):
    driver = get_driver()
    driver.get(os.getenv('url'))
    metadata = parse_metadata(driver)
    table = parse_table(driver)


def main():
    dt_from = convert_str_to_dt(input('from: '))
    if not dt_from:
        return None
    dt_to = convert_str_to_dt(input('to: '))
    if not dt_to:
        return None
    get_data(dt_from, dt_to)


if __name__ == '__main__':
    load_dotenv()
    callback = main()
    if callback:
        print(callback)

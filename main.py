from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
import os
import re
import math
import time
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import yaml

baseURL = 'https://coralnet.ucsd.edu'
loginUrl = baseURL + '/accounts/login/'

def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def login_coral_net(username, password, binary_location):
    print('Connecting to the source...')
    options = ChromeOptions()
    if binary_location is not None :
        options.binary_location = binary_location
    download_directory = './Annotations'
    #options.add_argument('download.default_directory=' + download_directory)
    prefs = {
        "download.default_directory": download_directory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option('prefs', prefs)

    driver = webdriver.Chrome(options)

    # Open login page
    driver.get(loginUrl)

    # Field forms of the login page
    username_field = driver.find_element(By.NAME, 'username').send_keys(username)
    password_field = driver.find_element(By.NAME, 'password').send_keys(password)

    # Submit form
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

    # Waiting for the page to connect (CoralNet is kind of slow)
    driver.implicitly_wait(10)

    return driver


def download_images(num, driver, numSource):
    print('Downloading', num, 'images')
    numImages = num
    fileName = '/source/'+str(numSource)+'/browse/images'
    imageUrl = baseURL + fileName

    # read number of images you need to download
    print('Number of Images in the list:', numImages)

    # number of images found
    k = 0

    # Login
    driver.get(imageUrl)

    #download_annotations(driver)

    select_element = driver.find_element(By.ID, "id_annotation_status")

    select = Select(select_element)

    select.select_by_value("confirmed")
    # make requests session
    selenium_cookies = driver.get_cookies()

    search_form = driver.find_element(By.ID,"search-form")

    search_button = search_form.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Search"]')

    search_button.click()
    time.sleep(5)

    session = requests.Session()

    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    iterations = math.ceil(numImages / 20)
    print('Number of pages to download:', iterations)
    directory = './Images'
    if not os.path.exists(directory):
        os.makedirs(directory)
    for n in range(iterations):
        ids = list()
        try:
            if n > 0:
                print("Go to page", n + 1)
                form = driver.find_element(By.CLASS_NAME, "no-padding")
                next_page_input = form.find_element(By.XPATH, "//input[@title='Next page']")
                # Click on next page
                next_page_input.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "thumb_wrapper")))
        except (NoSuchElementException, TimeoutException) as e:
            print("Erreur lors du changement de page :", e)
            print("Tentative de se connecter à nouveau après une pause de 10 secondes...")
            time.sleep(10)
            try:
                print("Tentative de chargement de la page à nouveau...")
                driver.get(imageUrl)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_annotation_status")))
                print("Page chargée avec succès. Reprise du téléchargement.")
            except TimeoutException:
                print("Timeout lors de la tentative de chargement de la page. Arrêt du téléchargement.")
                break

        print(n, 'Searching images in the url code...')
        # Get source code
        html_content = driver.page_source

        # Extract images
        soup_image = BeautifulSoup(html_content, "html.parser")

        # get csrf token
        csrf_middleware_token = soup_image.find("input", {"name": "csrfmiddlewaretoken"})
        csrf_token = csrf_middleware_token['value']

        # each images is under thumb_wrapper class
        thumb_wrappers = soup_image.find_all('span', class_='thumb_wrapper')
        for thumb_wrapper in thumb_wrappers:
            # find image view link
            link_tag = thumb_wrapper.find('a')
            # print('link_tag', link_tag)
            link = baseURL + link_tag['href']

            # extract ids image
            id_image = re.search('(\d+)', link_tag['href']).group(1)
            ids.append(id_image)

            image_view = session.get(link)
            html_image = image_view.text
            soup_a_image = BeautifulSoup(html_image, "html.parser")

            # find image original source
            div_img_original = soup_a_image.find('div', id="original_image_container")
            img_original = div_img_original.find('img')
            img_src = img_original['src']

            # get image name
            img_tag = thumb_wrapper.find('img')
            img_name = img_tag['title']

            src = session.get(img_src, allow_redirects=True)

            # write in directory
            if src.status_code == 200:
                img_name = img_name.split("JPG")[0].strip()
                img_name += "JPG"
                print(img_name)
                with open(os.path.join(directory, img_name), 'wb') as f:
                    f.write(src.content)
                    k = k + 1
                    print('Image', k, 'saved')
                    if k > numImages:
                        print("Downloading ended")
                        break
            else:
                print('Error in finding the image source: ', src.status_code)



def download_annotations(driver):
    # downloading all the annotation file
    action_dropdown = Select(
        driver.find_element(By.XPATH, "//div[@id='action-box']/select[@name='browse_action']"))
    action_dropdown.select_by_value('export_annotations')

    time.sleep(2)

    image_dropdown = Select(
        driver.find_element(By.XPATH, "//div[@id='action-box']/select[@name='image_select_type']"))
    image_dropdown.select_by_value('all')

    submit_button = driver.find_element(By.XPATH,
                                        "//div[@id='action-box']/form[@id='export-annotations-prep-form']"
                                        "/button[@class='submit red']")

    submit_button.click()

    time.sleep(10)


if __name__ == '__main__':
    config = load_config('config.yaml')

    # Extract yaml config
    username = config['credentials']['username']
    password = config['credentials']['password']
    binary_location = config['chrome']['binary_location']
    nb_source = config['source_parameters']['nb_source']
    nb_images_download = config['source_parameters']['nb_images_download']

    driver = login_coral_net(username, password, binary_location)
    download_images(nb_images_download, driver, nb_source)
    driver.quit()



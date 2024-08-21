from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
from dotenv import load_dotenv
import time
import sys

# Încărcăm variabilele de mediu
load_dotenv()

driver = webdriver.Firefox()
driver.maximize_window()
# Deschidem pagina principală
driver.get("https://www.calendis.ro")

# Autentificare
try:
    # Apăsăm butonul de autentificare
    login_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "login-btn"))
    )
    login_btn.click()

    # Completăm email-ul
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "forEmail"))
    )
    email_field.send_keys(os.getenv('EMAIL'))

    # Completăm parola
    password_field = driver.find_element(By.ID, "forPassword")
    password_field.send_keys(os.getenv('ACC_PASSWORD'))

    # Apăsăm butonul de conectare
    connect_btn = driver.find_element(By.CSS_SELECTOR, "button.connect.validation_button")
    connect_btn.click()

    print("Autentificare reușită!")
except TimeoutException:
    print("Eroare la autentificare: timpul de așteptare a expirat.")
    driver.quit()
    sys.exit(1)

# Navigăm la pagina dorită
try:
    driver.get("https://www.calendis.ro/cluj-napoca/baza-sportiva-gheorgheni/b")
    print("Navigare reușită!")
except TimeoutException:
    print("Eroare la navigare: timpul de așteptare a expirat.")
    driver.quit()
    sys.exit(1)

try:
    fotbal_service = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='col-xs-6 service-name' and @title='Fotbal']"))
    )
    fotbal_service.click()
except TimeoutException:
    print("Nu s-a găsit serviciul Fotbal.")
    driver.quit()
    sys.exit(1)

def check_availability():
    calendar_days = driver.find_elements(By.CSS_SELECTOR, ".calendar-days-wrapper .day")

    for day in calendar_days:
        day.click()
        time.sleep(2)  # Adăugăm un delay de 2 secunde după click

        try:
            # Așteptăm ca sloturile să se încarce sau să apară mesajul
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#appointment-slots .slot-item, .slots-message"))
            )

            # Verificăm dacă există mesajul
            try:
                message = driver.find_element(By.CSS_SELECTOR, ".slots-message").text
                if "Ai deja o rezervare la acest sport în săptămâna selectată." in message:
                    print(f"Rezervare existentă pentru ziua {day.find_element(By.CSS_SELECTOR, '.day-nr').text}. Trecem la următoarea zi.")
                    continue
                elif "Se pot face rezervări cu maxim 14 zile înainte." in message:
                    print("S-a atins limita de 14 zile pentru rezervări. Încheiem procesul de căutare.")
                    return False  # Oprim procesul de căutare
            except NoSuchElementException:
                pass  # Nu există mesaj, continuăm cu verificarea sloturilor

            slots = driver.find_elements(By.CSS_SELECTOR, "#appointment-slots .slot-item")

            if not slots:
                print(f"Nu sunt sloturi disponibile pentru ziua {day.find_element(By.CSS_SELECTOR, '.day-nr').text}")
            else:
                for slot in slots:
                    slot_time = slot.find_element(By.CSS_SELECTOR, ".slot-time strong").text
                    if slot_time in ["20:00", "21:00"]:
                        print(f"Slot disponibil: {day.find_element(By.CSS_SELECTOR, '.day-nr').text} - {slot_time}")

        except TimeoutException:
            print(f"Eroare la încărcarea sloturilor pentru ziua {day.find_element(By.CSS_SELECTOR, '.day-nr').text}")

    return True  # Continuăm procesul de căutare

# Verificăm disponibilitatea pentru trei săptămâni
for week in range(1, 4):
    print(f"\nVerificăm disponibilitatea pentru săptămâna {week}:")
    if not check_availability():
        break  # Oprim procesul dacă am atins limita de 14 zile

    if week < 3:  # Navigăm la următoarea săptămână doar dacă nu suntem la ultima
        try:
            next_week_arrow = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".calendar-arrow.right-arrow .arrow-img-holder"))
            )
            next_week_arrow.click()
            time.sleep(2)  # Adăugăm un delay de 2 secunde după navigarea la săptămâna următoare
        except TimeoutException:
            print(f"Nu s-a putut naviga la săptămâna {week + 1}.")
            break

# Închidem browserul
driver.quit()
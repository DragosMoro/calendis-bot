import os
from dotenv import load_dotenv
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import discord
from discord.ext import commands

load_dotenv()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await run_selenium_script()
    await bot.close()

async def send_discord_message(message):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(message)
    else:
        print(f"Could not find channel with ID {CHANNEL_ID}")

async def run_selenium_script():
    driver = webdriver.Firefox()
    driver.maximize_window()
    driver.get("https://www.calendis.ro")

    try:
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login-btn"))
        )
        login_btn.click()

        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "forEmail"))
        )
        email_field.send_keys(os.getenv('EMAIL'))

        password_field = driver.find_element(By.ID, "forPassword")
        password_field.send_keys(os.getenv('ACC_PASSWORD'))

        connect_btn = driver.find_element(By.CSS_SELECTOR, "button.connect.validation_button")
        connect_btn.click()

        print("Autentificare reușită!")
    except TimeoutException:
        print("Eroare la autentificare: timpul de așteptare a expirat.")
        driver.quit()
        sys.exit(1)

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

    available_slots = []

    def check_availability():
        calendar_days = driver.find_elements(By.CSS_SELECTOR, ".calendar-days-wrapper .day")

        for day in calendar_days:
            day.click()
            time.sleep(2)

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#appointment-slots .slot-item, .slots-message"))
                )

                try:
                    message = driver.find_element(By.CSS_SELECTOR, ".slots-message").text
                    if "Ai deja o rezervare la acest sport în săptămâna selectată." in message:
                        print(f"Rezervare existentă pentru ziua {day.find_element(By.CSS_SELECTOR, '.day-nr').text}. Trecem la următoarea zi.")
                        continue
                    elif "Se pot face rezervări cu maxim 14 zile înainte." in message:
                        print("S-a atins limita de 14 zile pentru rezervări. Încheiem procesul de căutare.")
                        return False
                except NoSuchElementException:
                    pass

                slots = driver.find_elements(By.CSS_SELECTOR, "#appointment-slots .slot-item")

                if not slots:
                    print(f"Nu sunt sloturi disponibile pentru ziua {day.find_element(By.CSS_SELECTOR, '.day-nr').text}")
                else:
                    for slot in slots:
                        slot_time = slot.find_element(By.CSS_SELECTOR, ".slot-time strong").text
                        if slot_time in ["20:00", "21:00"]:
                            date = day.find_element(By.CSS_SELECTOR, '.day-nr').text
                            available_slots.append(f"{date} - {slot_time}")
                            print(f"Slot disponibil: {date} - {slot_time}")

            except TimeoutException:
                print(f"Eroare la încărcarea sloturilor pentru ziua {day.find_element(By.CSS_SELECTOR, '.day-nr').text}")

        return True

    for week in range(1, 4):
        print(f"\nVerificăm disponibilitatea pentru săptămâna {week}:")
        if not check_availability():
            break

        if week < 3:
            try:
                next_week_arrow = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".calendar-arrow.right-arrow .arrow-img-holder"))
                )
                next_week_arrow.click()
                time.sleep(2)
            except TimeoutException:
                print(f"Nu s-a putut naviga la săptămâna {week + 1}.")
                break

    driver.quit()

    if available_slots:
        message = "Sloturi disponibile pentru fotbal:\n" + "\n".join(available_slots)
        await send_discord_message(message)
    else:
        await send_discord_message("Nu sunt sloturi disponibile pentru fotbal la orele 20:00 sau 21:00.")

bot.run(DISCORD_TOKEN)
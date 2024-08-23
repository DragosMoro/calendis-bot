import os
import sys
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import discord
from discord.ext import commands

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))


def setup_driver():
    try:
        driver = webdriver.Firefox()
        driver.maximize_window()
        return driver
    except Exception as e:
        print(f"Error setting up the driver: {str(e)}")
        sys.exit(1)

def click_element(driver, element):
    try:
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        # Wait a bit for the page to settle after scrolling
        time.sleep(0.5)
        # Try to click using JavaScript
        driver.execute_script("arguments[0].click();", element)
    except Exception as e:
        print(f"Error clicking element with JavaScript: {str(e)}")
        try:
            # If JavaScript click fails, try ActionChains
            ActionChains(driver).move_to_element(element).click().perform()
        except Exception as e:
            print(f"Error clicking element with ActionChains: {str(e)}")
            raise

def login(driver):
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

    except TimeoutException:
        print("Error: Timeout while trying to log in. Check your internet connection or the website's responsiveness.")
        driver.quit()
        sys.exit(1)
    except NoSuchElementException as e:
        print(f"Error: Could not find element during login process. Details: {str(e)}")
        driver.quit()
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during login: {str(e)}")
        driver.quit()
        sys.exit(1)


def navigate_to_page(driver):
    try:
        driver.get("https://www.calendis.ro/cluj-napoca/baza-sportiva-gheorgheni/b")
    except Exception as e:
        print(f"Error navigating to the page: {str(e)}")
        driver.quit()
        sys.exit(1)

    try:
        fotbal_service = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='col-xs-6 service-name' and @title='Fotbal']"))
        )
        click_element(driver, fotbal_service)
    except TimeoutException:
        print("Error: Timeout while trying to find 'Fotbal' service. The element might not be present.")
        driver.quit()
        sys.exit(1)
    except ElementClickInterceptedException:
        print("Error: 'Fotbal' service is intercepted. Trying to handle any overlays...")
        try:
            # Try to handle cookie consent or other overlays
            overlay = driver.find_element(By.CSS_SELECTOR, ".accept_cookies button.btn-accept-cookies")
            click_element(driver, overlay)
            time.sleep(1)
            click_element(driver, fotbal_service)
        except Exception as e:
            print(f"Failed to handle overlay: {str(e)}")
            driver.quit()
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while selecting 'Fotbal' service: {str(e)}")
        driver.quit()
        sys.exit(1)


def check_availability_for_day(driver, day):
    day_text = day.find_element(By.CSS_SELECTOR, '.day-nr').text

    day.click()
    time.sleep(2)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#appointment-slots .slot-item, .slots-message"))
        )

        try:
            message = driver.find_element(By.CSS_SELECTOR, ".slots-message").text
            if "Ai deja o rezervare la acest sport în săptămâna selectată." in message:
                return []
            elif "Se pot face rezervări cu maxim 14 zile înainte." in message:
                return None
        except NoSuchElementException:
            pass

        slots = driver.find_elements(By.CSS_SELECTOR, "#appointment-slots .slot-item")
        available_slots = []

        if not slots:
            return []
        else:
            for slot in slots:
                slot_time = slot.find_element(By.CSS_SELECTOR, ".slot-time strong").text
                if slot_time in ["20:00", "21:00"]:
                    available_slots.append(f"{day_text} - {slot_time}")

        return available_slots

    except TimeoutException:
        print(f"Error: Timeout while checking availability for day {day_text}. The slots or message might not have loaded.")
        return []
    except Exception as e:
        print(f"Unexpected error while checking availability for day {day_text}: {str(e)}")
        return []


def check_availability():
    driver = setup_driver()
    login(driver)
    navigate_to_page(driver)

    all_available_slots = []

    for week in range(1, 4):
        try:
            current_day = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".day.active.current-day, .day[disabled='false']"))
            )
        except TimeoutException:
            print("Error: Timeout while trying to find the current day or first available day.")
            driver.quit()
            return []
        except Exception as e:
            print(f"Unexpected error while finding the current day: {str(e)}")
            driver.quit()
            return []

        calendar_days = driver.find_elements(By.CSS_SELECTOR, ".calendar-days-wrapper .day[disabled='false']")
        start_index = calendar_days.index(current_day)

        for day in calendar_days[start_index:]:
            available_slots = check_availability_for_day(driver, day)
            if available_slots is None:
                driver.quit()
                return all_available_slots
            all_available_slots.extend(available_slots)

        if week < 3:
            try:
                next_week_arrow = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".calendar-arrow.right-arrow .arrow-img-holder"))
                )
                next_week_arrow.click()
                time.sleep(2)
            except TimeoutException:
                print("Error: Timeout while trying to click the next week arrow. The element might not be clickable or present.")
                break
            except Exception as e:
                print(f"Unexpected error while navigating to the next week: {str(e)}")
                break

    driver.quit()
    return all_available_slots


def main():
    available_slots = check_availability()

    if available_slots:
        message = "There We Land! These are the spots available: \n" + "\n".join(available_slots)

        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)

        @bot.event
        async def on_ready():
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(message)
            else:
                print("Error: Discord channel not found. Check your DISCORD_CHANNEL_ID.")
            await bot.close()

        try:
            bot.run(DISCORD_TOKEN)
        except discord.LoginFailure:
            print("Error: Failed to log in to Discord. Check your DISCORD_TOKEN.")
        except Exception as e:
            print(f"Unexpected error while running the Discord bot: {str(e)}")
    else:
        print("No slots available")

if __name__ == "__main__":
    main()
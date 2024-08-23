import os
import sys
import time
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))


def setup_driver():
    try:
        logger.info("Setting up the Selenium WebDriver")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        geckodriver_path = os.getenv('GECKODRIVER_PATH', 'geckodriver')
        logger.info(f"Using GeckoDriver at path: {geckodriver_path}")

        service = Service(executable_path=geckodriver_path)

        driver = webdriver.Firefox(options=options, service=service)
        driver.maximize_window()
        logger.info("WebDriver setup completed successfully")
        return driver
    except Exception as e:
        logger.error(f"Error setting up the driver: {str(e)}")
        sys.exit(1)

def click_element(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", element)
        logger.info("Element clicked successfully using JavaScript")
    except Exception as e:
        logger.warning(f"Error clicking element with JavaScript: {str(e)}")
        try:
            ActionChains(driver).move_to_element(element).click().perform()
            logger.info("Element clicked successfully using ActionChains")
        except Exception as e:
            logger.error(f"Error clicking element with ActionChains: {str(e)}")
            raise

def login(driver, website_url):
    logger.info("Initiating login process")
    driver.get(website_url)
    try:
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login-btn"))
        )
        login_btn.click()
        logger.info("Clicked login button")

        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "forEmail"))
        )
        email_field.send_keys(os.getenv('EMAIL'))
        logger.info("Entered email" + os.getenv('EMAIL'))

        password_field = driver.find_element(By.ID, "forPassword")
        password_field.send_keys(os.getenv('ACC_PASSWORD'))
        logger.info("Entered password" + os.getenv('ACC_PASSWORD'))

        connect_btn = driver.find_element(By.CSS_SELECTOR, "button.connect.validation_button")
        connect_btn.click()
        logger.info("Clicked connect button")

        time.sleep(5)

    except TimeoutException:
        logger.error("Timeout while trying to log in. Check your internet connection or the website's responsiveness.")
        driver.quit()
        sys.exit(1)
    except NoSuchElementException as e:
        logger.error(f"Could not find element during login process. Details: {str(e)}")
        driver.quit()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        driver.quit()
        sys.exit(1)


def navigate_to_page(driver):
    logger.info("Navigating to the sports facility page")
    try:
        driver.get("https://www.calendis.ro/cluj-napoca/baza-sportiva-gheorgheni/b")
        login(driver, "https://www.calendis.ro/cluj-napoca/baza-sportiva-gheorgheni/b")
    except Exception as e:
        logger.error(f"Error navigating to the page: {str(e)}")
        driver.quit()
        sys.exit(1)

    try:
        fotbal_service = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='col-xs-6 service-name' and @title='Fotbal']"))
        )
        click_element(driver, fotbal_service)
        logger.info("Selected 'Fotbal' service")
    except TimeoutException:
        logger.error("Timeout while trying to find 'Fotbal' service. The element might not be present.")
        driver.quit()
        sys.exit(1)
    except ElementClickInterceptedException:
        logger.warning("'Fotbal' service is intercepted. Trying to handle any overlays...")
        try:
            overlay = driver.find_element(By.CSS_SELECTOR, ".accept_cookies button.btn-accept-cookies")
            click_element(driver, overlay)
            time.sleep(1)
            click_element(driver, fotbal_service)
            logger.info("Handled overlay and selected 'Fotbal' service")
        except Exception as e:
            logger.error(f"Failed to handle overlay: {str(e)}")
            driver.quit()
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error while selecting 'Fotbal' service: {str(e)}")
        driver.quit()
        sys.exit(1)


def check_availability_for_day(driver, day):
    day_text = day.find_element(By.CSS_SELECTOR, '.day-nr').text
    logger.info(f"Checking availability for day: {day_text}")

    day.click()
    time.sleep(2)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#appointment-slots .slot-item, .slots-message"))
        )

        try:
            message = driver.find_element(By.CSS_SELECTOR, ".slots-message").text
            if "Ai deja o rezervare la acest sport în săptămâna selectată." in message:
                logger.info("Already have a reservation this week")
                return []
            elif "Se pot face rezervări cu maxim 14 zile înainte." in message:
                logger.info("Reached maximum reservation period (14 days)")
                return None
        except NoSuchElementException:
            pass

        slots = driver.find_elements(By.CSS_SELECTOR, "#appointment-slots .slot-item")
        available_slots = []

        if not slots:
            logger.info(f"No slots available for day {day_text}")
            return []
        else:
            for slot in slots:
                slot_time = slot.find_element(By.CSS_SELECTOR, ".slot-time strong").text
                if slot_time in ["20:00", "21:00"]:
                    available_slots.append(f"{day_text} - {slot_time}")
                    logger.info(f"Available slot found: {day_text} - {slot_time}")

        return available_slots

    except TimeoutException:
        logger.error(f"Timeout while checking availability for day {day_text}. The slots or message might not have loaded.")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while checking availability for day {day_text}: {str(e)}")
        return []


def check_availability():
    driver = setup_driver()
    login(driver, "https://www.calendis.ro")
    navigate_to_page(driver)


    all_available_slots = []

    for week in range(1, 4):
        logger.info(f"Checking week {week}")
        try:
            current_day = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".day.active.current-day, .day[disabled='false']"))
            )
        except TimeoutException:
            logger.error("Timeout while trying to find the current day or first available day.")
            driver.quit()
            return []
        except Exception as e:
            logger.error(f"Unexpected error while finding the current day: {str(e)}")
            driver.quit()
            return []

        calendar_days = driver.find_elements(By.CSS_SELECTOR, ".calendar-days-wrapper .day[disabled='false']")
        start_index = calendar_days.index(current_day)

        for day in calendar_days[start_index:]:
            available_slots = check_availability_for_day(driver, day)
            if available_slots is None:
                logger.info("Reached end of available booking period")
                driver.quit()
                return all_available_slots
            all_available_slots.extend(available_slots)

        if week < 3:
            try:
                next_week_arrow = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".calendar-arrow.right-arrow .arrow-img-holder"))
                )
                next_week_arrow.click()
                logger.info("Navigated to next week")
                time.sleep(2)
            except TimeoutException:
                logger.error("Timeout while trying to click the next week arrow. The element might not be clickable or present.")
                break
            except Exception as e:
                logger.error(f"Unexpected error while navigating to the next week: {str(e)}")
                break

    driver.quit()
    return all_available_slots


def main():
    logger.info("Starting availability check")
    available_slots = check_availability()

    if available_slots:
        logger.info(f"Found {len(available_slots)} available slots")
        message = "There We Land! These are the spots available: \n" + "\n".join(available_slots)

        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)

        @bot.event
        async def on_ready():
            logger.info("Discord bot is ready")
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(message)
                logger.info("Sent available slots message to Discord channel")
            else:
                logger.error("Discord channel not found. Check your DISCORD_CHANNEL_ID.")
            await bot.close()

        try:
            logger.info("Attempting to run Discord bot")
            bot.run(DISCORD_TOKEN)
        except discord.LoginFailure:
            logger.error("Failed to log in to Discord. Check your DISCORD_TOKEN.")
        except Exception as e:
            logger.error(f"Unexpected error while running the Discord bot: {str(e)}")
    else:
        logger.info("No slots available")

if __name__ == "__main__":
    main()
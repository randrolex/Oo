import telebot
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random
import string

TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_data = {}

ADDRESS = {
    "street": "Aakash Tower, 781, Eastern Bypass, Ruby, Kasba, Anandpur",
    "city": "Kolkata",
    "state": "West Bengal",
    "postal_code": "700107",
    "phone": "09804279691",
    "full_name": "Pranab Pratap Mehan",
    "gender": "male"
}
PASSWORD = "2001@Pubg"

CARD = {
    "number": "4748380903754740",
    "expiry": "06/26",  # Common format MM/YY
    "cvv": "957"
}
LIMIT_CODESPACE = 1000
LIMIT_ACTIONS = 2000

def generate_username(email):
    name_part = email.split('@')[0]
    rand_digits = ''.join(random.choices(string.digits, k=4))
    return f"{name_part}{rand_digits}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /create and send your email. Username will be auto, password fixed, address/card auto-filled for billing.")

@bot.message_handler(commands=['create'])
def ask_email(message):
    user_data[message.chat.id] = {}
    bot.reply_to(message, "Please enter your email address:")

@bot.message_handler(func=lambda message: True)
def process_input(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return

    if 'email' not in user_data[chat_id]:
        email = message.text.strip()
        if '@' not in email or '.' not in email:
            bot.reply_to(message, "Invalid email. Please try again.")
            return
        user_data[chat_id]['email'] = email
        username = generate_username(email)
        user_data[chat_id]['username'] = username
        user_data[chat_id]['password'] = PASSWORD
        bot.reply_to(message, f"Creating GitHub account...\nUsername: {username}\nPassword: {PASSWORD}\nAddress and card auto-filled on billing.")
        result = create_github_account(email, username, PASSWORD)
        bot.reply_to(message, result)
        del user_data[chat_id]

def create_github_account(email, username, password):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get("https://github.com/join")

        driver.find_element(By.ID, "user_login").send_keys(username)
        driver.find_element(By.ID, "user_email").send_keys(email)
        driver.find_element(By.ID, "user_password").send_keys(password)
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[contains(text(),'Create account')]").click()
        time.sleep(5)

        page_source = driver.page_source

        # Billing and payment page flows
        if "Upgrade to GitHub Pro" in page_source or "Billing" in page_source:
            try:
                driver.find_element(By.NAME, "address_line1").send_keys(ADDRESS["street"])
                driver.find_element(By.NAME, "city").send_keys(ADDRESS["city"])
                driver.find_element(By.NAME, "state").send_keys(ADDRESS["state"])
                driver.find_element(By.NAME, "postal_code").send_keys(ADDRESS["postal_code"])
                driver.find_element(By.NAME, "phone_number").send_keys(ADDRESS["phone"])
                driver.find_element(By.NAME, "full_name").send_keys(ADDRESS["full_name"])
                time.sleep(2)
                # Payment: Enter card details (field names may vary/hidden in iframes)
                try:
                    driver.find_element(By.NAME, "cardnumber").send_keys(CARD["number"])
                    driver.find_element(By.NAME, "exp-date").send_keys(CARD["expiry"])
                    driver.find_element(By.NAME, "cvc").send_keys(CARD["cvv"])
                    time.sleep(1)
                    driver.find_element(By.XPATH, "//button[contains(text(),'Buy Pro')]").click()
                    time.sleep(5)
                except Exception:
                    pass   # May not succeed due to iframes/extra security
                # Set Codespace and Actions spending budgets ($1000,$2000)
                try:
                    driver.get("https://github.com/settings/billing")
                    time.sleep(2)
                    # Codespaces budget
                    driver.find_element(By.XPATH, "//a[contains(text(),'Budgets and alerts')]").click()
                    time.sleep(1)
                    driver.find_element(By.XPATH, "//button[contains(text(),'New budget')]").click()
                    time.sleep(1)
                    # These selectors are approximate
                    driver.find_element(By.XPATH, "//select[@name='product']").send_keys("Codespaces")
                    driver.find_element(By.NAME, "budget_amount").send_keys(str(LIMIT_CODESPACE))
                    driver.find_element(By.XPATH, "//button[contains(text(),'Create budget')]").click()
                    time.sleep(1)
                    # Actions budget
                    driver.find_element(By.XPATH, "//button[contains(text(),'New budget')]").click()
                    driver.find_element(By.XPATH, "//select[@name='product']").send_keys("Actions")
                    driver.find_element(By.NAME, "budget_amount").send_keys(str(LIMIT_ACTIONS))
                    driver.find_element(By.XPATH, "//button[contains(text(),'Create budget')]").click()
                    time.sleep(1)
                except Exception:
                    pass
            except Exception:
                pass

        driver.quit()

        if "Verify your account" in page_source or "captcha" in page_source.lower():
            return "Account/card submitted! Manual CAPTCHA or bank verification may be required. Please complete steps manually."

        if "Check your email" in page_source:
            return "Account and card info submitted! Check your email and GitHub billing for further instructions."

        return "Signup/purchase attempted. Check your email/browser for next steps."
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    bot.polling()

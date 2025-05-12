from flask import Flask
import requests
from bs4 import BeautifulSoup
import telegram
import json
import os
import threading
import time

app = Flask(__name__)

# Telegram Bot Token ve Chat ID
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"  # Buraya Telegram API token'ını yaz
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # Buraya Telegram Chat ID'ni yaz

# Duyuru siteleri ve birim adları
SITES = [
    {"url": "https://www.firat.edu.tr/tr/page/announcement", "unit": "F.Ü Genel"},
    {"url": "https://iibf.firat.edu.tr/announcements-all", "unit": "F.Ü İktisadi ve İdari Bilimler Fakültesi"},
    {"url": "https://muhendislikf.firat.edu.tr/announcements-all", "unit": "F.Ü Mühendislik Fakültesi"},
    {"url": "https://teknolojif.firat.edu.tr/announcements-all", "unit": "F.Ü Teknoloji Fakültesi"},
    {"url": "https://ogrencidb.firat.edu.tr/announcements-all", "unit": "F.Ü Öğrenci İşleri Daire Başkanlığı"},
    {"url": "https://ogrencidekanligi.firat.edu.tr/announcements-all", "unit": "F.Ü Öğrenci Dekanlığı"},
    {"url": "https://yazokuluyeni.firat.edu.tr/announcements-all", "unit": "F.Ü Yaz Okulu"},
    {"url": "https://egitimf.firat.edu.tr/tr/announcements-all", "unit": "F.Ü Eğitim Fakültesi"},
    {"url": "https://kutuphanedb.firat.edu.tr/announcements-all", "unit": "F.Ü Kütüphane Daire Başkanlığı"},
]

def read_seen_announcements():
    try:
        if os.path.exists("seen_announcements.json"):
            with open("seen_announcements.json", "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error reading seen announcements: {e}")
        return []

def write_seen_announcements(seen):
    try:
        with open("seen_announcements.json", "w") as f:
            json.dump(seen, f)
    except Exception as e:
        print(f"Error writing seen announcements: {e}")

def check_announcements():
    seen_announcements = read_seen_announcements()
    new_announcements = []

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    for site in SITES:
        try:
            # SSL doğrulamasını devre dışı bırak
            response = requests.get(site["url"], timeout=10, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            announcements = soup.find_all("div", class_="announcement-item")

            for ann in announcements:
                title = ann.find("h2").text.strip() if ann.find("h2") else "Başlık Bulunamadı"
                date = ann.find("span", class_="date").text.strip() if ann.find("span", class_="date") else "Tarih Bulunamadı"
                link = ann.find("a")["href"] if ann.find("a") else site["url"]

                if title not in seen_announcements:
                    seen_announcements.append(title)
                    new_announcements.append({
                        "unit": site["unit"],
                        "title": title,
                        "date": date,
                        "link": link
                    })

        except Exception as e:
            print(f"Error scraping {site['url']}: {e}")

    for ann in new_announcements:
        message = (
            f"{ann['unit']} Yeni Duyuru Paylaşıldı\n"
            f"Başlık: {ann['title']}\n"
            f"Tarih: {ann['date']}\n"
            f"Duyuruya ulaşmak için: {ann['link']}"
        )
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

    write_seen_announcements(seen_announcements)

def run_background_task():
    while True:
        print("Checking announcements...")
        check_announcements()
        time.sleep(60)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    # SSL doğrulama uyarılarını devre dışı bırak
    requests.packages.urllib3.disable_warnings()
    threading.Thread(target=run_background_task, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

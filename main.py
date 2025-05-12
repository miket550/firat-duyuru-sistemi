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
TELEGRAM_TOKEN = "7673163419:AAGEl0zOpSF93LpZj3d_Kr3o_1KKbHvI8Fs"
TELEGRAM_CHAT_ID = "944442637"

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
            print(f"Scraping site: {site['url']}")
            response = requests.get(site["url"], timeout=10, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Duyuruları bul (daha genel bir yapı kullanıyoruz)
            # Fırat Üniversitesi sitelerinde genellikle "list-item" veya benzeri bir sınıf olabilir
            announcements = soup.find_all("div", class_=["list-item", "announcement", "news-item", "card"])

            if not announcements:
                print(f"No announcements found on {site['url']}. HTML structure may have changed.")
                continue

            for ann in announcements:
                # Başlık için h3, h4 veya h2 etiketlerini kontrol et
                title_tag = ann.find(["h3", "h4", "h2"])
                title = title_tag.text.strip() if title_tag else "Başlık Bulunamadı"

                # Tarih için span veya div içinde date sınıfını kontrol et
                date_tag = ann.find(["span", "div"], class_=["date", "post-date", "meta-date"])
                date = date_tag.text.strip() if date_tag else "Tarih Bulunamadı"

                # Link için a etiketini kontrol et
                link_tag = ann.find("a")
                link = link_tag["href"] if link_tag and "href" in link_tag.attrs else site["url"]
                # Eğer link relatif bir URL ise tam URL'ye çevir
                if link.startswith("/"):
                    link = site["url"].rstrip("/") + link

                print(f"Found announcement: {title} on {date} - {link}")

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

    if new_announcements:
        for ann in new_announcements:
            message = (
                f"{ann['unit']} Yeni Duyuru Paylaşıldı\n"
                f"Başlık: {ann['title']}\n"
                f"Tarih: {ann['date']}\n"
                f"Duyuruya ulaşmak için: {ann['link']}"
            )
            print(f"Sending message to Telegram: {message}")
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    else:
        print("No new announcements found.")

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
    requests.packages.urllib3.disable_warnings()
    threading.Thread(target=run_background_task, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

import requests
from bs4 import BeautifulSoup
import telegram
import json
import time
import os

# Telegram Bot Token ve Chat ID (Bunları sen dolduracaksın)
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

# Önceki duyuruları saklamak için bir JSON dosyası
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

# Duyuruları tarama fonksiyonu
def check_announcements():
    seen_announcements = read_seen_announcements()
    new_announcements = []

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    for site in SITES:
        try:
            response = requests.get(site["url"], timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Duyuruları bul (sitelerin yapısına göre özelleştirildi)
            announcements = soup.find_all("div", class_="announcement-item")  # Örnek class, sitelere göre değişecek

            for ann in announcements:
                title = ann.find("h2").text.strip() if ann.find("h2") else "Başlık Bulunamadı"
                date = ann.find("span", class_="date").text.strip() if ann.find("span", class_="date") else "Tarih Bulunamadı"
                link = ann.find("a")["href"] if ann.find("a") else site["url"]

                # Eğer duyuru daha önce görülmediyse
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

    # Yeni duyuruları Telegram'a gönder
    for ann in new_announcements:
        message = (
            f"{ann['unit']} Yeni Duyuru Paylaşıldı\n"
            f"Başlık: {ann['title']}\n"
            f"Tarih: {ann['date']}\n"
            f"Duyuruya ulaşmak için: {ann['link']}"
        )
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

    # Görülen duyuruları güncelle
    write_seen_announcements(seen_announcements)

if __name__ == "__main__":
    while True:
        print("Checking announcements...")
        check_announcements()
        time.sleep(60)  # 1 dakikada bir kontrol et

import os
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import winsound

# --- KONFIGURASI ---
load_dotenv()
API_KEY = os.getenv('CMC_API_KEY')
TARGET_NETWORKS = ['Solana', 'BNB Smart Chain (BEP20)']
MAX_TOTAL_SUPPLY = 10_000_000
MIN_VOLUME_24H = 50_000
MAX_MARKET_CAP = 5_000_000
REFRESH_INTERVAL = 600 # 10 Menit

seen_coins = set()

def play_alarm():
    """Mengeluarkan suara beep jika koin ditemukan"""
    for _ in range(3):
         winsound.PlaySound(r"C:\Windows\Media\notify.wav", winsound.SND_FILENAME)
         time.sleep(0.1)

def check_rugcheck(mint_address):
    """Mengecek keamanan koin Solana via RugCheck API"""
    try:
        url = f"https://api.rugcheck.xyz/v1/tokens/{mint_address}/report/summary"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            score = data.get('score', 0)
            if score < 100: return "✅ Good"
            elif score < 500: return "⚠️ Warning"
            else: return "🚨 Danger"
        return "N/A"
    except:
        return "Error"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_logo():
    # Menggunakan r""" agar backslash logo tidak menyebabkan SyntaxWarning
    print(r"""
    #################################################################
    #                                                               #
    #    _____  ______  ____   ______  ______  _   __ ___ ___  __   #
    #   / ___/ / ____// __ \ / ____// ____// | / // ____//  _// /   #
    #   \__ \ / /    / /_/ // __/  / __/  /  |/ // /     / / / /    #
    #  ___/ // /___ / _, _/ ____/ / / / /___ / /|  // /_/ / / /     #
    # /____/ \____//_/ |_|/_____//_____//_/ |_/ \____//___/(_)      #
    #                                                               #
    #                   --- POWERED BY BAHA ---                     #
    #                                                               #
    #              [!] JANGAN TUTUP JENDELA INI [!]                 #
    #         Status: RUGCHECK AKTIF | INTERVAL: 10 MENIT           #
    #        ⚠️ SCREENING COIN SEDANG DI LAKUKAN CMC DYOR⚠️           #
    #################################################################
""")

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f"⏳ Menunggu scan berikutnya dalam {timer}...", end="\r")
        time.sleep(1)
        t -= 1

def process_screener():
    clear_screen()
    print_logo()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{now}] MEMULAI PEMINDAHAN PASAR MOHON TUNGGU ...⏳\n")
    
    try:
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {'start': '1', 'limit': '1000', 'convert': 'USD', 'sort': 'date_added', 'sort_dir': 'desc'}
        headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': API_KEY}
        
        response = requests.get(url, params=parameters, headers=headers)
        data = response.json()

        if 'data' not in data:
            print(f"❌ Error API: {data.get('status', {}).get('error_message')}")
            return

        new_finds = []
        for coin in data['data']:
            c_id = coin['id']
            if c_id in seen_coins: continue

            supply = coin.get('total_supply') or 0
            price = coin['quote']['USD'].get('price') or 0
            mcap = coin['quote']['USD'].get('market_cap') or 0
            vol = coin['quote']['USD'].get('volume_24h') or 0
            platform = coin.get('platform')
            
            net = platform.get('name') if platform else "Native"
            ca = platform.get('token_address') if platform else "N/A"

            net_match = any(target.lower() in net.lower() for target in TARGET_NETWORKS)
            
            if net_match and supply <= MAX_TOTAL_SUPPLY and vol >= MIN_VOLUME_24H:
                if mcap == 0 or mcap <= MAX_MARKET_CAP:
                    
                    rug_status = "N/A"
                    if "solana" in net.lower() and ca != "N/A":
                        # Spasi tambahan setelah teks agar tidak menempel
                        print(f"🛡️  ✅ Memeriksa RugCheck untuk {coin['symbol']}  ")
                        rug_status = check_rugcheck(ca)

                    # Menambahkan kembali Network dan Supply dengan formatting lebar kolom
                    new_finds.append({
                        'Time': datetime.now().strftime('%H:%M'),
                        'Symbol': f"{coin['symbol']:<8}",
                        'Network': f"{net:<15}",
                        'Price': f" ${price:<14.8f}",
                        'RugCheck': f" {rug_status:<10}",
                        'Vol_24h': f" ${vol:>11,.0f}",
                        'Supply': f" {supply:>12,.0f}",
                        'CA': f"  {ca}"
                    })
                    seen_coins.add(c_id)

        if new_finds:
            df = pd.DataFrame(new_finds)
            # Pastikan \n berada di dalam tanda kutip untuk menghindari SyntaxError
            print("\n" + "=" * 40 + "\n")
            print("🚀 TEMUAN BARU! \n")
            
            # Pengaturan agar tabel lebar tidak terpotong di terminal
            pd.set_option('display.max_colwidth', None)
            pd.set_option('display.expand_frame_repr', False)
            pd.set_option('display.unicode.east_asian_width', True) 
            
            print(df.to_string(index=False))
            print("\n" + "=" * 40 + "\n")
            
            play_alarm()
            df.to_csv('history_log.csv', mode='a', header=not os.path.exists('history_log.csv'), index=False)
        else:
            print("Belum ada koin baru yang cocok kriteria.")

    except Exception as e:
        print(f"\n❌ Terjadi gangguan: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ API Key tidak ditemukan! Isi dulu di file .env")
    else:
        while True:
            process_screener()
            print("\n" + "-" * 100)
            countdown(REFRESH_INTERVAL)
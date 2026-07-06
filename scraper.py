import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "http://quotes.toscrape.com/page/{}/"
CSV_PATH = "quotes.csv"
SAVE_EVERY = 5   
MAX_PAGES = 50  
TIMEOUT = 10     
MAX_RETRIES = 3  

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def fetch_page(url):
    """Ambil satu halaman dengan retry + timeout. Return response, atau None kalau gagal total."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            return response
        except requests.exceptions.Timeout:
            print(f"  Timeout saat ambil {url} (percobaan {attempt}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError:
            print(f"  Gagal konek ke {url} (percobaan {attempt}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as e:
 
            print(f"  Error tak terduga saat ambil {url}: {e} (percobaan {attempt}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES:
            time.sleep(1) 

    return None


def save_partial(all_data):
    """Simpan progres saat ini ke CSV, dipanggil secara berkala & saat interrupt."""
    if not all_data:
        return
    df = pd.DataFrame(all_data)
    df.to_csv(CSV_PATH, index=False)


def scrape_all_pages():
    all_data = []
    page = 1
    previous_first_quote = None

    while page <= MAX_PAGES:
        url = BASE_URL.format(page)
        response = fetch_page(url)

        if response is None:
            print(f"Gagal ambil page {page} setelah {MAX_RETRIES} percobaan, berhenti.")
            break

        if response.status_code != 200:
            print(f"Status code {response.status_code} di page {page}, berhenti.")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        quote_blocks = soup.find_all("div", class_="quote")

        if not quote_blocks:
            print(f"Page {page} kosong (tidak ada quote), berhenti.")
            break

        first_quote_text = quote_blocks[0].find("span", class_="text").get_text(strip=True)
        if first_quote_text == previous_first_quote:
            print(f"Page {page} isinya sama dengan page sebelumnya, kemungkinan sudah berulang. Berhenti.")
            break
        previous_first_quote = first_quote_text

        for block in quote_blocks:
            text = block.find("span", class_="text").get_text(strip=True)
            author = block.find("small", class_="author").get_text(strip=True)
            tags = [tag.get_text(strip=True) for tag in block.find_all("a", class_="tag")]

            all_data.append({
                "quote": text,
                "author": author,
                "tags": ", ".join(tags)
            })

        print(f"Page {page} selesai, total quotes terkumpul: {len(all_data)}")

        if page % SAVE_EVERY == 0:
            save_partial(all_data)
            print(f"  -> progres disimpan sementara ke {CSV_PATH}")

        page += 1
        time.sleep(0.5)

    return all_data


if __name__ == "__main__":
    data = []
    try:
        data = scrape_all_pages()
    except KeyboardInterrupt:
        print("\nDihentikan manual (Ctrl+C). Menyimpan data yang sudah terkumpul...")
    finally:
        save_partial(data)
        print(f"\nSelesai! {len(data)} quotes disimpan ke {CSV_PATH}")
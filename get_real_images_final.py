import urllib.request
import os

def download_image_robustly(url, filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'referer': 'https://www.google.com/'
    }
    try:
        print(f"Downloading {url}...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        print(f"Success: {filename} ({os.path.getsize(filename)} bytes)")
        return True
    except Exception as e:
        print(f"Error {filename}: {e}")
        return False

def main():
    dest_dir = "storage/evidence"
    os.makedirs(dest_dir, exist_ok=True)
    
    # Wikimedia Original URLs (Not thumbs, which are more likely to be throttled)
    images = {
        "X-123_pre_work_site.jpg": "https://upload.wikimedia.org/wikipedia/commons/e/ef/Oil_Well_Pump_Jack.jpg",
        "Z-789_leakage_cellar.jpg": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Oil_spill_on_the_ground.jpg"
    }
    
    for filename, url in images.items():
        download_image_robustly(url, os.path.join(dest_dir, filename))

if __name__ == "__main__":
    main()

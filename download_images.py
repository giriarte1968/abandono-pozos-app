import urllib.request
import os

def download_image(url, filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        print(f"Attempting to download {url}...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        print(f"Success: {filename} ({os.path.getsize(filename)} bytes)")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

def main():
    dest_dir = "storage/evidence"
    os.makedirs(dest_dir, exist_ok=True)
    
    # Stable Pexels URLs (Industrial/Oil theme)
    images = {
        "X-123_pre_work_site.jpg": "https://images.pexels.com/photos/162534/oil-pumping-extraction-petroleum-fossil-fuel-162534.jpeg?auto=compress&cs=tinysrgb&w=800",
        "Z-789_leakage_cellar.jpg": "https://images.pexels.com/photos/2449491/pexels-photo-2449491.jpeg?auto=compress&cs=tinysrgb&w=800",
        "M-555_capped_wellhead.jpg": "https://images.pexels.com/photos/247763/pexels-photo-247763.jpeg?auto=compress&cs=tinysrgb&w=800"
    }
    
    for filename, url in images.items():
        download_image(url, os.path.join(dest_dir, filename))

if __name__ == "__main__":
    main()

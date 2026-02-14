import requests
import os

def download_real_image(url, filename):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
    }
    try:
        print(f"Downloading from {url}...")
        response = requests.get(url, headers=headers, timeout=20, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Success: {filename} ({os.path.getsize(filename)} bytes)")
            return True
        else:
            print(f"Failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    dest_dir = "storage/evidence"
    os.makedirs(dest_dir, exist_ok=True)
    
    images = {
        "X-123_pre_work_site.jpg": "https://images.pexels.com/photos/162534/oil-pumping-extraction-petroleum-fossil-fuel-162534.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "Z-789_leakage_cellar.jpg": "https://images.pexels.com/photos/2449491/pexels-photo-2449491.jpeg?auto=compress&cs=tinysrgb&w=1200",
        "M-555_capped_wellhead.jpg": "https://images.pexels.com/photos/247763/pexels-photo-247763.jpeg?auto=compress&cs=tinysrgb&w=1200"
    }
    
    for filename, url in images.items():
        download_real_image(url, os.path.join(dest_dir, filename))

if __name__ == "__main__":
    main()

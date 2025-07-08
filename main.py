import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm

# Speed optimization using adapter for connection reuse
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount('https://', adapter)
session.mount('http://', adapter)

def download_apk(package_name, output_name=None):
    headers = {"User-Agent": "Mozilla/5.0"}

    download_page = f"https://apkpure.net/{package_name.replace('.', '-')}/{package_name}/download"
    resp = session.get(download_page, headers=headers, timeout=5)

    if resp.status_code != 200 or "We couldn't find that page" in resp.text:
        print("[-] APK not available at apkpure.net")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    link = soup.find("a", href=re.compile(r"https://.*?/b/APK/"))
    if not link:
        print("[-] Direct download link not found.")
        return

    redirect_url = link["href"]
    final = session.get(redirect_url, headers=headers, allow_redirects=False, timeout=5)
    if final.status_code != 302 or "Location" not in final.headers:
        print("[-] Failed to get final APK link.")
        return

    apk_url = final.headers["Location"]
    print(f"[+] Final APK URL: {apk_url}")

    apk_response = session.get(apk_url, headers=headers, stream=True, timeout=15)
    if apk_response.status_code == 200:
        filename = f"{output_name or package_name}.apk"
        total = int(apk_response.headers.get("Content-Length", 0))
        with open(filename, "wb") as f, tqdm(
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024
        ) as bar:
            for chunk in apk_response.iter_content(chunk_size = 2 * 1024 * 1024):  # 1MB chunks
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        print(f"[+] APK downloaded: {filename}")

if __name__ == "__main__":
    pkg = input("Enter package name (e.g., com.zerodha.varsity): ").strip()
    name = input("Enter output APK name (press Enter to use default): ").strip()
    download_apk(pkg, output_name=name if name else None)

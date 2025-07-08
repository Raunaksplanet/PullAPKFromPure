import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm

def download_apk(package_name):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    download_page = f"https://apkpure.net/{package_name.replace('.', '-')}/{package_name}/download"
    resp = requests.get(download_page, headers=headers, timeout=10)

    if resp.status_code != 200 or "We couldn't find that page" in resp.text:
        print("[-] APK not available at apkpure.net")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    link = soup.find("a", href=re.compile(r"https://.*?/b/APK/"))
    if not link:
        print("[-] Direct download link not found.")
        return

    redirect_url = link["href"]
    final = requests.get(redirect_url, headers=headers, allow_redirects=False, timeout=10)
    if final.status_code != 302 or "Location" not in final.headers:
        print("[-] Failed to get final APK link.")
        return

    apk_url = final.headers["Location"]
    print(f"[+] Final APK URL: {apk_url}")

    # Fast download using larger chunks
    apk_response = requests.get(apk_url, headers=headers, stream=True, timeout=30)
    if apk_response.status_code == 200:
        filename = f"{package_name}.apk"
        total = int(apk_response.headers.get("Content-Length", 0))
        with open(filename, "wb") as f, tqdm(
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024
        ) as bar:
            for chunk in apk_response.iter_content(chunk_size=256 * 1024):  # 256 KB
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        print(f"[+] APK downloaded: {filename}")


if __name__ == "__main__":
    pkg = input("Enter package name (e.g., com.zerodha.varsity): ").strip()
    download_apk(pkg)

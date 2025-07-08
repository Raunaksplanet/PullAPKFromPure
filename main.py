import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import argparse
import os
from tqdm.asyncio import tqdm


headers = {"User-Agent": "Mozilla/5.0"}

async def fetch(session, url):
    async with session.get(url, headers=headers, timeout=10) as resp:
        return await resp.text()

async def get_final_apk_url(session, package_name):
    url = f"https://apkpure.net/{package_name.replace('.', '-')}/{package_name}/download"
    html = await fetch(session, url)
    if "We couldn't find that page" in html:
        print(f"[-] {package_name}: Not found")
        return None

    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("a", href=re.compile(r"https://.*?/b/APK/"))
    if not link:
        print(f"[-] {package_name}: Direct download link not found")
        return None

    redirect = await session.get(link["href"], headers=headers, allow_redirects=False)
    if redirect.status != 302:
        print(f"[-] {package_name}: No redirect to APK")
        return None

    return redirect.headers.get("Location")

async def download_apk(session, package_name, output_name=None):
    url = await get_final_apk_url(session, package_name)
    if not url:
        return

    filename = f"{output_name or package_name}.apk"
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            total = int(resp.headers.get("Content-Length", 0))
            with open(filename, "wb") as f:
                bar = tqdm(total=total, unit='B', unit_scale=True, desc=filename)
                async for chunk in resp.content.iter_chunked(2 * 1024 * 128):  # 128KB chunk
                    f.write(chunk)
                    bar.update(len(chunk))
                bar.close()
            print(f"[✓] Downloaded: {filename}")
        else:
            print(f"[-] {package_name}: Failed to download")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", nargs="?", help="Single package name (e.g. com.whatsapp)")
    parser.add_argument("-l", "--list", help="File with list of package names")
    args = parser.parse_args()

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        if args.list:
            if not os.path.exists(args.list):
                print("[-] List file not found.")
                return
            with open(args.list, "r") as f:
                pkgs = [line.strip() for line in f if line.strip()]
            await asyncio.gather(*(download_apk(session, pkg) for pkg in pkgs))
        elif args.package:
            name = input("Enter output name (press Enter for default): ").strip()
            await download_apk(session, args.package, name if name else None)

if __name__ == "__main__":
    asyncio.run(main())

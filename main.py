import os
import time
from datetime import datetime
from typing import Dict, List

import requests


def fetch_latest_news(session: requests.Session) -> List[Dict]:
    url = "https://www.nhkg.tp.edu.tw/nss/site/main/storage/5a9759adef37531ea27bf1b0/y635Ty46272/find"
    now_ms = int(time.time() * 1000)
    one_day_ms = 24 * 60 * 60 * 1000
    since_ms = now_ms - one_day_ms
    payload = {
        "option": {
            "number": 10,
            "sort": {
                "released": 1,
                "top": -1,
                "stime": -1,
                "mtime": -1,
                "ctime": -1,
                "dtime": -1,
            },
            "page": 1,
            "query": [
                {
                    "between": {
                        "max": "dtime",
                        "min": "stime",
                        "value": since_ms,
                    },
                    "match": {"released": True, "status": "passed", "show": True},
                }
            ],
        },
        "vector": "private",
        "static": False,
    }
    response = session.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("result", [])


def build_summary(items: List[Dict]) -> str:
    if not items:
        return "臺北市立南海實驗幼兒園：目前沒有最新消息。"

    lines = ["臺北市立南海實驗幼兒園 最新消息（最新 10 則）:"]
    for item in items:
        data = item.get("data", {})
        title = data.get("name") or item.get("title") or "未命名"
        link = data.get("link") or data.get("url") or item.get("link") or item.get("url") or ""
        lines.append(f"- {title}{f' ({link})' if link else ''}")
    return "\n".join(lines)


def send_telegram_message(message: str) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print(
            datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "Telegram 設定缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID。",
        )
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/85.0.4183.83 Safari/537.36"
            )
        }
    )
    items = fetch_latest_news(session)
    if items:
        message = build_summary(items)
        send_telegram_message(message)
    else:
        print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "No announcements found.")
    print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "Fetch Success.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "Fetch Failed.", error)

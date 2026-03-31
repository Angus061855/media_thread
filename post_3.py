import os
import re
import time
import requests

# ── 環境變數 ──────────────────────────────────────────
NOTION_TOKEN       = os.environ["NOTION_TOKEN"]
NOTION_POST_DB_ID  = os.environ["NOTION_DATABASE_ID_3"]
THREADS_USER_ID    = os.environ["THREADS_USER_ID"]
THREADS_TOKEN      = os.environ["IG_ACCESS_TOKEN"]

def get_pending_posts():
    url = f"https://api.notion.com/v1/databases/{NOTION_POST_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    payload = {}  # ← 不加 filter，撈全部
    res = requests.post(url, headers=headers, json=payload).json()

    # 印出原始狀態資料
    if res.get("results"):
        page = res["results"][0]
        print("狀態欄位原始資料：", page["properties"].get("狀態"))

    return res.get("results", [])

def get_content_from_property(page):
    rich_text = page["properties"].get("內容", {}).get("rich_text", [])
    return "".join([t["plain_text"] for t in rich_text])

def update_status(page_id, status="已發"):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    requests.patch(url, headers=headers, json={"properties": {"狀態": {"status": {"name": status}}}})

def post_to_threads(content):
    posts = re.split(r'§\d+', content)
    posts = [p.strip() for p in posts if p.strip()]
    last_published_id = ""

    for i, text in enumerate(posts):
        text = text.replace("\\n", "\n")
        while len(text.encode('utf-8')) > 480:
            text = text[:-1]

        print(f"🚀 建立第 {i+1} 則 container...")
        create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        data = {"media_type": "TEXT", "text": text, "access_token": THREADS_TOKEN}
        if last_published_id:
            data["reply_to_id"] = last_published_id

        res = requests.post(create_url, data=data).json()
        creation_id = res.get("id")
        if not creation_id:
            raise Exception(f"建立 container 失敗（第 {i+1} 則）：{res}")
        time.sleep(5)

        pub_res = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
            data={"creation_id": creation_id, "access_token": THREADS_TOKEN}
        ).json()
        last_published_id = pub_res.get("id", "")
        print(f"第 {i+1} 則結果：", pub_res)
        time.sleep(3)

if __name__ == "__main__":
    print("=== _3 段落直接發模式 ===")
    posts = get_pending_posts()
    if not posts:
        print("沒有待發內容，結束。")
        exit(0)

    page = posts[0]
    page_id = page["id"]

    content = get_content_from_property(page)

    if not content.strip():
        print("內容為空，結束。")
        update_status(page_id, "已發")
        exit(0)

    print("📄 找到待發內容，開始發文...")
    post_to_threads(content)
    update_status(page_id, "已發")
    print("✅ 完成！")

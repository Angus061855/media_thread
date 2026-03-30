import os
import requests
from google import genai

# 環境變數
THREADS_USER_ID = os.environ.get("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# 從 Notion 取得一篇未發布的文章
def get_notion_article():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    body = {
        "filter": {
            "property": "發布狀態",
            "select": {
                "equals": "未發布"
            }
        },
        "page_size": 1
    }
    res = requests.post(url, headers=headers, json=body)
    data = res.json()
    results = data.get("results", [])
    if not results:
        print("沒有找到未發布的文章")
        return None, None
    page = results[0]
    page_id = page["id"]
    title = page["properties"]["名稱"]["title"][0]["text"]["content"]
    return page_id, title

# 用 Gemini 生成文案
def generate_post(title):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"請根據以下主題，寫一篇適合發布在 Threads 上的短文，約150字，語氣輕鬆自然：\n主題：{title}"
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

# 發布到 Threads
def post_to_threads(text):
    # Step 1: 建立 container
    url1 = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    params1 = {
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN
    }
    res1 = requests.post(url1, params=params1)
    container_id = res1.json().get("id")
    if not container_id:
        print("建立 container 失敗", res1.json())
        return False

    # Step 2: 發布
    url2 = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    params2 = {
        "creation_id": container_id,
        "access_token": THREADS_ACCESS_TOKEN
    }
    res2 = requests.post(url2, params=params2)
    print("發布結果：", res2.json())
    return True

# 把 Notion 文章標記為已發布
def mark_as_published(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    body = {
        "properties": {
            "發布狀態": {
                "select": {
                    "name": "已發布"
                }
            }
        }
    }
    requests.patch(url, headers=headers, json=body)
    print("已標記為已發布")

# 主程式
if __name__ == "__main__":
    page_id, title = get_notion_article()
    if title:
        print(f"文章標題：{title}")
        post_text = generate_post(title)
        print(f"生成文案：{post_text}")
        success = post_to_threads(post_text)
        if success:
            mark_as_published(page_id)


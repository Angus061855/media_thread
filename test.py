import os
import re
import time
import requests
import datetime
from google import genai

# ── 環境變數 ──────────────────────────────────────────
NOTION_TOKEN       = os.environ["NOTION_API_KEY"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
GEMINI_API_KEY     = os.environ["GEMINI_API_KEY"]
THREADS_USER_ID    = os.environ["THREADS_USER_ID"]
THREADS_TOKEN      = os.environ["THREADS_ACCESS_TOKEN"]

# ── 1. 從 Notion 撈所有已發過的主題 ──────────────────
def get_used_topics():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    used = []
    payload = {}
    while True:
        res = requests.post(url, headers=headers, json=payload).json()
        for page in res.get("results", []):
            props = page.get("properties", {})
            title_list = props.get("主題", {}).get("title", [])
            if title_list:
                used.append(title_list[0]["plain_text"])
        if not res.get("has_more"):
            break
        payload["start_cursor"] = res["next_cursor"]
    return used

# ── 2. 用 Gemini 自己想題材，再產生七則貼文內容 ────────
def generate_post(used_topics):
    client = genai.Client(api_key=GEMINI_API_KEY)

    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "（目前沒有已用主題）"

    prompt = f"""
你是一位在八大行業做了7年的男性經紀人，現在在 Threads 上連續發文，目的是幫助想入行或已經在行業裡的女生保護自己、避免被黑心經紀騙。

以下是已經用過的主題，【全部禁止重複】：
{used_str}

【第一步：自己想題材】
請根據以下方向，自由發揮，想一個還沒用過、有吸引力的新主題。
不要侷限在固定清單裡，可以從真實情境、常見誤解、心理操控、財務陷阱、職場安全、合約漏洞、入行心態等任何角度切入。
只要是能幫助女生保護自己的題材，都可以。

【角色設定】
- 性別：男
- 身份：八大經紀人，做了7年
- 口吻：像一個有經驗的前輩在跟朋友說話，不說教、不高高在上
- 定位：誠實、透明、敢講真話、保護小姐

【文章結構】（七則連發）
- 第一則：衝擊性開場，打破常見認知，製造懸念，引發好奇
- 第二則：具體案例故事，有時間點、有對話、有細節
- 第三則：深化觀點，解釋現象背後的原因和機制
- 第四則：第二個案例或延伸說明，加深複雜度
- 第五則：實用建議，越細節越好，可操作
- 第六則：第三個案例或強化論點，有對話、有結果
- 第七則：收尾昇華，重複核心觀念，引導留言或私訊

【字數規則】
- 每則嚴格控制在 120-140 個中文字以內
- 總字數 840-980 字
- 寧可寫少，不要超過

【語言風格】
- 用「妳」稱呼讀者
- 台灣口語，說人話，不用專業術語
- 短句為主，每句不超過 20 字
- 遇到句號就換行並空一行
- 大量使用「妳」「我」「妳們」，製造一對一對話感
- 重要觀念重複三次強調
- 對話用「她說」「我說」推動故事，有來有往

【案例設計規則】
- 每個案例都要有：具體時間點 + 具體數字 + 對話 + 結果
- 案例結構：問題出現 → 當事人的選擇 → 結果 → 教訓
- 至少 2 個不同案例，遞進式鋪陳

【說服邏輯】
- 先說「不這樣做會怎樣」，再給解方
- 用對比手法：別的經紀怎麼做 vs 我怎麼做
- 建立權威：「我做了7年」「我看過太多這種案例」

【格式規則】
- 直接輸出文章內容，不要用任何 codeblock 包起來
- 每則開頭單獨一行寫「§1」「§2」...「§7」作為分隔標記
- 遇到句號就換行並空一行
- 禁用：「——」「[1]」「[2]」等引用標籤、emoji、粗體、斜體
- 標點符號全部使用全形（，。？！：）
- 只輸出文章內容，不要加任何說明、標題、編號

【嚴格禁止的 AI 感用語】
禁止使用：他笑著搖搖頭、我愣住了、他苦笑著說、頓了頓、深吸一口氣、若有所思、眼神黯淡下來、不是⋯而是⋯、更扯的是、意味著

【行動呼籲規則】
- 最後一則必須引導「如果妳需要，可以來找我」
- 語氣是邀請，不是推銷

輸出格式：
第一行輸出「主題：[你選的主題]」，空一行後開始輸出七則貼文內容。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()

# ── 3. 從貼文內容擷取主題文字 ────────────────────────
def extract_topic(post_text):
    lines = post_text.strip().split("\n")
    for line in lines:
        if line.startswith("主題："):
            return line.replace("主題：", "").strip()
    return "未知主題"

# ── 4. 用 reply_to_id 串成同一篇串文發到 Threads ──────
def post_to_threads(post_text):
    lines = post_text.strip().split("\n")
    content_lines = []
    skip_topic = True
    for line in lines:
        if skip_topic and line.startswith("主題："):
            skip_topic = False
            continue
        content_lines.append(line)
    content = "\n".join(content_lines).strip()

    posts = re.split(r'§\d+', content)
    posts = [p.strip() for p in posts if p.strip()]

    first_post_id = ""
    last_published_id = ""

    for i, text in enumerate(posts):
        # 確保換行正確
        text = text.replace("\\n", "\n")

        # 超過 490 字元強制截斷（Threads 上限 500）
        if len(text) > 490:
            text = text[:490]

        print(f"🚀 建立第 {i+1} 則 container（{len(text)} 字元）...")

        create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        data = {
            "media_type": "TEXT",
            "text": text,
            "access_token": THREADS_TOKEN,
        }

        if last_published_id:
            data["reply_to_id"] = last_published_id

        res = requests.post(create_url, data=data).json()
        creation_id = res.get("id")
        if not creation_id:
            raise Exception(f"建立 container 失敗（第 {i+1} 則）：{res}")

        time.sleep(5)

        print(f"📤 發布第 {i+1} 則...")
        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        pub_res = requests.post(publish_url, data={
            "creation_id": creation_id,
            "access_token": THREADS_TOKEN,
        }).json()

        published_id = pub_res.get("id", "")
        print(f"第 {i+1} 則發文結果：", pub_res)

        if i == 0:
            first_post_id = published_id

        last_published_id = published_id
        time.sleep(3)

    return first_post_id

# ── 5. 把新主題記錄進 Notion ─────────────────────────
def save_to_notion(topic, post_text, post_id):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "主題": {
                "title": [{"text": {"content": topic}}]
            },
            "貼文內容": {
                "rich_text": [{"text": {"content": post_text[:2000]}}]
            },
            "貼文 ID": {
                "rich_text": [{"text": {"content": post_id}}]
            },
            "發文時間": {
                "date": {"start": now}
            }
        }
    }
    res = requests.post(url, headers=headers, json=payload)
    print("Notion 回應狀態：", res.status_code)

# ── 主程式 ────────────────────────────────────────────
if __name__ == "__main__":
    print("📥 撈取已用主題...")
    used_topics = get_used_topics()
    print(f"共 {len(used_topics)} 個已用主題")

    print("✍️ 產生新貼文...")
    post_text = generate_post(used_topics)
    print("貼文內容：\n", post_text)

    topic = extract_topic(post_text)
    print("📌 本次主題：", topic)

    print("🚀 發文到 Threads（七則串文）...")
    first_post_id = post_to_threads(post_text)

    print("📝 記錄主題到 Notion：", topic)
    save_to_notion(topic, post_text, first_post_id)

    print("✅ 完成！")

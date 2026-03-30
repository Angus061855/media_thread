name: Instagram Auto Post

on:
  workflow_dispatch:
  schedule:
    # 自動模式（Gemini 自由發揮）
    - cron: '0 9 * * *'    # 台灣時間 17:00
    - cron: '0 13 * * *'   # 台灣時間 21:00
    - cron: '0 15 * * *'   # 台灣時間 23:00
    # 待發模式（從 Notion 撈）
    - cron: '0 10 * * *'   # 台灣時間 18:00
    - cron: '0 14 * * *'   # 台灣時間 22:00
    - cron: '0 16 * * *'   # 台灣時間 00:00

jobs:
  post-auto:
    if: |
      github.event_name == 'schedule' && (
        github.event.schedule == '0 9 * * *' ||
        github.event.schedule == '0 13 * * *' ||
        github.event.schedule == '0 15 * * *'
      )
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run auto post
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          IG_ACCESS_TOKEN: ${{ secrets.IG_ACCESS_TOKEN }}
          IG_USER_ID: ${{ secrets.IG_USER_ID }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
          NOTION_PENDING_DATABASE_ID: ${{ secrets.NOTION_PENDING_DATABASE_ID }}
          POST_MODE: auto
        run: python test.py

  post-pending:
    if: |
      github.event_name == 'schedule' && (
        github.event.schedule == '0 10 * * *' ||
        github.event.schedule == '0 14 * * *' ||
        github.event.schedule == '0 16 * * *'
      )
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pending post
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          IG_ACCESS_TOKEN: ${{ secrets.IG_ACCESS_TOKEN }}
          IG_USER_ID: ${{ secrets.IG_USER_ID }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
          NOTION_PENDING_DATABASE_ID: ${{ secrets.NOTION_PENDING_DATABASE_ID }}
          POST_MODE: pending
        run: python test.py

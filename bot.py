import os
import json
import re
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "data.json"


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_date(mmdd):
    return f"{mmdd[:2]}월 {mmdd[2:]}일"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "/id":
        await update.message.reply_text(
            f"채팅 ID: {update.effective_chat.id}\n"
            f"채팅 타입: {update.effective_chat.type}\n"
            f"채팅명: {update.effective_chat.title}"
        )
        return

    if text == "/오늘":
        today = datetime.now().strftime("%m%d")

        data = load_data()

        if today not in data:
            await update.message.reply_text(
                "오늘 등록된 출근자가 없습니다."
            )
            return

        names = "\n".join(
            [f"• {name}" for name in data[today]]
        )

        await update.message.reply_text(
            f"📢 금일 출근자\n\n{names}"
        )
        return

    if text == "/스케줄":
        data = load_data()

        if not data:
            await update.message.reply_text(
                "등록된 스케줄이 없습니다."
            )
            return

        result = "📅 현재 스케줄\n\n"

        for date in sorted(data.keys()):
            result += f"{date[:2]}/{date[2:]}\n"
            result += "\n".join(
                [f"• {name}" for name in data[date]]
            )
            result += "\n\n"

        await update.message.reply_text(result)
        return

    if text == "/도움말":
        await update.message.reply_text(
            "/0610 성민 영재\n"
            "→ 등록 또는 수정\n\n"
            "/0610\n"
            "→ 날짜 조회\n\n"
            "/취소 0610\n"
            "→ 삭제\n\n"
            "/오늘\n"
            "→ 오늘 출근자\n\n"
            "/스케줄\n"
            "→ 전체 스케줄\n\n"
            "/id\n"
            "→ 그룹 정보"
        )
        return

    if text.startswith("/취소"):
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text(
                "사용법: /취소 0610"
            )
            return

        date = parts[1]

        data = load_data()

        if date in data:
            del data[date]

            save_data(data)

            await update.message.reply_text(
                f"✅ {format_date(date)} 삭제 완료"
            )
        else:
            await update.message.reply_text(
                "등록된 스케줄이 없습니다."
            )

        return

    match_lookup = re.match(r"^/(\d{4})$", text)

    if match_lookup:
        date = match_lookup.group(1)

        data = load_data()

        if date not in data:
            await update.message.reply_text(
                "등록된 스케줄이 없습니다."
            )
            return

        names = "\n".join(
            [f"• {name}" for name in data[date]]
        )

        await update.message.reply_text(
            f"📅 {format_date(date)}\n\n{names}"
        )

        return

    match_register = re.match(
        r"^/(\d{4})\s+(.+)$",
        text
    )

    if match_register:
        date = match_register.group(1)

        names = match_register.group(2).split()

        names = list(dict.fromkeys(names))

        data = load_data()

        data[date] = names

        save_data(data)

        people = "\n".join(
            [f"• {name}" for name in names]
        )

        await update.message.reply_text(
            f"✅ {format_date(date)} 등록 완료\n\n{people}"
        )

        return


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT,
            handle_message
        )
    )

    print("Bot Started")

    app.run_polling()


if __name__ == "__main__":
    main()

import os
import json
import re
from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "data.json"

# 시청 홀덤 일정 그룹
GROUP_ID = -5123266102


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


async def daily_notification(context):
    today = datetime.now().strftime("%m%d")

    data = load_data()

    if today not in data:
        return

    names = "\n".join(
        [f"• {name}" for name in data[today]]
    )

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"📢 금일 출근자 알림\n\n{names}"
    )


async def cleanup_old_schedules(context):
    today = datetime.now().strftime("%m%d")

    data = load_data()

    new_data = {}

    for date, names in data.items():
        if date >= today:
            new_data[date] = names

    save_data(new_data)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # /id
    if text == "/id":
        await update.message.reply_text(
            f"채팅 ID: {update.effective_chat.id}\n"
            f"채팅 타입: {update.effective_chat.type}\n"
            f"채팅명: {update.effective_chat.title}"
        )
        return

    # /테스트
    if text == "/테스트":
        await daily_notification(context)
        return

    # /오늘
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

    # /스케줄
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

    # /도움말
    if text == "/도움말":
        await update.message.reply_text(
            "사용 가능한 명령어\n\n"
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
            "/테스트\n"
            "→ 자동 알림 테스트\n\n"
            "/id\n"
            "→ 그룹 정보"
        )
        return

    # /취소 0610
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

    # /0610 조회
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

    # /0610 성민 영재 등록
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

    # 매일 오전 10시 알림
    app.job_queue.run_daily(
        daily_notification,
        time=time(
            hour=10,
            minute=0,
            tzinfo=ZoneInfo("Asia/Seoul")
        )
    )

    # 매일 00:01 이전 일정 삭제
    app.job_queue.run_daily(
        cleanup_old_schedules,
        time=time(
            hour=0,
            minute=1,
            tzinfo=ZoneInfo("Asia/Seoul")
        )
    )

    print("Bot Started")

    app.run_polling()


if __name__ == "__main__":
    main()

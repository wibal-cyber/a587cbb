import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from questions.davlat import questions_davlat
from questions.mantiq import questions_mantiq
from questions.tarix import questions_tarix
from questions.game import questions_game

from utils.skills import calculate_iq, detect_skills
from utils.poll_sender import send_quiz_poll

BOT_TOKEN = "7946946712:AAFs4T4gJTwQZ2WyBNluaFFrwxyDzpYHuF0"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


CATEGORY_DATA = {
    "davlat": questions_davlat,
    "mantiq": questions_mantiq,
    "tarix": questions_tarix,
    "game": questions_game
}

user_state = {}


@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Davlatlar", callback_data="davlat")],
        [InlineKeyboardButton(text="🧠 Mantiq", callback_data="mantiq")],
        [InlineKeyboardButton(text="🏺 Tarix", callback_data="tarix")],
        [InlineKeyboardButton(text="🎮 Game", callback_data="game")],
    ])
    await message.answer("🧠 Qaysi bo‘limdan test boshlaymiz?", reply_markup=kb)


@dp.callback_query(F.data.in_(["davlat", "mantiq", "tarix", "game"]))
async def select_category(call: types.CallbackQuery):
    category = call.data


    selected = random.sample(CATEGORY_DATA[category], 10)

    user_state[call.from_user.id] = {
        "category": category,
        "questions": selected,
        "index": 0,
        "correct": 0,
        "wrong": 0,
        "category_scores": {"davlat": 0, "mantiq": 0, "tarix": 0, "game": 0}
    }

    await send_next_question(call.from_user.id)


async def send_next_question(user_id):
    data = user_state[user_id]

    chat_id = user_id


    if data["wrong"] >= 3:
        return await finish_test(chat_id, user_id)


    if data["index"] >= 15:
        return await finish_test(chat_id, user_id)

    savol = data["questions"][data["index"]]
    data["current_correct"] = savol["correct"]

    await send_quiz_poll(bot, chat_id, savol, savol["correct"])


@dp.poll_answer()
async def handle_poll(poll: types.PollAnswer):
    user_id = poll.user.id

    if user_id not in user_state:
        return

    data = user_state[user_id]
    selected = poll.option_ids[0]
    correct = data["current_correct"]


    if selected == correct:
        data["correct"] += 1
        data["category_scores"][data["category"]] += 1


    else:
        data["wrong"] += 1

    data["index"] += 1

    await send_next_question(user_id)


async def finish_test(chat_id, user_id):
    data = user_state[user_id]

    category = data["category"]
    correct = data["correct"]
    wrong = data["wrong"]
    category_score = data["category_scores"][category]


    iq, iq_level = calculate_iq(correct)


    if category_score >= 8:
        skill_text = "A'lo!"
    elif category_score >= 5:
        skill_text = "Yaxshi!"
    elif category_score >= 3:
        skill_text = "O‘rtacha."
    else:
        skill_text = "Past daraja."


    category_names = {
        "davlat": "🌍 Geografiya",
        "mantiq": "🧠 Mantiq",
        "tarix":  "🏺 Tarix",
        "game":   "🎮 Gaming"
    }

    text = (
        "🏁 <b>Test tugadi!</b>\n\n"
        f"✔️ To‘g‘ri javob: {correct}\n"
        f"❌ Xato javob: {wrong}\n\n"
        f"🧠 IQ: <b>{iq}</b> — {iq_level}\n\n"
        f"📘 Tanlangan yo‘nalish: {category_names[category]}\n"
        f"🔎 Yo‘nalish bo‘yicha baho: {skill_text}\n\n"
        "👉 Yangi test: /start"
    )

    await bot.send_message(chat_id, text, parse_mode="HTML")
    user_state.pop(user_id)


print("bot Start")
asyncio.run(dp.start_polling(bot))
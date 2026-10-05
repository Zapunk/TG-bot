# import asyncio
# import logging
# import os
# from io import BytesIO

# import qrcode
# from aiogram import Bot, Dispatcher, F
# from aiogram.filters import CommandStart
# from aiogram.types import (
#     BufferedInputFile,
#     CallbackQuery,
#     InlineKeyboardButton,
#     InlineKeyboardMarkup,
#     Message,
# )
# from dotenv import load_dotenv

# load_dotenv()

# BOT_TOKEN = os.environ["BOT_TOKEN"]
# # Ссылка из QR-кода банка (то, что "зашито" в QR, обычно https://qr.nspk.ru/...)
# PAYMENT_LINK = os.environ["PAYMENT_LINK"]

# QUESTION = "Хочешь просрать чирик?"
# GREETING = "Привет! Это бот, где можно потратить 10 рублей просто так. Ничего взамен не получишь 😈"

# dp = Dispatcher()


# def make_qr_png(data: str) -> bytes:
#     """Рисуем QR-код из ссылки и возвращаем PNG в виде байтов."""
#     img = qrcode.make(data)
#     buffer = BytesIO()
#     img.save(buffer, format="PNG")
#     return buffer.getvalue()


# QR_PNG = make_qr_png(PAYMENT_LINK)  # делаем один раз при старте


# def menu_keyboard() -> InlineKeyboardMarkup:
#     return InlineKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 InlineKeyboardButton(text="ДА", callback_data="yes"),
#                 InlineKeyboardButton(text="НЕТ", callback_data="no"),
#             ]
#         ]
#     )


# async def send_menu(message: Message) -> None:
#     await message.answer(QUESTION, reply_markup=menu_keyboard())


# @dp.message(CommandStart())
# async def start(message: Message) -> None:
#     await message.answer(GREETING)
#     await send_menu(message)


# @dp.callback_query(F.data == "no")
# async def answer_no(callback: CallbackQuery) -> None:
#     await callback.answer()
#     # убираем кнопки у старого вопроса, чтобы не жали по нескольку раз
#     await callback.message.edit_reply_markup(reply_markup=None)
#     await callback.message.answer("Ну ты и жмот 😡")
#     await send_menu(callback.message)


# @dp.callback_query(F.data == "yes")
# async def answer_yes(callback: CallbackQuery) -> None:
#     await callback.answer()
#     await callback.message.edit_reply_markup(reply_markup=None)
#     await callback.message.answer_photo(
#         BufferedInputFile(QR_PNG, filename="qr.png"),
#         caption="Ты настоящий герой! 🫡",
#     )
#     await send_menu(callback.message)


# async def main() -> None:
#     logging.basicConfig(level=logging.INFO)
#     bot = Bot(token=BOT_TOKEN)
#     await dp.start_polling(bot)


# if __name__ == "__main__":
#     asyncio.run(main())


import asyncio
import logging
import os
from io import BytesIO

import qrcode
from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
PAYMENT_LINK = os.environ["PAYMENT_LINK"]

QUESTION = "Хочешь просрать чирик?"
GREETING = "Привет! Это бот, где можно потратить 10 рублей просто так. Ничего взамен не получишь 😈"

dp = Dispatcher()

last_messages: dict[int, list[int]] = {}


def make_qr_png(data: str) -> bytes:
    """Рисуем QR-код из ссылки и возвращаем PNG в виде байтов."""
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


QR_PNG = make_qr_png(PAYMENT_LINK)


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="ДА", callback_data="yes"),
                InlineKeyboardButton(text="НЕТ", callback_data="no"),
            ]
        ]
    )


def remember(message: Message) -> None:
    """Запоминаем сообщение бота, чтобы потом его удалить."""
    last_messages.setdefault(message.chat.id, []).append(message.message_id)


async def cleanup(bot: Bot, chat_id: int) -> None:
    """Удаляем все запомненные сообщения бота в этом чате."""
    for message_id in last_messages.pop(chat_id, []):
        try:
            await bot.delete_message(chat_id, message_id)
        except TelegramBadRequest:
            pass


async def send_menu(message: Message) -> None:
    sent = await message.answer(QUESTION, reply_markup=menu_keyboard())
    remember(sent)


@dp.message(CommandStart())
async def start(message: Message, bot: Bot) -> None:
    await cleanup(bot, message.chat.id)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    greeting = await message.answer(GREETING)
    remember(greeting)
    await send_menu(message)


@dp.callback_query(F.data == "no")
async def answer_no(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    await cleanup(bot, callback.message.chat.id)
    sent = await callback.message.answer("Ну ты и жмот 😡")
    remember(sent)
    await send_menu(callback.message)


@dp.callback_query(F.data == "yes")
async def answer_yes(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    await cleanup(bot, callback.message.chat.id)
    sent = await callback.message.answer_photo(
        BufferedInputFile(QR_PNG, filename="qr.png"),
        caption="Ты настоящий герой! 🫡",
    )
    remember(sent)
    await send_menu(callback.message)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



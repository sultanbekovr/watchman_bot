import asyncio
import logging
import os
import re
import sys
from datetime import datetime, timedelta

import redis
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ChatPermissions, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

dp = Dispatcher()

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


async def button_create(button_num1: int, button_num2: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=f"Yes ({button_num1})",
        callback_data="Yes")
    )
    builder.add(InlineKeyboardButton(
        text=f"No ({button_num2})",
        callback_data="No")
    )

    return builder


async def get_counter_from_text(text) -> int:
    list_of_digits = re.findall(r'\d+', text)
    counter = int(list_of_digits[0])

    return counter


async def mute_user(chat_id: int, user: types.User) -> None:
    permissions = ChatPermissions(can_send_messages=False,
                                  can_send_audios=False,
                                  can_send_documents=False,
                                  can_send_photos=False,
                                  can_send_videos=False,
                                  can_send_video_notes=False,
                                  can_send_voice_notes=False,
                                  can_send_polls=False,
                                  can_send_other_messages=False,)

    await bot.restrict_chat_member(chat_id=chat_id,
                                   user_id=user.id,
                                   permissions=permissions,
                                   until_date=datetime.now() + timedelta(days=7))
    await bot.send_message(chat_id=chat_id,
                           text=f'Пользователь с айди {user.first_name} получт мут на 7 дней')


async def check_new_voice(user: types.User, message_id: int) -> bool:
    host = os.getenv('REDIS_HOST')
    port = os.getenv('REDIS_PORT')
    r = redis.Redis(host=host, port=port, decode_responses=True)
    if r.get(str(user.id) + str(message_id)) is not None:
        return False
    r.set(str(user.id) + str(message_id), 'true', ex=600)
    return True


@dp.message(Command('mute'))
async def echo_handler(message: types.Message) -> None:
    builder = await button_create(0, 0)

    await message.answer(f'Дать мут на 7 дней для {message.reply_to_message.from_user.first_name} (до 10 голосов)?', reply_markup=builder.as_markup(), reply_to_message_id=message.reply_to_message.message_id)


@dp.callback_query(F.data == 'Yes')
async def change_yes_button_data(callback: types.CallbackQuery):
    no_counter = await get_counter_from_text(callback.message.reply_markup.inline_keyboard[0][1].text)
    yes_counter = await get_counter_from_text(callback.message.reply_markup.inline_keyboard[0][0].text)

    new_voice = await check_new_voice(callback.from_user, callback.message.message_id)
    if new_voice:
        yes_counter += 1
        builder = await button_create(yes_counter, no_counter)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    else:
        await bot.answer_callback_query(callback_query_id=callback.id, text='Вы уже проголосовали')

    if yes_counter >= 3:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await mute_user(callback.message.chat.id, callback.message.reply_to_message.from_user)


@dp.callback_query(F.data == 'No')
async def change_no_button_data(callback: types.CallbackQuery):
    no_counter = await get_counter_from_text(callback.message.reply_markup.inline_keyboard[0][1].text)
    yes_counter = await get_counter_from_text(callback.message.reply_markup.inline_keyboard[0][0].text)

    new_voice = await check_new_voice(callback.from_user, callback.message.message_id)
    if new_voice:
        no_counter += 1
        builder = await button_create(yes_counter, no_counter)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    else:
        await bot.answer_callback_query(callback_query_id=callback.id, text='Вы уже проголосовали')

    if no_counter >= 10:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


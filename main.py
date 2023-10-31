import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import PollAnswer, ChatPermissions

# Bot token can be obtained via https://t.me/BotFather
TOKEN = os.getenv('BOT_TOKEN')

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

# Initialize Bot instance with a default parse mode which will be passed to all API calls
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


@dp.message(Command('mute'))
async def echo_handler(message: types.Message) -> None:
    user_id = message.from_user
    if user_id is not None:
        await message.answer_poll(question=f'Дать муть на 7 дней для {message.reply_to_message.from_user.first_name} ({message.reply_to_message.from_user.id}) ? (Нужно 10 голосов)',
                                  options=['Yes', 'No'],
                                  reply_to_message_id=message.reply_to_message.message_id,
                                  open_period=600)


@dp.poll()
async def poll_handler(poll: PollAnswer):
    text = poll.question
    user_id = text.split()[-5].replace('(', '').replace(')', '')
    if poll.options[0].voter_count == 10:
        permissions = ChatPermissions(can_send_messages=False,
                                      can_send_audios=False,
                                      can_send_documents=False,
                                      can_send_photos=False,
                                      can_send_videos=False,
                                      can_send_video_notes=False,
                                      can_send_voice_notes=False,
                                      can_send_polls=False,
                                      can_send_other_messages=False,)

        await bot.restrict_chat_member(chat_id='-1001592712917',
                                       user_id=user_id,
                                       permissions=permissions,
                                       until_date=datetime.now() + timedelta(days=7))

        await bot.send_message(chat_id='-1001592712917',
                               text=f'Пользователь с айди {user_id} получт мут на 7 дней')


async def main() -> None:
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


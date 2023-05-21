import configparser
import redis
from aiogram import Bot, Dispatcher, executor, types
import bot_common
config = configparser.ConfigParser()
config.read('bot.ini')
TOKEN = config["bot"]["tg_token"]
issues_link = ""

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
r = redis.Redis(decode_responses=True)


@dp.message_handler(commands=["start", "pomoc"])
async def send_welcome(message: types.Message):
    await message.reply("Cześć! Jestem botem. Pomogę Ci zarejestrować się w Awatarii. "
                        "Już za chwilę podam Ci nazwę użytkownika i hasło. Miłej gry."
                        "Pamiętaj aby nikomu nie udostępniać swojego hasła!\n"
                        "Aby się zarejestrować i uzyskać hasło, wpisz /rejestracja\n"
                        "Aby zmienić swoje hasło, wpisz /zmianahasla \n""Aby zresetować konto - "
                        f"wpisz /reset\n Wszelkie błędy zgłaszaj {issues_link}\n"
                        "Miłej gry!")


@dp.message_handler(commands=["rejestracja"])
async def password(message: types.Message):
    passwd = r.get(f"tg:{message.from_user.id}")
    if passwd:
        uid = r.get(f"auth:{passwd}")
    else:
        uid, passwd = bot_common.new_account(r)
        r.set(f"tg:{message.from_user.id}", passwd)
    await message.reply(f"Twoja nazwa użytkownika: {uid}\nTwoje hasło: {passwd}")


@dp.message_handler(commands=["zmianahasla"])
async def change_password(message: types.Message):
    passwd = r.get(f"tg:{message.from_user.id}")
    if not passwd:
        return await message.reply("Twoje konto nie zostało jeszcze utworzone. Użyj /rejestracja aby je utworzyć.")
    while True:
        new_passwd = bot_common.random_string()
        if r.get(f"auth:{new_passwd}"):
            continue
        break
    uid = r.get(f"auth:{passwd}")
    r.delete(f"auth:{passwd}")
    r.set(f"auth:{new_passwd}", uid)
    r.set(f"tg:{message.from_user.id}", new_passwd)
    await message.reply(f"Twoje nowe hasło: {new_passwd}")


@dp.message_handler(commands=["reset"])
async def reset(message: types.Message):
    passwd = r.get(f"tg:{message.from_user.id}")
    if not passwd:
        return await message.reply("Twoje konto nie zostało jeszcze utworzone. Użyj /rejestracja aby je utworzyć.")
    uid = r.get(f"auth:{passwd}")
    bot_common.reset_account(r, uid)
    await message.reply(f"Konto zostało zresetowane.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

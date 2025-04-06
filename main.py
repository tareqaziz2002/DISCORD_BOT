import discord
from discord.ext import commands
import os
from googletrans import Translator
import random
import asyncio
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
translator = Translator()

user_xp = {}
user_level = {}
user_skills = {}
user_comments = {}

auto_replies = {
    "hello": "Hi there!",
    "how are you": "I'm just a bot, but I'm doing great!",
    "bye": "Goodbye! See you soon.",
    "good morning": "Good morning sunshine!",
    "good night": "Sleep tight!",
    "who are you": "I'm your helpful Discord bot!",
    "what's up": "Just hanging out in the cloud.",
    "thanks": "You're welcome!",
    "lol": "Glad you found that funny!",
    "help": "How can I assist you today?",
    "i'm bored": "Wanna hear a joke?",
    "joke": "Why did the chicken join a band? Because it had the drumsticks!",
    "hi": "Hey there!",
    "no": "Why not?",
    "yes": "Great!",
    "maybe": "Hmm, uncertain much?",
    "ok": "Got it!",
    "cool": "Cool cool cool!",
    "nice": "Thanks! You're nice too!",
    "love you": "I love you too, in a code-y way!"
}

funny_lines = [
    "তুমি কি চা খেয়েছো আজ?",
    "তুমি হাসো অনেক সুন্দর করে!",
    "তোমার কথা না বললেই না!",
    "তুমি কি জানো, আমি তোমাকে খুব পছন্দ করি!",
    "তুমি কি ম্যাজিক জানো?",
    "তোমার চোখে কি WiFi আছে?",
    "তোমাকে দেখলেই মনে হয় হার্টবিট বেড়ে যায়!",
    "Are you Google? Because you’ve got everything I’m searching for.",
    "Do you have a name or can I call you mine?",
    "You’re like sunshine on a rainy day.",
    "You're the reason I check my phone every 5 minutes.",
    "You're like a dictionary – you add meaning to my life.",
    "You're not a camera, but every time I look at you, I smile.",
    "You must be a time traveler, because I see you in my future.",
    "If kisses were snowflakes, I’d send you a blizzard.",
    "You’re my daily dose of dopamine."
]

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    bot.loop.create_task(auto_message_task())

async def auto_message_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            text_channels = [c for g in bot.guilds for c in g.text_channels if c.permissions_for(g.me).send_messages]
            if text_channels:
                channel = random.choice(text_channels)
                line = random.choice(funny_lines)
                await channel.send(line)
        except Exception as e:
            print(f"Auto message error: {e}")
        await asyncio.sleep(300)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    user_id = message.author.id

    creator_questions = [
        "who is your creator", "who made you", "who is your developer",
        "তোমাকে কে বানাইছে", "তোমাকে কে বানিয়েছে", "তোমার developer কে"
    ]
    if any(q in content for q in creator_questions):
        if any(word in content for word in ["কে", "বাংলা", "বানাইছে", "বানিয়েছে"]):
            reply = "আমার নির্মাতা তারেক আজিজ। তিনি বাংলাদেশের কক্সবাজার থেকে।"
        else:
            reply = "My creator is Tareq Aziz. He is from Cox's Bazar, Bangladesh."
        await message.channel.send(reply)
        return

    user_xp[user_id] = user_xp.get(user_id, 0) + 10
    xp = user_xp[user_id]
    level = xp // 100
    if user_level.get(user_id, 0) < level:
        user_level[user_id] = level
        await message.channel.send(f"{message.author.display_name} just leveled up to Level {level}!")

    if content in auto_replies:
        await message.channel.send(auto_replies[content])

    emoji_list = ["😂", "🔥", "👍", "❤️", "😎", "🤖", "😘", "🥰", "😍", "💯"]
    try:
        await message.add_reaction(random.choice(emoji_list))
    except discord.errors.Forbidden:
        pass

    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def hi(ctx):
    await ctx.send(f"Hello {ctx.author.display_name}!")

@bot.command()
async def joke(ctx):
    await ctx.send("আমি শুনেছি তুমি বুদ্ধিমান! কিন্তু তুমি তো আমাকে চালাকি করতে এসেছো!")

@bot.command(aliases=["tr", "t"])
async def translate(ctx, *, arg):
    try:
        if '.' not in arg:
            await ctx.send("Usage: `!translate <text>. <language code>`")
            return
        parts = arg.rsplit('.', 1)
        text = parts[0].strip()
        dest = parts[1].strip().lower()

        supported_langs = {
            "bn": "Bengali", "en": "English", "ar": "Arabic", "hi": "Hindi", "es": "Spanish",
            "ja": "Japanese", "fr": "French", "de": "German", "zh-cn": "Chinese", "ru": "Russian",
            "it": "Italian", "pt": "Portuguese", "tr": "Turkish", "ko": "Korean", "ur": "Urdu",
            "fa": "Persian", "id": "Indonesian", "ms": "Malay", "pl": "Polish", "sv": "Swedish",
            "uk": "Ukrainian", "vi": "Vietnamese", "ta": "Tamil", "te": "Telugu"
        }

        if dest not in supported_langs:
            langs_list = ", ".join([f"`{k}` ({v})" for k, v in supported_langs.items()])
            await ctx.send(f"Supported language codes:
{langs_list}")
            return

        translated = translator.translate(text, dest=dest)
        await ctx.send(f"**Translated ({translated.src} → {translated.dest}):** {translated.text}")

    except Exception as e:
        await ctx.send(f"Translation error: `{e}`")

@bot.command()
async def level(ctx):
    user_id = ctx.author.id
    level = user_level.get(user_id, 0)
    xp = user_xp.get(user_id, 0)
    await ctx.send(f"{ctx.author.display_name}, you are Level {level} with {xp} XP.")

@bot.command()
async def setskill(ctx, skill: str, level: int):
    user_id = ctx.author.id
    user_skills.setdefault(user_id, {})[skill] = level
    await ctx.send(f"Set skill **{skill}** to level {level}.")

@bot.command()
async def myskills(ctx):
    user_id = ctx.author.id
    skills = user_skills.get(user_id, {})
    if not skills:
        await ctx.send("You have no skills set.")
        return
    msg = "\n".join([f"{k}: {v}" for k, v in skills.items()])
    await ctx.send(f"Your skills:\n{msg}")

@bot.command()
async def comment(ctx, *, msg: str):
    user_id = ctx.author.id
    user_comments.setdefault(user_id, []).append(msg)
    await ctx.send("Your comment has been saved.")

@bot.command()
async def mycomments(ctx):
    user_id = ctx.author.id
    comments = user_comments.get(user_id, [])
    if not comments:
        await ctx.send("You have no comments saved.")
        return
    await ctx.send("Your comments:\n" + "\n".join(comments[-5:]))

@bot.command()
async def guess(ctx):
    number = random.randint(1, 5)
    await ctx.send("Guess a number between 1 and 5.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        guess_msg = await bot.wait_for("message", check=check, timeout=10)
        guess = int(guess_msg.content)
        if guess == number:
            await ctx.send("Correct! You guessed it!")
        else:
            await ctx.send(f"Wrong! The number was {number}.")
    except asyncio.TimeoutError:
        await ctx.send("You took too long to guess!")

@bot.event
async def on_member_join(member):
    welcome_message = f"""Welcome to the **Rise of Kingdoms** community, {member.mention}!

Here you’ll meet players from all over the world — ready to build, battle, and grow together!

Feel free to introduce yourself and ask any questions. **Let the Kingdom rise with you!**"""
    for channel in member.guild.text_channels:
        if "welcome" in channel.name or "general" in channel.name:
            if channel.permissions_for(member.guild.me).send_messages:
                await channel.send(welcome_message)
                break

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))

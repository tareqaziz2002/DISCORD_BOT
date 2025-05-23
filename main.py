import discord
from discord.ext import commands
import os
import random
import asyncio
from googletrans import Translator
from textblob import TextBlob
import nltk
from flask import Flask
import threading

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")
translator = Translator()

user_xp = {}
user_level = {}
user_skills = {}
user_comments = {}
afk_users = {}
warnings = {}

bad_words = {
    "en": ["fuck", "shit", "bitch", "asshole", "bastard", "burn", "dog"],
    "bn": ["চুদ", "মাদারচোদ", "মাগী", "খারাপ", "হেই", "গালি", "হেলো"],
    "hi": ["गाली", "कुत्ता", "माँचोद", "बहनचोद", "शराबी"],
    "ur": ["گالی", "کتّا", "مچود", "ماں چود", "بہن چود"],
    "ar": ["شتيمة", "كلب", "أمك", "بذاءة"],
    "vi": ["chửi", "mày", "đụ", "lồn", "bậy bạ"],
    "es": ["puta", "mierda", "cabron", "perra"],
    "fr": ["pute", "merde", "connard", "salopard"]
}

supported_langs = {
    "bn": "Bengali", "en": "English", "ar": "Arabic", "hi": "Hindi",
    "es": "Spanish", "ja": "Japanese", "fr": "French", "de": "German",
    "zh-cn": "Chinese", "ru": "Russian", "it": "Italian", "pt": "Portuguese",
    "tr": "Turkish", "ko": "Korean", "ur": "Urdu", "fa": "Persian",
    "id": "Indonesian", "ms": "Malay", "pl": "Polish", "sv": "Swedish",
    "uk": "Ukrainian", "vi": "Vietnamese", "ta": "Tamil", "te": "Telugu"
}

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

async def send_warning(ctx, user_id, lang):
    warnings[user_id] = warnings.get(user_id, 0) + 1
    count = warnings[user_id]

    messages = {
        "en": [
            f"{ctx.author.mention}, this is your first warning!",
            f"{ctx.author.mention}, second warning! Be cautious!",
            f"{discord.utils.get(ctx.guild.members, guild_permissions__administrator=True).mention}, {ctx.author.mention} has been using inappropriate language repeatedly!"
        ],
        "bn": [
            f"{ctx.author.mention}, এটা প্রথম ওয়ার্নিং!",
            f"{ctx.author.mention}, আবার ওয়ার্নিং দিচ্ছি! সাবধান হও।",
            f"{discord.utils.get(ctx.guild.members, guild_permissions__administrator=True).mention}, {ctx.author.mention} বারবার খারাপ ভাষা ব্যবহার করছে!"
        ]
    }

    if count <= 2:
        await ctx.send(messages.get(lang, messages["en"])[count - 1])
    else:
        admin = discord.utils.get(ctx.guild.members, guild_permissions__administrator=True)
        if admin:
            await ctx.send(messages.get(lang, messages["en"])[2])

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    user_id = message.author.id
    lang = 'en'

    if content:
        blob = TextBlob(content)
        polarity = blob.sentiment.polarity
        if polarity < -0.5:
            await message.add_reaction("😠")
        elif polarity < 0:
            await message.add_reaction("😢")
        elif polarity < 0.3:
            await message.add_reaction("🙂")
        elif polarity < 0.7:
            await message.add_reaction("😄")
        else:
            await message.add_reaction("😂")

    for language, words in bad_words.items():
        if any(word in content for word in words):
            lang = language
            await send_warning(message.channel, user_id, lang)
            break

    if user_id in afk_users:
        await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK status.")
        del afk_users[user_id]

    for mentioned in message.mentions:
        if mentioned.id in afk_users:
            await message.channel.send(f"{mentioned.display_name} is AFK: {afk_users[mentioned.id]}")

    user_xp[user_id] = user_xp.get(user_id, 0) + 10
    xp = user_xp[user_id]
    level = xp // 100
    if user_level.get(user_id, 0) < level:
        user_level[user_id] = level
        await message.channel.send(f"{message.author.display_name} just leveled up to Level {level}!")

    await bot.process_commands(message)

@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = reason
    await ctx.send(f"{ctx.author.display_name} is now AFK: {reason}")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", description="Here's everything I can do:", color=0x00ff00)
    embed.add_field(name="XP/Leveling", value="!level", inline=False)
    embed.add_field(name="Skills", value="!setskill , !myskills", inline=False)
    embed.add_field(name="Comments", value="!comment , !mycomments", inline=False)
    embed.add_field(name="AFK System", value="!afk", inline=False)
    embed.add_field(name="Translator", value="Reply a message and use !t <lang_code>", inline=False)
    embed.add_field(name="Fun", value="!guess, !hi, !joke", inline=False)
    embed.add_field(name="Ping", value="!ping", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def level(ctx):
    xp = user_xp.get(ctx.author.id, 0)
    level = user_level.get(ctx.author.id, 0)
    await ctx.send(f"{ctx.author.display_name}, you are Level {level} with {xp} XP.")

@bot.command()
async def setskill(ctx, skill: str, level: int):
    user_skills.setdefault(ctx.author.id, {})[skill] = level
    await ctx.send(f"Set skill {skill} to level {level}.")

@bot.command()
async def myskills(ctx):
    skills = user_skills.get(ctx.author.id, {})
    if not skills:
        await ctx.send("You have no skills set.")
    else:
        msg = "\n".join([f"{k}: {v}" for k, v in skills.items()])
        await ctx.send(f"Your skills:\n{msg}")

@bot.command()
async def comment(ctx, *, msg: str):
    user_comments.setdefault(ctx.author.id, []).append(msg)
    await ctx.send("Your comment has been saved.")

@bot.command()
async def mycomments(ctx):
    comments = user_comments.get(ctx.author.id, [])
    if not comments:
        await ctx.send("You have no comments saved.")
    else:
        await ctx.send("Your comments:\n" + "\n".join(comments[-5:]))

@bot.command(aliases=["t"])
async def translate(ctx, lang=None):
    try:
        if not lang:
            await ctx.send("Usage: Reply to a message and use !t <lang_code>")
            return
        lang = lang.strip().lower()
        if lang not in supported_langs:
            langs = ", ".join([f"{k} ({v})" for k, v in supported_langs.items()])
            await ctx.send(f"Supported languages: {langs}")
            return
        if ctx.message.reference:
            replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            text_to_translate = replied_msg.content
        else:
            await ctx.send("Please reply to the message you want to translate.")
            return

        translated = translator.translate(text_to_translate, dest=lang)
        await ctx.send(f"Translated ({supported_langs[lang]}): {translated.text}")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
async def guess(ctx):
    number = random.randint(1, 5)
    await ctx.send("Guess a number between 1 and 5.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=10)
        if int(msg.content) == number:
            await ctx.send("Correct!")
        else:
            await ctx.send(f"Wrong! It was {number}.")
    except asyncio.TimeoutError:
        await ctx.send("Too late!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! Latency is {round(bot.latency * 1000)}ms.")

@bot.command()
async def who(ctx, lang=None):
    lang = lang or "en"
    if lang == "bn":
        await ctx.send("আমাকে তৈরী করেছে তারেক আজিজ। সে কক্সবাজার, বাংলাদেশে থাকে।")
    elif lang == "ar":
        await ctx.send("لقد صنعني طارق عزيز. إنه يعيش في كوكس بازار، بنغلاديش.")
    else:
        await ctx.send("I was created by Tareq Aziz. He lives in Cox's Bazar, Bangladesh.")

@bot.event
async def on_member_join(member):
    welcome = f"Welcome to the Rise of Kingdoms server, {member.mention}!"
    for ch in member.guild.text_channels:
        if "welcome" in ch.name or "general" in ch.name:
            await ch.send(welcome)
            break

def start_bot():
    bot.run(os.getenv("TOKEN"))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=start_bot).start()

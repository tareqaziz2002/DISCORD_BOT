import discord
from discord.ext import commands
import os
import random
from googletrans import Translator
import asyncio
from textblob import TextBlob
import nltk

# Download TextBlob corpora
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

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

# Bad words for only three languages (English, Bengali, Hindi)
bad_words = {
    "en": ["fuck", "shit", "bitch", "asshole", "bastard", "burn", "dog"],
    "bn": ["চুদ", "মাদারচোদ", "মাগী", "খারাপ", "হেই", "গালি", "হেলো"],
    "hi": ["गाली", "कुत्ता", "माँचोद", "बहनचोद", "शराबी"]
}

supported_langs = {
    "bn": "Bengali", "en": "English", "hi": "Hindi"
}

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

async def send_warning(ctx, user_id, lang):
    warnings[user_id] = warnings.get(user_id, 0) + 1
    count = warnings[user_id]
    
    if lang == "en":
        if count == 1:
            await ctx.send(f"{ctx.author.mention}, this is your first warning!")
        elif count == 2:
            await ctx.send(f"{ctx.author.mention}, second warning! Be cautious!")
        else:
            admin = discord.utils.get(ctx.guild.members, guild_permissions__administrator=True)
            if admin:
                await ctx.send(f"{admin.mention}, {ctx.author.mention} has been using inappropriate language repeatedly!")
    
    elif lang == "bn":
        if count == 1:
            await ctx.send(f"{ctx.author.mention}, এটা প্রথম ওয়ার্নিং!")
        elif count == 2:
            await ctx.send(f"{ctx.author.mention}, আবার ওয়ার্নিং দিচ্ছি! সাবধান হও।")
        else:
            admin = discord.utils.get(ctx.guild.members, guild_permissions__administrator=True)
            if admin:
                await ctx.send(f"{admin.mention}, {ctx.author.mention} বারবার খারাপ ভাষা ব্যবহার করছে!")
    
    elif lang == "hi":
        if count == 1:
            await ctx.send(f"{ctx.author.mention}, यह आपकी पहली चेतावनी है!")
        elif count == 2:
            await ctx.send(f"{ctx.author.mention}, दूसरी चेतावनी! ध्यान रखें!")
        else:
            admin = discord.utils.get(ctx.guild.members, guild_permissions__administrator=True)
            if admin:
                await ctx.send(f"{admin.mention}, {ctx.author.mention} बार-बार गलत भाषा का उपयोग कर रहे हैं!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    user_id = message.author.id
    lang = 'en'  # Default language

    # Sentiment analysis react
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

    # Checking if any bad word is in the message
    for language, words in bad_words.items():
        if any(word in content for word in words):
            lang = language  # Detect language based on bad words found
            await send_warning(message.channel, user_id, lang)
            await message.add_reaction("❌")  # Adding a reaction for bad language
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
    elif lang == "hi":
        await ctx.send("मुझे तारिक अजीज ने बनाया है। वह कक्स बाजार, बांगलादेश में रहता है।")
    else:
        await ctx.send("I was created by Tareq Aziz. He lives in Cox's Bazar, Bangladesh.")

@bot.event
async def on_member_join(member):
    welcome = f"Welcome to the Rise of Kingdoms server, {member.mention}!"
    for ch in member.guild.text_channels:
        if "welcome" in ch.name or "general" in ch.name:
            await ch.send(welcome)
            break

bot.run(os.getenv("TOKEN"))

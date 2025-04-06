import discord
from discord.ext import commands, tasks
import os
import random
import asyncio
from googletrans import Translator
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")  # Default help command removed
translator = Translator()

user_xp = {}
user_level = {}
user_skills = {}
user_comments = {}
afk_users = {}
warnings = {}

bad_words = ["fuck", "shit", "bitch", "asshole", "bastard", "চুদ", "মাদারচোদ", "মাগী", "burn", "dog"]

supported_langs = { 
    "bn": "Bengali", "en": "English", "ar": "Arabic", "hi": "Hindi", "es": "Spanish", "ja": "Japanese", 
    "fr": "French", "de": "German", "zh-cn": "Chinese", "ru": "Russian", "it": "Italian", "pt": "Portuguese", 
    "tr": "Turkish", "ko": "Korean", "ur": "Urdu", "fa": "Persian", "id": "Indonesian", "ms": "Malay", 
    "pl": "Polish", "sv": "Swedish", "uk": "Ukrainian", "vi": "Vietnamese", "ta": "Tamil", "te": "Telugu"
}

funny_lines = [
    "তুমি কি চা খেয়েছো আজ?", "তুমি হাসো অনেক সুন্দর করে!", "তোমার কথা না বললেই না!", 
    "তুমি কি জানো, আমি তোমাকে খুব পছন্দ করি!", "তুমি কি ম্যাজিক জানো?", "তোমার চোখে কি WiFi আছে?", 
    "তোমাকে দেখলেই মনে হয় হার্টবিট বেড়ে যায়!", "Are you Google? Because you’ve got everything I’m searching for.", 
    "Do you have a name or can I call you mine?", "You’re like sunshine on a rainy day."
]

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    auto_message_loop.start()

@tasks.loop(minutes=30)
async def auto_message_loop():
    text_channels = [c for g in bot.guilds for c in g.text_channels if c.permissions_for(g.me).send_messages]
    if text_channels:
        channel = random.choice(text_channels)
        line = random.choice(funny_lines)
        await channel.send(line)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    user_id = message.author.id
    content = message.content.lower()

    # Bad word warning system
    if any(word in content for word in bad_words):
        warnings[user_id] = warnings.get(user_id, 0) + 1
        count = warnings[user_id]
        if count == 1:
            await message.channel.send(f"{message.author.mention}, এটা প্রথম ওয়ার্নিং!")
        elif count == 2:
            await message.channel.send(f"{message.author.mention}, আবার ওয়ার্নিং দিচ্ছি! সাবধান হও।")
        else:
            admin = discord.utils.get(message.guild.members, guild_permissions__administrator=True)
            if admin:
                await message.channel.send(f"{admin.mention}, {message.author.mention} বারবার খারাপ ভাষা ব্যবহার করছে!")
    
    # AFK system
    if user_id in afk_users:
        await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK status.")
        del afk_users[user_id]
    
    for mentioned in message.mentions:
        if mentioned.id in afk_users:
            await message.channel.send(f"{mentioned.display_name} is AFK: {afk_users[mentioned.id]}")

    # XP system
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
    embed.add_field(name="AFK System", value="!afk ", inline=False)
    embed.add_field(name="Translator", value="!translate . <lang_code>", inline=False)
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

@bot.command(aliases=["tr", "t"])
async def translate(ctx, *, arg):
    try:
        if '.' not in arg:
            await ctx.send("Usage: !translate . <lang_code>")
            return
        
        text, dest = arg.rsplit('.', 1)
        dest = dest.strip().lower()
        
        if dest not in supported_langs:
            langs = ", ".join([f"{k} ({v})" for k, v in supported_langs.items()])
            await ctx.send(f"Supported languages: {langs}")
            return
        
        translated = translator.translate(text.strip(), dest=dest)
        await ctx.send(f"Translated: {translated.text}")
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
        await ctx.send("I was created by Tarek Aziz. He lives in Cox's Bazar, Bangladesh.")

@bot.event
async def on_member_join(member):
    welcome = f"Welcome to the Rise of Kingdoms server, {member.mention}!"
    for ch in member.guild.text_channels:
        if "welcome" in ch.name or "general" in ch.name:
            await ch.send(welcome)
            break

keep_alive()
bot.run(os.getenv("TOKEN"))

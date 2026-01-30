import os
import io
import json
import time
import discord
from discord import app_commands
from discord.ext import commands
import git
import google.generativeai as genai
import google.generativeai.types as gen
from PIL import Image
import pytesseract
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
REPO_PATH = os.getenv('REPO_PATH')

# Configure Gemini
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY is not set in environment variables.")

else:
    genai.configure(api_key=GEMINI_API_KEY)

# Load context data
try:
    with open('data/bot_context.json', 'r') as f:
        bot_context = json.load(f)
        system_instruction = bot_context.get("system_instruction", "")
        base_history = bot_context.get("history", [])
except FileNotFoundError:
    print("Warning: data/bot_context.json not found. Using empty context.")
    system_instruction = ""
    base_history = []
except json.JSONDecodeError:
    print("Error: Failed to decode data/bot_context.json.")
    system_instruction = ""
    base_history = []

# Gemini Model Configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

if GEMINI_API_KEY:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction,
        safety_settings={
            gen.HarmCategory.HARM_CATEGORY_HATE_SPEECH: gen.HarmBlockThreshold.BLOCK_NONE,
            gen.HarmCategory.HARM_CATEGORY_HARASSMENT: gen.HarmBlockThreshold.BLOCK_NONE,
            gen.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: gen.HarmBlockThreshold.BLOCK_NONE,
            gen.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: gen.HarmBlockThreshold.BLOCK_NONE,
        }
    )
else:
    model = None

# Discord Bot Setup
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

conversation_history = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="hello", description="Says hello to the user")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

@bot.tree.command(name="commit_push", description="Commits and pushes changed files to GitHub")
async def commit_push(interaction: discord.Interaction, commit_message: str):
    if not REPO_PATH:
        await interaction.response.send_message("Error: REPO_PATH environment variable is not set.", ephemeral=True)
        return

    try:
        await interaction.response.defer()
        repo = git.Repo(REPO_PATH)
        changed_files = [item.a_path for item in repo.index.diff(None)] + repo.untracked_files

        if not changed_files:
            await interaction.followup.send("No changes to commit.")
            return

        repo.git.add(A=True)
        repo.index.commit(commit_message)
        origin = repo.remote(name='origin')
        origin.push()

        await interaction.followup.send("Changes have been committed and pushed successfully!")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

async def process_prompt(prompt, user_id):
    if not model:
        return "Error: Gemini API key is not configured."

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    user_history = conversation_history[user_id]

    # Combine base history with user's previous history
    full_history = base_history + user_history

    try:
        chat_session = model.start_chat(history=full_history)
        response = chat_session.send_message(prompt)

        # Update user history with the new turn
        user_history.append({"role": "user", "parts": [prompt]})
        user_history.append({"role": "model", "parts": [response.text]})

        return response.text
    except Exception as e:
        return f"Error from Gemini API: {e}"

@bot.tree.command(name="bard", description="Chat with Bard AI (Google Generative AI)")
async def bard(interaction: discord.Interaction, prompt: str = None, attachment: discord.Attachment = None):
    try:
        await interaction.response.defer()

        if attachment:
            if attachment.filename.endswith('.txt'):
                file_content = await attachment.read()
                prompt = file_content.decode('utf-8')
            elif attachment.content_type.startswith('image/'):
                image_data = await attachment.read()
                image = Image.open(io.BytesIO(image_data))
                prompt = pytesseract.image_to_string(image)

        if not prompt:
            await interaction.followup.send("Please provide a prompt or attach a .txt or image file.")
            return

        response_text = await process_prompt(prompt, str(interaction.user.id))

        if len(response_text) > 2000:
            with open("response.txt", "w", encoding="utf-8") as f:
                f.write(response_text)
            await interaction.followup.send("The response is too long. Please see the attached file.", file=discord.File("response.txt"))
        else:
            await interaction.followup.send(response_text)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        prompt = ""
        if message.attachments:
            try:
                attachment = message.attachments[0]
                if attachment.filename.endswith('.txt'):
                    file_content = await attachment.read()
                    prompt = file_content.decode('utf-8')
                elif attachment.content_type.startswith('image/'):
                    image_data = await attachment.read()
                    image = Image.open(io.BytesIO(image_data))
                    prompt = pytesseract.image_to_string(image)
                else:
                    await message.channel.send("Unsupported attachment type. Please attach a .txt or image file.")
                    return
            except Exception as e:
                await message.channel.send(f"An error occurred while reading the file: {e}")
                return
        else:
            prompt = message.content

        if not prompt:
             return

        try:
            response_text = await process_prompt(prompt, str(message.author.id))

            if len(response_text) > 2000:
                with open("response.txt", "w", encoding="utf-8") as f:
                    f.write(response_text)
                await message.channel.send("The response is too long. Please see the attached file.", file=discord.File("response.txt"))
            else:
                await message.channel.send(response_text)
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

if not DISCORD_BOT_TOKEN:
    DISCORD_BOT_TOKEN = input("Please enter your Discord bot token: ")

if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("Error: No Discord bot token provided.")

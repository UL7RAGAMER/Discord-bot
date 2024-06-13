import os
import discord
from discord import app_commands
from discord.ext import commands
import git
import google.generativeai as genai
import time
import history
import google.generativeai.types as gen

# Set the path to the Git executable

# Replace 'YOUR_GEMINI_API_KEY' with your actual API key
genai.configure(api_key='AIzaSyDotzLRQW6ygO-j1vvblXTmrpizbLGFfLQ')

# Create the model configuration
def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def wait_for_files_active(files):
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction=history.system_instruction,
    safety_settings = {
    gen.HarmCategory.HARM_CATEGORY_HATE_SPEECH: gen.HarmBlockThreshold.BLOCK_NONE,
    gen.HarmCategory.HARM_CATEGORY_HARASSMENT: gen.HarmBlockThreshold.BLOCK_NONE,
    gen.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: gen.HarmBlockThreshold.BLOCK_NONE,
    gen.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: gen.HarmBlockThreshold.BLOCK_NONE,
}
)  

files = [
    upload_to_gemini("C:/Users/siddk/Downloads/lemh105.pdf", mime_type="application/pdf"),
]

intents = discord.Intents.default()
intents.messages = True  # Enable message intent to handle DMs
bot = commands.Bot(command_prefix="!", intents=intents)

conversation_history = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="hello", description="Says hello to the user")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

@bot.tree.command(name="commit_push", description="Commits and pushes changed files to GitHub")
async def commit_push(interaction: discord.Interaction, commit_message: str):
    try:
        await interaction.response.defer()
        repo_path = "/path/to/yourrepo"  # Adjust based on your environment
        repo = git.Repo(repo_path)
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

@bot.tree.command(name="bard", description="Chat with Bard AI (Google Generative AI)")
async def bard(interaction: discord.Interaction, prompt: str = None, attachment: discord.Attachment = None):
    try:
        await interaction.response.defer()

        if attachment and attachment.filename.endswith('.txt'):
            prompt = await attachment.read()
            prompt = prompt.decode('utf-8')

        if not prompt:
            await interaction.followup.send("Please provide a prompt or attach a .txt file.")
            return

        user_id = str(interaction.user.id)
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        user_history = conversation_history[user_id]
        user_history.append({"role": "user", "parts": [prompt]})
        print(user_history + history.history)
        chat_session = model.start_chat(history=user_history + history.history)
        response = chat_session.send_message(prompt)
        user_history.append({"role": "model", "parts": [response.text]})

        if len(response.text) > 2000:
            # If the response is too long, save it to a file and send the file
            with open("response.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            await interaction.followup.send("The response is too long. Please see the attached file.", file=discord.File("response.txt"))
        else:
            await interaction.followup.send(response.text)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.attachments and message.attachments[0].filename.endswith('.txt'):
            try:
                file = message.attachments[0]
                prompt = await file.read()
                prompt = prompt.decode('utf-8')
            except Exception as e:
                await message.channel.send(f"An error occurred while reading the file: {e}")
                return
        else:
            prompt = message.content

        try:
            user_id = str(message.author.id)
            if user_id not in conversation_history:
                conversation_history[user_id] = []

            user_history = conversation_history[user_id]
            user_history.append({"role": "user", "parts": [prompt]})
            chat_session = model.start_chat(history=user_history + history.history)
            response = chat_session.send_message(prompt)
            user_history.append({"role": "model", "parts": [response.text]})

            if len(response.text) > 2000:
                with open("response.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                await message.channel.send("The response is too long. Please see the attached file.", file=discord.File("response.txt"))
            else:
                await message.channel.send(response.text)
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

token = os.getenv('DISCORD_BOT_TOKEN')
if not token:
    token = input("Please enter your Discord bot token: ")
bot.run(token)

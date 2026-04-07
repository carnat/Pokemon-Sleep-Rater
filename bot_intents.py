import discord
import os
from dotenv import load_dotenv
from pokemon import RatePokemon
from ocr import detect_text_uri

load_dotenv()


class PokemonSleepRatingBot(discord.Client):
    async def on_message(self, message):
        # Prevents bot from replying to itself.
        if message.author.id == self.user.id:
            return

        if message.content.startswith('!rateps'):
            if message.attachments and any(
                    att.filename.endswith(('.png', '.jpg', '.jpeg')) for att in message.attachments):
                result = RatePokemon().rate_pokemon(detect_text_uri(message.attachments[0].url))
                if not result:
                    await message.reply(
                        "Pokémon not found. Please check image upload (name, nature, and subskills) or try again.")
                else:
                    await message.reply(
                        f"{result['name']} is rated {result['final_grade']} — "
                        f"Score: {result['grade']} ({result['specialty']})")


intents = discord.Intents.default()
intents.message_content = True

token = os.getenv('BOT_TOKEN')
if not token:
    raise RuntimeError("BOT_TOKEN environment variable is not set.")

client = PokemonSleepRatingBot(intents=intents)
client.run(token)

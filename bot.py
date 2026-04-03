import discord
import logging
import os
from pokemon_db import db
from dotenv import load_dotenv
from pokemon import RatePokemon
from ocr import detect_text_uri

load_dotenv()
bot = discord.Bot()
logger = logging.getLogger(__name__)


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(name="rateps", description="Upload an image of your Pokémon to be rated.")
async def rateps(
    ctx,
    image: discord.Option(discord.Attachment, required=True),
    level: discord.Option(int, description="Your Pokémon's current level (enables level-aware scoring)",
                          required=False, default=None),
):
    if image:
        try:
            print(image)
            result = RatePokemon().rate_pokemon(detect_text_uri(image.url), pokemon_level=level)
            if not result:
                await ctx.respond(
                    "Pokémon not found. Please check image upload (name, nature, and subskills) or try again.")
                return

            name = result['name']
            final_grade = result['final_grade']
            skills_value = result['skills_value']
            locked_skills = result['locked_skills']
            nature = result['nature']
            nature_rating = result['nature_rating']
            grade = result['grade']
            percentile = result['percentile']
            all_scores = result['all_scores']
            helps_per_day = result['helps_per_day']
            specialty = result['specialty']

            level_note = f" (Lv. {level})" if level else ""
            embed = discord.Embed(
                title="Pokémon Evaluation",
                description=f"[*Your {name}{level_note} is rated {final_grade}*]({image.url})",
                color=discord.Colour.green(),
            )

            embed.add_field(
                name="Subskills",
                value=db.subskills_to_string(skills_value, locked_skills),
                inline=False,
            )
            embed.add_field(name="Nature", value=f"{nature}: {nature_rating}", inline=False)

            top_pct = 100 - percentile
            embed.add_field(
                name=f"Total Score ({specialty})",
                value=f"{grade}  •  Top {top_pct}% for {specialty}",
                inline=False,
            )

            # Show scores for all three specialties for comparison
            spec_lines = []
            for spec, data in all_scores.items():
                marker = "★" if spec == specialty else "  "
                spec_lines.append(f"{marker} {spec}: **{data['grade']}** (top {100 - data['percentile']}%)")
            embed.add_field(name="All Specialty Scores", value="\n".join(spec_lines), inline=False)

            if helps_per_day:
                embed.add_field(
                    name="Est. Production",
                    value=f"~{helps_per_day} helps/day",
                    inline=True,
                )

            embed.set_author(name="Pokémon Sleep Rater", icon_url="https://i.imgur.com/xQ8V3OI.png")
            embed.set_thumbnail(url="https://i.imgur.com/Ox0DTqY.png")
            await ctx.respond(embed=embed)
        except Exception as e:
            logger.error("Error processing /rateps: %s", e, exc_info=True)
            await ctx.respond(
                "Pokémon not found. Please check image upload (name, nature, and subskills) or try again.")


bot.run(os.getenv('BOT_TOKEN'))

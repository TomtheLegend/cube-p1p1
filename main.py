import os
import random
import json
from dotenv import load_dotenv
import datetime, zoneinfo
import aiohttp, io
# Discord imports
import discord
from discord.ext import commands, tasks


load_dotenv()

# Retrieve the discord token
token = os.getenv("DISCORD_TOKEN")
channel_id = os.getenv("DISCORD_CHANNEL")

# main file

# Set your target time (UTC)
nz_tz = zoneinfo.ZoneInfo("Pacific/Auckland")
scheduled_time = [
    datetime.time(hour=11, minute=00, tzinfo=nz_tz), # 11:00 AM NZT
    # datetime.time(hour=17, minute=0, tzinfo=nz_tz)  
]

@commands.command()
async def cubelist(ctx):
    embed = discord.Embed(
            title="Cubes List", 
            description="Current Cube list to request p1p1 from.\nUse the alias after p1p1 command to request", 
            color=discord.Color.green()
        )

    all_cubes = get_cube_lsit()

    cube_names = ""
    cube_aliases = ""
    cube_owners = ""

    for cube in all_cubes:
        cube_names += cube["cube_name"] + "\n"
        cube_aliases += cube["cube_alias"] + "\n"
        # hack to mkae it fit in an embed (limited width)
        padding = (22 - len(cube["cube_owner_name"])) * " \u200b"
        cube_owners += cube["cube_owner_name"] + padding + "[Link](" + cube["cube_url"] + ")\n"

    embed.add_field(name="Cube Name", value=cube_names, inline=True)
    embed.add_field(name="Cube Alias", value=cube_aliases, inline=True)
    embed.add_field(name="Cube Owner    Cube Link", value=cube_owners, inline=True)

    await ctx.send(embed=embed)
          
@commands.command()
async def p1p1(ctx, cube_alias: str = ""):
    # get cube data , imageurl, link to cube etc.
    cube_info = get_cube_data(cube_alias)

    cube_message_text= f"Generating a P1P1 from {cube_info["cube_owner_name"]}'s [{cube_info["cube_name"]}]({cube_info["cube_url"]})"

    # send image
    if ctx:
        async with aiohttp.ClientSession() as session:
            async with session.get(cube_info["cube_image_url"]) as response:
                if response.status != 200:
                    return await ctx.send("Failed to download image.")
                    
                # Read bytes into a memory buffer
                data = io.BytesIO(await response.read())
                p1p1file = discord.File(data, filename='p1p1file.jpg')
                
                msg = await ctx.send(cube_message_text)
                await msg.edit(suppress=True)
                await ctx.send(file=p1p1file)

@commands.command()
async def cubehelp(ctx):
    help_message = "I am the Pack1Pick one Bot.\n" \
                    "Use the below Commands in chat channels:\n" \
                    "- *** !cubelist *** - Will show the list of cubes to select from (cube_alias shown here)\n" \
                    "- *** !p1p1 [cube_alias] *** - Will display a random pack1pick1 from either a randomly selected cube or the cube alias provided\n\n" \
                    "I will also show a daily random Pack1Pick1 in the cube-p1p1 channel at 11am"
    await ctx.send(help_message)

class P1P1Bot(commands.Bot):
    def __init__(self):
        # Text commands require the message_content intent enabled
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents,help_command=None)

    async def setup_hook(self):
        # Start the background task loop when the bot starts up
        self.send_scheduled_message.start()
        self.add_command(p1p1)
        self.add_command(cubelist)
        self.add_command(cubehelp)

    async def on_ready(self):
        print(f"Logged in as {self.user.name}")

    @tasks.loop(time=scheduled_time)
    async def send_scheduled_message(self):
        channel = self.get_channel(channel_id)

        # get cube data , imageurl, link to cube etc.
        cube_info = get_cube_data()
        # set cube message info    
        cube_message_text= f"Todays P1P1 is from {cube_info["cube_owner_name"]}'s [{cube_info["cube_name"]}]({cube_info["cube_url"]})"

        # send image
        if channel:
            async with aiohttp.ClientSession() as session:
                async with session.get(cube_info["cube_image_url"]) as response:
                    if response.status != 200:
                        return await channel.send("Failed to download image.")
                        
                    # Read bytes into a memory buffer
                    data = io.BytesIO(await response.read())
                    p1p1file = discord.File(data, filename='p1p1file.jpg')
                    
                    msg = await channel.send(cube_message_text)
                    await msg.edit(suppress=True)
                    await channel.send(file=p1p1file)
  

# function to get cube data to p1p1 image
def get_cube_data(cube_alias=None):
    cube_data = {}
    # get all cube data
    with open('cube_info.json', 'r', encoding='utf-8') as file:
        all_cube_data = json.load(file)
    # randomly select a cube from the list
    cube_alias_lower = cube_alias.lower()
    if cube_alias == '' or cube_alias_lower == 'random': 
        cube_data = random.choice(all_cube_data)
    else:
        cube_data = next((d for d in all_cube_data if d.get("cube_alias") == cube_alias_lower), None)
    
    # generate random sample pack with seed
    random_seed = random.randint(1111111111111,9999999999999)
    cube_data["cube_image_url"] = f"https://cubecobra.com/cube/samplepackimage/{cube_data["sample_pack_code"]}/{random_seed}"

    return cube_data

def get_cube_lsit():
     # get all cube data
    with open('cube_info.json', 'r', encoding='utf-8') as file:
        all_cube_data = json.load(file)
    
    return all_cube_data


# Run the bot
if __name__ == '__main__':
    bot = P1P1Bot()
    bot.run(token)

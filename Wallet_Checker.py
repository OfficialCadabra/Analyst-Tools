import discord
from discord.ext import commands
import requests
import random
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BIRDEYE_API_KEY = os.getenv('BIRDEYE_API_KEY', 'BIRDEYEAPIKEYHERE!!')
BROKE_GIFS = [
    'https://media.tenor.com/aj47iJzWZgwAAAPo/broke-no.mp4',
    'https://media.tenor.com/h1-tMFNDA1gAAAPo/broke-poor.mp4',
    'https://media.tenor.com/y6HVvese3nMAAAPo/wallet-penacony.mp4'
]

# Initialize bot with command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def format_usd(value):
    """Format USD value with appropriate decimal places"""
    if value >= 1:
        return f"${value:,.2f}"
    else:
        return f"${value:,.6f}"

def format_number(value):
    """Format numbers with appropriate decimal places"""
    if value >= 1:
        return f"{value:,.2f}"
    else:
        return f"{value:,.6f}"

async def fetch_wallet_portfolio(wallet_address):
    """Fetch wallet portfolio from Birdeye API"""
    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={wallet_address}"
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": BIRDEYE_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready to use in {len(bot.guilds)} servers')

@bot.command(name='wallet')
async def wallet(ctx, address: str):
    """Command to check wallet portfolio"""
    # Fetch wallet data
    wallet_data = await fetch_wallet_portfolio(address)
    
    if "error" in wallet_data:
        await ctx.send(f"Error fetching wallet data: {wallet_data['error']}")
        return
        
    if not wallet_data["success"]:
        await ctx.send("Failed to fetch wallet data")
        return
        
    data = wallet_data["data"]
    
    # Handle empty wallet
    if data["totalUsd"] == 0 or not data["items"]:
        gif_url = random.choice(BROKE_GIFS)
        await ctx.send(f"Wallet is empty! {gif_url}")
        return
    
    # Sort items by USD value (highest to lowest)
    sorted_items = sorted(data["items"], key=lambda x: x.get("valueUsd", 0), reverse=True)
    
    # Create main embed for wallet overview
    main_embed = discord.Embed(
        title="💼 Wallet Portfolio Summary",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    # Add wallet info to main embed
    main_embed.add_field(
        name="👛 Wallet Address",
        value=f"`{data['wallet']}`",
        inline=False
    )
    main_embed.add_field(
        name="💰 Total Portfolio Value",
        value=f"**{format_usd(data['totalUsd'])}**",
        inline=False
    )
    
    # Add separator
    main_embed.add_field(
        name="〰️ Assets 〰️",
        value="",
        inline=False
    )
    
    # Add portfolio items
    for item in sorted_items:
        token_name = item.get("name", "Unknown Token")
        symbol = item.get("symbol", "???")
        value_usd = item.get("valueUsd", 0)
        token_address = item.get("address", "N/A")
        balance = item.get("uiAmount", 0)
        
        # Format the token information
        value_text = format_usd(value_usd)
        balance_text = format_number(balance)
        
        field_value = (
            f"💵 Value: **{value_text}**\n"
            f"🔢 Balance: **{balance_text}** {symbol}\n"
            f"📝 CA: `{token_address}`"
        )
        
        main_embed.add_field(
            name=f"🪙 {token_name} ({symbol})",
            value=field_value,
            inline=False
        )
    
    # Add footer
    main_embed.set_footer(text="Data provided by Birdeye.so")
    
    await ctx.send(embed=main_embed)

# Run the bot with error handling
def run_bot():
    if not TOKEN:
        raise ValueError("No Discord token found. Please set DISCORD_BOT_TOKEN in your .env file")
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Failed to login to Discord. Please check if your token is correct.")
        print("Make sure your .env file contains the correct DISCORD_BOT_TOKEN")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    run_bot()

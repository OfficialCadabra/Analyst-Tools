import discord
from discord.ui import Button, View
import requests
import json
from discord import ButtonStyle
from discord.ext import commands
from datetime import datetime

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

BIRDEYE_API_KEY = "BIRDEYE API KEY HERE"
BIRDEYE_BASE_URL = "https://public-api.birdeye.so"

def format_number(number, decimals=2):
    """Format numbers with appropriate decimals and commas"""
    if number is None:
        return "N/A"
    if number == 0:
        return "0"
    if abs(number) < 0.00001:
        return f"{number:.8f}"
    if abs(number) < 1:
        return f"{number:.6f}"
    return f"{number:,.{decimals}f}"

def format_percent(number):
    """Format percentage with appropriate color emoji"""
    if number is None:
        return "N/A"
    emoji = "🟢" if number > 0 else "🔴" if number < 0 else "⚪"
    return f"{emoji} {format_number(number)}%"

class MainView(View):
    def __init__(self, token_data):
        super().__init__(timeout=None)
        self.token_data = token_data

    @discord.ui.button(label="📱 Social Links", style=ButtonStyle.primary)
    async def social_links(self, interaction: discord.Interaction, button: Button):
        social_links = {
            "website": self.token_data.get("extensions", {}).get("website", ""),
            "twitter": self.token_data.get("extensions", {}).get("twitter", ""),
            "telegram": self.token_data.get("extensions", {}).get("telegram", ""),
            "discord": self.token_data.get("extensions", {}).get("discord", "")
        }

        embed = discord.Embed(
            title="🔗 Social Links",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        for platform, url in social_links.items():
            if url:
                embed.add_field(name=platform.capitalize(), value=f"[Visit]({url})", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📊 Charts", style=ButtonStyle.primary)
    async def charts(self, interaction: discord.Interaction, button: Button):
        token_address = self.token_data.get("address", "")
        embed = discord.Embed(
            title="📈 Available Charts",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="DEX Chart", value=f"[View](https://dexscreener.com/solana/{token_address})", inline=False)
        embed.add_field(name="Birdeye Chart", value=f"[View](https://birdeye.so/token/{token_address})", inline=False)
        embed.add_field(name="CoinGecko", value=f"[View](https://www.coingecko.com/en/coins/{token_address})", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def get_token_data(address):
    url = f"{BIRDEYE_BASE_URL}/defi/token_overview"
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": BIRDEYE_API_KEY
    }
    params = {"address": address}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"API Response: {data}")  # Debugging: Log the full response
        if 'data' in data:
            return data['data']
        else:
            print(f"Unexpected API response format: {data}")
            return None
    except Exception as e:
        print(f"Error fetching token data: {e}")
        return None

@bot.command(name='token')
async def token_info(ctx, address: str):
    loading_message = await ctx.send("🔍 Fetching token data...")

    token_data = await get_token_data(address)

    if not token_data:
        await loading_message.edit(content="❌ Error fetching token data. Please verify the token address and try again.")
        return

    # Create main embed
    embed = discord.Embed(
        title=f"{token_data.get('symbol', 'Unknown')} Token Information",
        description=f"```{token_data.get('name', 'Unknown')}```",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )

    # Add token image if available
    embed.set_thumbnail(url=token_data.get('logoURI', 'https://via.placeholder.com/150'))

    # Price Information
    embed.add_field(
        name="💰 Price Information",
        value=f"```Current Price: ${format_number(token_data.get('price', 0), 8)}\n"
              f"Price Changes:\n"
              f"30m: {format_percent(token_data.get('priceChange30mPercent'))}\n"
              f"1h:  {format_percent(token_data.get('priceChange1hPercent'))}\n"
              f"4h:  {format_percent(token_data.get('priceChange4hPercent'))}\n"
              f"24h: {format_percent(token_data.get('priceChange24hPercent'))}```",
        inline=False
    )

    # Market Metrics
    embed.add_field(
        name="📊 Market Metrics",
        value=f"```Market Cap: ${format_number(token_data.get('realMc', 0))}\n"
              f"Liquidity: ${format_number(token_data.get('liquidity', 0))}\n"
              f"Holders: {format_number(token_data.get('holder', 0))}```",
        inline=False
    )

    # Volume Information
    embed.add_field(
        name="📈 24h Volume",
        value=f"```Total Volume: ${format_number(token_data.get('v24hUSD', 0))}\n"
              f"Buy Volume:  ${format_number(token_data.get('vBuy24hUSD', 0))}\n"
              f"Sell Volume: ${format_number(token_data.get('vSell24hUSD', 0))}\n"
              f"Volume Change: {format_percent(token_data.get('v24hChangePercent'))}```",
        inline=False
    )

    # Trading Activity
    embed.add_field(
        name="🔄 24h Trading Activity",
        value=f"```Total Trades: {format_number(token_data.get('trade24h', 0))}\n"
              f"Buy Trades:  {format_number(token_data.get('buy24h', 0))}\n"
              f"Sell Trades: {format_number(token_data.get('sell24h', 0))}\n"
              f"Trade Change: {format_percent(token_data.get('trade24hChangePercent'))}```",
        inline=False
    )

    # Unique Wallets
    embed.add_field(
        name="👥 Unique Wallets",
        value=f"```30m: {format_number(token_data.get('uniqueWallet30m', 0))} ({format_percent(token_data.get('uniqueWallet30mChangePercent'))})\n"
              f"1h:  {format_number(token_data.get('uniqueWallet1h', 0))} ({format_percent(token_data.get('uniqueWallet1hChangePercent'))})\n"
              f"4h:  {format_number(token_data.get('uniqueWallet4h', 0))} ({format_percent(token_data.get('uniqueWallet4hChangePercent'))})\n"
              f"24h: {format_number(token_data.get('uniqueWallet24h', 0))} ({format_percent(token_data.get('uniqueWallet24hChangePercent'))})```",
        inline=False
    )

    # Supply Information
    embed.add_field(
        name="📦 Supply Information",
        value=f"```Circulating Supply: {format_number(token_data.get('circulatingSupply', 0))}\n"
              f"Total Supply: {format_number(token_data.get('supply', 0))}```",
        inline=False
    )

    # Add footer with token address and last trade time
    last_trade_time = datetime.fromtimestamp(token_data.get('lastTradeUnixTime', 0)).strftime('%Y-%m-%d %H:%M:%S UTC')
    embed.set_footer(text=f"Token Address: {token_data.get('address', 'N/A')} | Last Trade: {last_trade_time}")

    # Create view with buttons
    view = MainView(token_data)

    await loading_message.edit(content=None, embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name}')

# Run the bot
bot.run('DISCORD BOT KEY HERE')

import discord
from discord.ext import commands
import requests
from datetime import datetime
from typing import List, Dict

# Bot configuration
TOKEN = 'DISCORD BOT TOKEN HERE'
BIRDEYE_API_KEY = 'BIRDEYE API KEY HERE'
COMMAND_PREFIX = '!'

class SniperBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)

    async def setup_hook(self):
        await self.add_cog(SniperDetector(self))

class SniperDetector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": BIRDEYE_API_KEY
        }

    def fetch_early_trades(self, contract_address: str) -> List[Dict]:
        """Fetch trades from the first block after token creation."""
        url = f"https://public-api.birdeye.so/defi/txs/token/seek_by_time"
        params = {
            "address": contract_address,
            "offset": 0,
            "limit": 50,
            "tx_type": "swap",
            "before_time": 0,
            "after_time": 1  # Target block length of 1s
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('data', {}).get('items', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching trades: {e}")
            return []

    def analyze_trades(self, trades: List[Dict]) -> List[Dict]:
        """Analyze trades to identify snipers."""
        snipers = []
        
        for trade in trades:
            if trade['side'] == 'buy':
                sniper_info = {
                    'wallet': trade['owner'],
                    'amount_sol': trade['from']['uiAmount'],
                    'timestamp': datetime.fromtimestamp(trade['blockUnixTime']).strftime('%Y-%m-%d %H:%M:%S'),
                    'tx_hash': trade['txHash']
                }
                snipers.append(sniper_info)
        
        return snipers

    def create_embed(self, contract_address: str, snipers: List[Dict], page: int = 1, page_size: int = 25) -> discord.Embed:
        """Create a Discord embed with sniper information, supporting pagination."""
        embed = discord.Embed(
            title="🎯 Sniper Detection Results",
            description=f"Contract Address: `{contract_address}`",
            color=discord.Color.blue()
        )
        
        total_snipers = len(snipers)
        total_pages = (total_snipers + page_size - 1) // page_size  # Calculate total pages

        # Get the snipers for the current page
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        snipers_on_page = snipers[start_idx:end_idx]

        # Add sniper information to the embed
        for i, sniper in enumerate(snipers_on_page, start=start_idx + 1):
            embed.add_field(
                name=f"Sniper #{i}",
                value=(
                    f"🔷 Wallet: `{sniper['wallet']}`\n"
                    f"💰 Amount: {sniper['amount_sol']} SOL\n"
                    f"🕒 Time: {sniper['timestamp']}\n"
                    f"📝 TX: `{sniper['tx_hash']}`"
                ),
                inline=False
            )

        # Add pagination info
        embed.set_footer(text=f"Page {page}/{total_pages} | Total Snipers Found: {total_snipers}")

        return embed

    @commands.command(name='check')
    async def check_snipers(self, ctx, contract_address: str, page: int = 1):
        """Command to check for snipers on a given token contract, with pagination."""
        loading_message = await ctx.send("🔍 Analyzing token trades...")
        try:
            trades = self.fetch_early_trades(contract_address)
            snipers = self.analyze_trades(trades)

            if not snipers:
                await loading_message.edit(content="No snipers detected!")
                return

            # Generate and send the embed for the requested page
            embed = self.create_embed(contract_address, snipers, page=page)
            await loading_message.edit(content=None, embed=embed)

        except Exception as e:
            await loading_message.edit(content=f"❌ Error: {str(e)}")

def run_bot():
    bot = SniperBot()
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()


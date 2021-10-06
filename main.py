import discord
import os
import json
import datetime

from pycoingecko import CoinGeckoAPI
from discord.ext import commands, tasks

cg = CoinGeckoAPI()
bot = commands.Bot(command_prefix='$')
channel = bot.get_channel('')
default_currency = 'usd'
alert_container = {}
TOKEN = "" # ADD AUTH TOKEN 

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

    alert_task.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send(cg.ping()['gecko_says'])

@bot.command()
async def alerts(ctx):
    message = ''

    for key in alert_container:
        amount = float(alert_container[key][0])
        threshold = float(alert_container[key][1])
        message += "**" + key + ":** " + str(amount) + " -- threshold: " + str(threshold) + "%\n"

    await ctx.send(message)

@bot.command()
async def clear(ctx, target):
    if target.lower() == 'alerts':
        alert_container.clear()
        await ctx.send('Alerts cleared!')
    else:
        await ctx.send("can't clear " + target)
    

@bot.command()
async def price(ctx, *args):
    lower = map(lambda x:x.lower(), args)

    assets = ','.join(lower)
    asset_data = get_asset_price(assets)
    
    for asset in asset_data:
        if "-" in str(asset_data[asset]['usd_24h_change']):
            await ctx.send("**" + asset + ":** $" + str(asset_data[asset]['usd']) + "\n24h change: " + str(round(asset_data[asset]['usd_24h_change'], 2)) + "%  :arrow_down:\n")
        else:
            await ctx.send("**" + asset + ":** $" + str(asset_data[asset]['usd']) + "\n24h change: " + str(round(asset_data[asset]['usd_24h_change'], 2)) + "%  :arrow_up:")

@bot.command()
async def alert(ctx, asset, amount, threshold):
    alert_container[asset] = [amount, threshold, ctx.author.mention]
    await ctx.send('Alert set by _{}_ for {}, occuring when value hits {} :white_check_mark:'.format(ctx.author.mention, asset, amount))

@tasks.loop(seconds = 30)
async def alert_task():
    if(len(alert_container) > 0):
        for key in alert_container:
            amount = float(alert_container[key][0])
            threshold = float(alert_container[key][1])
            author = alert_container[key][2]

            asset_price = float(get_asset_price(key)[key][default_currency])
            alert_range_amount = threshold / 100

            low_range_asset_price =  asset_price - (asset_price * alert_range_amount)
            high_range_asset_price = asset_price + (asset_price * alert_range_amount)

            if amount >= low_range_asset_price and amount <= high_range_asset_price:
                await bot.get_channel(680192332645269524).send(':red_circle: :green_circle:  {} :green_circle: :red_circle: - is within {}% of your target price of {}! Are we buying, {}?'.format(key, threshold, amount, author))

@alert_task.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")

def get_asset_price(id, currency = 'usd'):
    return cg.get_price(id, currency, include_market_cap='false', include_24hr_vol='false', include_24hr_change='true')

def get_asset(id):
    return cg.get_coin_market_chart_by_id()

bot.run(TOKEN)
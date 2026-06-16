import discord, asyncio
from discord import ui, app_commands
import random
import string
from discord import member
from discord.ext.commands import Context
import requests
from bs4 import BeautifulSoup
import re
import os 
import sqlite3
from datetime import date
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



class Bids:
  def __init__(self):
    self.itemName = str
    self.BidderID = []
    self.itemBids = []
    self.itemBidders = []
    self.theView = discord.ui.View
    self.message = int
    self.button = str

global guildID
#guildID = int(os.getenv("GUILD_ID"))
#channelID = int(os.getenv("CHANNEL_ID"))

#print(f"{os.getenv("DISCORD_TOKEN")}")

class aclient(discord.Client):
  def __init__(self):
    super().__init__(intents=discord.Intents.default())
    self.synced = False
    self.intents.message_content = True


  async def on_ready(self):
    await self.wait_until_ready()

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync tree: {e}")

    if not self.synced:
      #await tree.sync(guild = discord.Object(id=guildID))
      self.synced = True
      global auctions 
      global memberList
      #global bidCommand
      auctions = {}
      
    print(f"I have logged in as {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)
CLEANR = re.compile('<.*?>')

#MCP Client Setup
MCP_SERVER_DIR = r"C:\Users\stare\source\repos\Sloan-James\Bid-Bot\MCP"
INDEX_JS_PATH = os.path.join(MCP_SERVER_DIR, "dist", "index.js")

current_env = os.environ.copy()

current_env["EQ_GAME_PATH"] = r"C:\\Users\\Public\\Daybreak Game Company\\Installed Games\\EverQuest"

server_params = StdioServerParameters(
    command="node",
    args=[INDEX_JS_PATH],
    env=current_env
)

async def item_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    # Implementation for item autocomplete
    if len(current) < 3:
        return []
    
    try: 
        async with stdio_client(server_params) as (read_stream, write_stream):

            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                response = await session.call_tool(
                    "search_items",
                    arguments={"query": current}
                )


                #print(f"checking content: {response.content}")

                if not response.content or not response.content[0].text:
                    print("No content received from MCP tool.")
                    return []

                

                raw_text = ""
                for block in response.content:
                    if hasattr(block, 'text') and block.text:
                        raw_text = block.text
                        break

                if not raw_text:
                    return []

               

                choices = []
                for line in raw_text.split("\n"):
                    if "**" in line:
                        start = line.find("**") + 2
                        end = line.find("**", start)
                        if start > 1 and end > start:
                            item_name = line[start:end].strip()

                            item_id = None
                            if "?item=" in line:
                                id_start = line.find("?item=") + 6
                                id_end = line.find(")", id_start)
                                if id_end == -1: id_end = len(line)
                                item_id = line[id_start:id_end].strip()

                            passed_value = f"{item_id}|{item_name}"

                            #if item_name and not any(c.name == item_name for c in choices):
                            if item_name:
                                item_name = item_name + " | " + item_id
                                choices.append(app_commands.Choice(name=item_name, value=passed_value))
                    

                    if len(choices) >= 25:
                        break

                return choices


    except Exception as e:
        print(f"Autocomplete backend error: {e}")
        return[]

    pass

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext


#Modal window for Bids
class Bid_Modal(ui.Modal, title = "Default"):

  #bidAmount = ui.TextInput(label = "How much would you like to bid?", style = discord.TextStyle.short, placeholder = "100000", required = True)

  def __init__(self, bidId, item, oldbid):
    super().__init__(timeout = None)
    #global auctions
    if oldbid == None:
      self.bidAmount = discord.ui.TextInput(label = "How much?", style = discord.TextStyle.short, placeholder = "100000", required = True)
    else:
      self.bidAmount = discord.ui.TextInput(label = "How much? Previous bid: {:,}".format(oldbid), style = discord.TextStyle.short, placeholder = "100000", required = True)
    self.add_item(self.bidAmount)
    self.title = item[:45]
    self.bid_id = bidId
    self.auctions = auctions
  
    






  
  async def on_submit(self, interaction: discord.Interaction):
    #Test for conversion to integer
    try:
        price = int(self.bidAmount.value)
    except ValueError:
        await interaction.response.send_message('Enter a valid integer.', ephemeral = True)
        return

    if price < 0:
        await interaction.response.send_message('Enter a positive integer', ephemeral = True)
    elif price == 0:
        await interaction.response.send_message('Bid for ' + self.auctions.get(self.bid_id).itemName + ' canceled.'.format(price), ephemeral = True)
        try:
            index = self.auctions.get(self.bid_id).BidderID.index(interaction.user.id)
        except:
            return
        if index != None:
            self.auctions.get(self.bid_id).itemBids.pop(index)
            self.auctions.get(self.bid_id).BidderID.pop(index)
            self.auctions.get(self.bid_id).itemBidders.pop(index)
    elif interaction.user.id in self.auctions.get(self.bid_id).BidderID:
      index = self.auctions.get(self.bid_id).BidderID.index(interaction.user.id)
      if interaction.user.display_name == self.auctions.get(self.bid_id).itemBidders[index]:   
        self.auctions.get(self.bid_id).itemBids[index] = price
        await interaction.response.send_message('Bid for ' + self.auctions.get(self.bid_id).itemName + ' updated to {:,} Plat.'.format(price), ephemeral = True)
        try:
          await interaction.user.send('Bid for ' + self.auctions.get(self.bid_id).itemName + ' updated to {:,} Plat.'.format(price))
        except discord.Forbidden:
          pass
      else:
        await interaction.response.send_message('Please do not change your display name after placing a bid. If you believe you received this message in error, please message an officer')
    else:
      self.auctions.get(self.bid_id).BidderID.append(interaction.user.id)
      self.auctions.get(self.bid_id).itemBids.append(price)
      self.auctions.get(self.bid_id).itemBidders.append(interaction.user.display_name)

      await interaction.response.send_message('Bid for ' + self.auctions.get(self.bid_id).itemName + ' accepted for {:,} Plat.'.format(price), ephemeral = True)
      try:
        await interaction.user.send('Bid for ' + self.auctions.get(self.bid_id).itemName + ' accepted for {:,} Plat.'.format(price))
      except discord.Forbidden:
        pass
  
  async def on_error(self, interaction: discord.Interaction, error):
    if self.bid_id not in self.auctions:
      await interaction.response.send_message("That auction is no longer active.", ephemeral = True)
    else:
      await interaction.response.send_message("Enter a valid number", ephemeral = True)

class inactiveAuction(ui.Modal, title="Auction is Inactive"):
  def __init__(self):
    super().__init__(timeout = 5)


#Button class for bid
class placeABid(discord.ui.View):
  def __init__(self, bidId, item):
    super().__init__(timeout = None)
    
    self.bid_id = bidId
    self.item = item

  @discord.ui.button(label="Place Bid", style=discord.ButtonStyle.green, custom_id = "bidButton")
  async def placeBid(self, interaction: discord.Interaction, button: discord.ui.Button):
    global auctions
    self.auctions = auctions
    self.interaction = interaction
    self.button = button

    price = None

    if self.auctions.get(self.bid_id) is not None:
      if interaction.user.display_name in auctions.get(self.bid_id).itemBidders:
        ind = auctions.get(self.bid_id).itemBidders.index(interaction.user.display_name)
        price = auctions.get(self.bid_id).itemBids[ind]
      await interaction.response.send_modal(Bid_Modal(self.bid_id, self.item, price))
    else:
      button.disabled = True
      await interaction.response.edit_message(view=self)
      await interaction.user.send("This auction has ended")
  
  async def disableButton(self, messageID, interaction: discord.Interaction):
    button1 = [x for x in self.children if x.custom_id == "bidButton"][0]
    button1.disabled = True
    channel = interaction.channel
    message = await channel.fetch_message(messageID)
    await message.edit(view=self)

#Multiple buttons for bidding
class itemButton(discord.ui.Button):
  def __init__(self, bidId, item):
    super().__init__(label = item, style=discord.ButtonStyle.green, custom_id = item)

    self.bid_id = bidId
    self.item = item
    self.price = None

  #price = None

  async def callback(self, interaction: discord.Interaction):
    if auctions.get(self.bid_id) is not None:
        if interaction.user.display_name in auctions.get(self.bid_id).itemBidders:
            ind = auctions.get(self.bid_id).itemBidders.index(interaction.user.display_name)
            self.price = auctions.get(self.bid_id).itemBids[ind]
        await interaction.response.send_modal(Bid_Modal(self.bid_id, self.item, self.price))
    else:
      self.disabled = True
      #await interaction.response.edit_message(view=self)
      await interaction.user.send("This auction has ended")

class activeAuctions(discord.ui.View):
  def __init__(self, auctions):
    super().__init__(timeout = None)
    
    self.auctions = auctions
    
    for x, y in self.auctions.items():
      self.add_item(itemButton(x, y.itemName))


'''    Command to place bid. Obsolete with introduction of button bidding
# Place a Bid
@tree.command(
  name = "bid",
  description = "Place a Bid",
  #guild = discord.Object(id=guildID)
)cc
async def bid(interaction: discord.Interaction, id: str, price: int):

  await interaction.response.defer(ephemeral=True)
  await asyncio.sleep(4)

  global auctions
  if id in auctions:
    if interaction.user.id in auctions.get(id).BidderID:
      index = auctions.get(id).BidderID.index(interaction.user.id)
      if interaction.user.display_name == auctions.get(id).itemBidders[index]:
        auctions.get(id).itemBids[index] = price
        await interaction.followup.send('Bid for ' + auctions.get(id).itemName + ' updated to {:,} Plat.'.format(price), ephemeral = True)
        try:
          await interaction.user.send('Bid for ' + auctions.get(id).itemName + ' updated to {:,} Plat.'.format(price))
        except discord.Forbidden:
          pass
      else:
        await interaction.followup.send('Please do not change your display name after placing a bid. If you believe you received this message in error, please message an officer')
    else:
      auctions.get(id).BidderID.append(interaction.user.id)
      auctions.get(id).itemBids.append(price)
      auctions.get(id).itemBidders.append(interaction.user.display_name)

      await interaction.followup.send('Bid for ' + auctions.get(id).itemName + ' accepted for {:,} Plat.'.format(price), ephemeral = True)
      try:
        await interaction.user.send('Bid for ' + auctions.get(id).itemName + ' accepted for {:,} Plat.'.format(price))
      except discord.Forbidden:
        pass
  else:
    await interaction.followup.send("No active auction under that ID", ephemeral = True)
    return

'''

# List active Auctions
@tree.command(
  name = "activeauctions",
  description = "List the currently active Auctions"
)
async def activeauctions(interaction: discord.Interaction):

  await interaction.response.defer(ephemeral=True)
  #await asyncio.sleep(4)

  global auctions
  theView = discord.ui.View
  

  if auctions == {}:
    await interaction.followup.send("There are no active Auctions", ephemeral=True)
  else:
    theView = activeAuctions(auctions)
    await interaction.followup.send("Active Auctions:", view=theView, ephemeral=True)


#  officer lookup active auctions, specifically item name and id  
@tree.command(
    name = "listauctions",
    description = "Get all auctions with bidbot ids. Helps for canceling stuck items"
)
@discord.app_commands.checks.has_role("Officer")
async def listauctions(interaction: discord.Interaction):
    
    await interaction.response.defer(ephemeral=True)

    global auctions

    if auctions == {}:
       await interaction.followup.send("There are no active Auctions", ephemeral=True)
    else:
       for BidID in auctions:
         active = auctions.get(BidID).itemName + " : " + BidID + "\n"
       await interaction.followup.send(active, ephemeral=True)



# Start an auction
@tree.command(
  name = "startauction",
  description = "Start an Auction"
)
@discord.app_commands.checks.has_role("Officer")
@discord.app_commands.autocomplete(item=item_autocomplete)
async def startauction(interaction: discord.Interaction, item: str, timer: int = None):

 # if not (interaction.channel.permissionsFor(interaction.guild.me).has('SEND_MESSAGES')):
   #   interaction.user.send("Cant send message in that channel, auction not created.")
     # return

  await interaction.response.defer()
  #await asyncio.sleep(4)
  
  display_name = item
  extracted_id = None

  if "|" in item:
      parts = item.split("|", 1)
      extracted_id = parts[0]
      display_name = parts[1]

  
  if timer != None:
    try:
        timer = int(timer)
    except ValueError:
        await interaction.response.send_message('Enter a valid integer for timer in minutes.', ephemeral = True)
        return

  global auctions

  ch1 = '%20'
  ch2 = '%27'
  
  for bid_id in auctions:
    if display_name == auctions.get(bid_id).itemName:
      await interaction.followup.send(display_name + " already up for auction, try again when the current one has completed")
      return

  z = ''.join(random.sample(string.ascii_letters, 4))
  auctions.update({z:Bids()})
  auctions.get(z).itemName = display_name

  itemStats = ''
  itemName = display_name


  replaceSpaces = display_name
  replaceSpaces = replaceSpaces.replace(' ',ch1)
  replaceSpaces = replaceSpaces.replace('\'',ch2) 

  if extracted_id is not None and extracted_id.isdigit():
      
    itemName = display_name
    link = "https://everquest.allakhazam.com/db/item.html?item=" + extracted_id
    auctions.get(z).link = link
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(link, headers=headers)

    if response.status_code != 404:
        EQicon = None
        thing = BeautifulSoup(response.text, features="lxml")
        txt = thing.find('div', {"class" : 'nobgrd'})
        if txt:
           itemStats = txt.get_text()
           auctions.get(z).itemStats = itemStats
           txt = thing.find('img', {"alt" : "EverQuest icon"})
           if txt:
              EQicon = txt.get('src')
              auctions.get(z).EQicon = EQicon



    
  else:
    link = "https://lucy.allakhazam.com/itemlist.html?searchtext=" + replaceSpaces
    
  
    url = "https://eq.magelo.com/quick_search.jspa?keyword=" + replaceSpaces
    auctions.get(z).link = url
    headers = {'accept': 'application/xml;q=0.9, */*;q=0.8'}
    response = requests.get(url, headers=headers)
    

    if response.status_code != 404:
      test = response.text.find('/item/')
      if test != -1:
          test2 = response.text[test:test+20].split('"')
          item_id = test2[0].split('/')
          url = "https://lucy.allakhazam.com/item.html?id=" + item_id[2]
          s = requests.Session()
          s.post(url)

          response = s.get(url)
          if response.status_code != 404:
              thing = BeautifulSoup(response.text, features="lxml")
              itemName = thing.find('table', {"class" : "shottopbg"})
              if itemName != None:
                  EQicon = None
                  itemName = itemName.get_text()
                  itemName = itemName.strip()
                  if txt:
                     txt = thing.find('table', {"class" : 'eqitem'})
                     itemStats = txt.get_text()
                     auctions.get(z).itemStats = itemStats
                     txt = thing.find('img', {"align": "absmiddle"})
                     if txt:
                        EQicon = txt.get('src')
                        auctions.get(z).EQicon = EQicon
              else:
                  itemName = display_name
  
  '''price_data = await get_avg_price(itemName)
  plat_price = None
  if price_data:
      plat_price = price_data.get("averagePlatPrice", "N/A")
      krono_price = price_data.get("averageKronoPrice", "N/A")'''
  #bidCommand = '**/bid id:' + z + ' price: **'

  if timer != None:
    now = time.time()
    seconds = timer * 60
    future_unix = int(now + seconds)

    embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats + "\n\n**BidBot Item ID: " + z + "**\n\n" + f"Auction will end <t:{future_unix}:R>\n")
    '''if plat_price == 1:
        embed.add_field(name="Average Krono Price", value = f"{krono_price:,.2f}", inline= False)
    elif plat_price != None:
        embed.add_field(name="Average Plat Price", value = f"{plat_price:,.2f}", inline= False)'''
    if EQicon:
        embed.set_thumbnail(url=EQicon)
    auctions.get(z).theView = placeABid(z, display_name)
    message = await interaction.followup.send("**" + display_name + "**", embed=embed, view = auctions.get(z).theView)
    auctions.get(z).message = message.id

    await asyncio.sleep(seconds)

    if auctions.get(z) != None:
        await auctions[z].theView.disableButton(auctions[z].message, interaction)

        noBids, winnerAnnounceInteraction, dataInteraction, winner, winnerInteraction = end_auction(z)

        if noBids == None:
            #await interaction.followup.send(winnerAnnounceInteraction)
            embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats + "\n\n**BidBot Item ID: " + z + "**\n\n" + winnerAnnounceInteraction + "\n")
            if EQicon:
                embed.set_thumbnail(url=EQicon)
            try:
                await message.edit(content=winnerAnnounceInteraction, embed = embed, view = None)
            except discord.NotFound:
                interaction.user.send("Message could not be found in order to edit.")
                pass
            try:
                await interaction.user.send(dataInteraction)
            except discord.Forbidden:
                pass

            user = await client.fetch_user(winner)
            try:
                await user.send(winnerInteraction) 
            except discord.Forbidden:
                pass

        else:
            #await interaction.followup.send(noBids)
            embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats + "\n\n**BidBot Item ID: " + z + "**\n\n" + noBids + "\n")
            if EQicon:
                embed.set_thumbnail(url=EQicon)
            await message.edit(content=noBids, embed = embed, view = None)

    else:
        await interaction.user.send("**" + display_name + "** with ID: " + z + " was previously cancelled after timer expired. This message can be ignored if accurate")

  else:
    embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats + "\n\n**BidBot Item ID: " + z + "**\n")
    '''if plat_price == 1:
        embed.add_field(name="Average Krono Price", value = f"{krono_price:,.2f}", inline= False)
    elif plat_price != None:
        embed.add_field(name="Average Plat Price", value = f"{plat_price:,.2f}", inline= False)'''
    if EQicon:
       embed.set_thumbnail(url=EQicon)
    auctions.get(z).theView = placeABid(z, display_name)
    message = await interaction.followup.send("**" + display_name + "**", embed=embed, view = auctions.get(z).theView)
    auctions.get(z).message = message.id
  




#Cancel an auction
@tree.command(
  name = "cancel",
  description = "Cancel an Auction"
)
@discord.app_commands.checks.has_role("Officer")
async def cancel(interaction: discord.Interaction, id:str):
  await interaction.response.defer(ephemeral=True)
  #await asyncio.sleep(4)

  channel = interaction.channel
  message = await channel.fetch_message(auctions[id].message)
  if message is not None:
     await message.edit(content="**" + auctions[id].itemName + "** auction has been canceled.", embed = None, view = None)
  
  await interaction.followup.send("**" + auctions[id].itemName + "** has been canceled")

  del auctions[id]
  

#Ending Auctions
@tree.command(
  name = "endauctions",
  description = "End All Auctions",
)
@discord.app_commands.checks.has_role("Officer")
async def endauctions(interaction: discord.Interaction):

  global auctions
      

  if auctions == {}:
    await interaction.response.send_message("There are no active Auctions")
  else:
    await interaction.response.defer()
    #await asyncio.sleep(4)

    #winners = []
    for i in auctions.values():
      try:
        await i.theView.disableButton(i.message, interaction)
      except:
        continue

    for i in auctions.values():
      
      #key = next(k for k, v in auctions.items() if v == i)
      
      
      noBids, winnerAnnounceInteraction, dataInteraction, winner, winnerInteraction = end_auction(i)
       
      if noBids == None:
            #await interaction.followup.send(winnerAnnounceInteraction)
            embed = discord.Embed(title = "**" + auctions.get(i).itemName + "**", url=auctions.get(i).link, description = auctions.get(i).itemStats + "\n\n**BidBot Item ID: " + i + "**\n\n" + winnerAnnounceInteraction + "\n")
            if auctions.get(i).EQicon:
                embed.set_thumbnail(url=auctions.get(i).EQicon)
            try:
                channel = interaction.channel_id
                message = await channel.fetch_message(auctions.get(i).message)
                await message.edit(content=winnerAnnounceInteraction, embed = embed, view = None)
            except discord.NotFound:
                interaction.user.send("Message could not be found in order to edit.")
                pass
            try:
                await interaction.user.send(dataInteraction)
            except discord.Forbidden:
                pass

            user = await client.fetch_user(winner)
            try:
                await user.send(winnerInteraction) 
            except discord.Forbidden:
                pass

      else:
            #await interaction.followup.send(noBids)
            #embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats + "\n\n**BidBot Item ID: " + z + "**\n\n" + noBids + "\n")
             
            embed = discord.Embed(title = "**" + auctions.get(i).itemName + "**", url=auctions.get(i).link, description = auctions.get(i).itemStats + "\n\n**BidBot Item ID: " + i + "**\n\n" + noBids + "\n")

            if auctions.get(i).EQicon:
                embed.set_thumbnail(url=auctions.get(i).EQicon)
            try:
               channel = interaction.channel_id
               message = await channel.fetch_message(auctions.get(i).message)
               await message.edit(content=noBids, embed = embed, view = None)
            except discord.NotFound:
                interaction.user.send("Message could not be found in order to edit.")
                pass

    
  auctions = {}
      


#End Bid on specific Item
@tree.command(
  name = "endauction",
  description = "End Auction on an item with id"
)
@discord.app_commands.checks.has_role("Officer")
async def endauction(interaction: discord.Interaction, id:str):

  global auctions

  currentTopBid = 0        

  if id not in auctions:
    await interaction.response.send_message("There are no active Auction with that ID")
  else:
    await interaction.response.defer()
    #await asyncio.sleep(2)         
    
    await auctions[id].theView.disableButton(auctions[id].message, interaction)

    currentTopBid = 0
    highestBid = 0
    count = 0
    prevHighest = 0
    prevBid = 0
    
    if auctions[id].itemBids != []:
      for l in auctions[id].itemBids:
        if l > highestBid:
          prevHighest = highestBid
          highestBid = l
          currentTopBid = count
          
        else:
          prevBid = prevHighest
          if (l > prevBid):
            prevHighest = l
            
        count = count + 1  
      await interaction.followup.send("**" + auctions[id].itemName + "** won by **" + auctions[id].itemBidders[currentTopBid]  + "** for **{:,}** platinum".format(prevHighest + 1))
  
      try:
        await interaction.user.send('**' + auctions[id].itemName + ':**\n' + str(auctions[id].BidderID) + '\n' + str(auctions[id].itemBidders) + '\n' + str(auctions[id].itemBids) + '\nWinnner:\n' + auctions[id].itemName + '\n' + auctions[id].itemBidders[currentTopBid] + '\n{:,}'.format(prevHighest +1))
      except discord.Forbidden:
        pass

      user = await client.fetch_user(auctions[id].BidderID[currentTopBid])
      try:
        await user.send("You won **" + auctions[id].itemName + "** for **{:,}** platinum".format(prevHighest + 1)) 
      except discord.Forbidden:
        pass

    else:
      await interaction.followup.send("No one bid on " + auctions[id].itemName + ".")
  
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    today = date.today().strftime('%Y-%m-%d')
    key = id

    cursor.execute("""INSERT INTO auctions ('id', 'seq_id', 'auction_date', 'item_name', 'winner_name', 'winning_price')
        VALUES (?,(SELECT COALESCE(MAX(seq_id), 0) + 1 FROM auctions WHERE id = ?), ?, ?, ?, ?) RETURNING seq_id""", (key, key, today, auctions[id].itemName, auctions[id].itemBidders[currentTopBid], prevHighest + 1))

    comb = list(zip(auctions[id].itemBidders, auctions[id].itemBids))
    data = []
    row = cursor.fetchone()
    if row:
        generated_seq_id = row[0]
    else: 
        cursor.execute("SELECT MAX(seq_id) FROM auctions WHERE id = ?", (key,))
        generated_seq_id = cursor.fetchone()[0]

    for item in comb:
        data.append((key,generated_seq_id) + item)

    cursor.executemany("""INSERT INTO bids ('auction_id', 'bidder_name', 'bid_amount')
        VALUES (?, ?, ?)""", (data))

    connection.commit()
    connection.close()

    del auctions[id]

'''     Unused/Not necessary for Bid Bot 
#Item Lookup
@tree.command(
  name = "search",
  description = "Search for an Item",
  #guild = discord.Object(id=guildID)
)
async def search(interaction: discord.Interaction, item: str):

  await interaction.response.defer()
  #await asyncio.sleep(4)


  ch1 = '%20'
  ch2 = '%27'

  replaceSpaces = item
  replaceSpaces = replaceSpaces.replace(' ',ch1)
  replaceSpaces = replaceSpaces.replace('\'',ch2)        

  link = "https://lucy.allakhazam.com/itemlist.html?searchtext=" + replaceSpaces

  
  url = "https://eq.magelo.com/quick_search.jspa?keyword=" + replaceSpaces
  headers = {'accept': 'application/xml;q=0.9, */*;q=0.8'}
  response = requests.get(url, headers=headers)
  itemStats = ''
  itemName = item

  if response.status_code != 404:
    test = response.text.find('/item/')
    if test != -1:
      test2 = response.text[test:test+20].split('"')
      test3 = test2[0].split('/')
      url = "https://lucy.allakhazam.com/item.html?id=" + test3[2]
      s = requests.Session()
      s.post(url)

      response = s.get(url)
      if response.status_code != 404:
        thing = BeautifulSoup(response.text, features="lxml")
        itemName = thing.find('table', {"class" : "shottopbg"})
        itemName = itemName.get_text()
        itemName = itemName.strip()
        txt = thing.find('table', {"class" : 'eqitem'})
        itemStats = txt.get_text()


  embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats)

  await interaction.followup.send("**" + item + "**", embed=embed)
  '''

@tree.command(name='sync', description='Owner only')
async def sync(interaction: discord.Interaction):
    if interaction.user.id == 99969800821833728:
        await tree.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

'''async def get_avg_price(item_name: str) -> dict | None:
    url = "https://www.tlp-auctions.com/api/prices"
    params = {"serverName": "Frostreaver", "searchTerm": item_name}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            # If the API requires an API key, you'd add headers:
            # headers={"Authorization": "Bearer YOUR_TOKEN"}
            
            if response.status_code == 200:
                data = response.json()
                return data  # This returns the raw JSON dictionary
            return None
        except httpx.HTTPError:
            return None'''



def end_auction(id):
    global auctions

    currentTopBid = 0
    highestBid = 0
    count = 0
    prevHighest = 0
    prevBid = 0
    noBids = None
    
    if auctions[id].itemBids != []:
      for l in auctions[id].itemBids:
        if l > highestBid:
          prevHighest = highestBid
          highestBid = l
          currentTopBid = count
          
        else:
          prevBid = prevHighest
          if (l > prevBid):
            prevHighest = l
            
        count = count + 1  

      winnerAnnounceInteraction = "**" + auctions[id].itemName + "** won by **" + auctions[id].itemBidders[currentTopBid]  + "** for **{:,}** platinum".format(prevHighest + 1)
      dataInteraction = '**' + auctions[id].itemName + ':**\n' + str(auctions[id].BidderID) + '\n' + str(auctions[id].itemBidders) + '\n' + str(auctions[id].itemBids) + '\nWinnner:\n' + auctions[id].itemName + '\n' + auctions[id].itemBidders[currentTopBid] + '\n{:,}'.format(prevHighest +1)
    

      winner = auctions[id].BidderID[currentTopBid]
      winnerInteraction = "You won **" + auctions[id].itemName + "** for **{:,}** platinum".format(prevHighest + 1)
      connection = sqlite3.connect("database.db")
      cursor = connection.cursor()
      today = date.today().strftime('%Y-%m-%d')

      key = id
      cursor.execute("""INSERT INTO auctions ('id', 'seq_id', 'auction_date', 'item_name', 'winner_name', 'winning_price')
        VALUES (?,(SELECT COALESCE(MAX(seq_id), 0) + 1 FROM auctions WHERE id = ?), ?, ?, ?, ?) RETURNING seq_id""", (key, key, today, auctions[id].itemName, auctions[id].itemBidders[currentTopBid], prevHighest + 1))

      comb = list(zip(auctions[id].itemBidders, auctions[id].itemBids))
      data = []
      row = cursor.fetchone()
      if row:
          generated_seq_id = row[0]
      else: 
          cursor.execute("SELECT MAX(seq_id) FROM auctions WHERE id = ?", (key,))
          generated_seq_id = cursor.fetchone()[0]

      for item in comb:
          data.append((key,generated_seq_id) + item)

      cursor.executemany("""INSERT INTO bids ('auction_id', 'seq_id', 'bidder_name', 'bid_amount')
            VALUES (?,?, ?, ?)""", (data))

      connection.commit()
      connection.close()
    else: 
      noBids = "No one bid on " + auctions[id].itemName + "."
  
    

    del auctions[id]

    if noBids == None:
        return None, winnerAnnounceInteraction, dataInteraction, winner, winnerInteraction
    else:
        return noBids, None, None, None, None

client.run(os.environ["DISCORD_TOKEN"])

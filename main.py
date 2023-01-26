import discord, asyncio
from discord import ui, app_commands
import random
import string
import requests
from bs4 import BeautifulSoup
import re
import os

class Bids:
  def __init__(self):
    self.itemName = str
    self.BidderID = []
    self.itemBids = []
    self.itemBidders = []
    self.button = []

global guildID
guildID = int(os.getenv("GUILD_ID"))
channelID = int(os.getenv("CHANNEL_ID"))

class aclient(discord.Client):
  def __init__(self):
    super().__init__(intents=discord.Intents.default())
    self.synced = False

  async def on_ready(self):
    await self.wait_until_ready()
    if not self.synced:
      await tree.sync(guild = discord.Object(id=guildID))
      self.synced = True
      global auctions 
      global memberList
      global bidCommand
      auctions = {}
      
    print(f"I have logged in as {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)

CLEANR = re.compile('<.*?>')

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

#Modal window for Bids
class Bid_Modal(ui.Modal, title = "Default"):
  def __init__(self, id, item):
    super().__init__(timeout = None)
    global auctions
    self.title = item
    self.id = id
    self.auctions = auctions


  bidAmount = ui.TextInput(label = "How much?", style = discord.TextStyle.short, placeholder = "100000", required = True) 
  
  async def on_submit(self, interaction: discord.Interaction):
    price = int(self.children[0].value)
    if interaction.user.id in self.auctions.get(self.id).BidderID:
      index = self.auctions.get(self.id).BidderID.index(interaction.user.id)
      if interaction.user.display_name == self.auctions.get(self.id).itemBidders[index]:
        self.auctions.get(self.id).itemBids[index] = price
        await interaction.response.send_message('Bid for ' + self.auctions.get(self.id).itemName + ' updated to {:,} Plat.'.format(price), ephemeral = True)
        try:
          await interaction.user.send('Bid for ' + self.auctions.get(self.id).itemName + ' updated to {:,} Plat.'.format(price))
        except discord.Forbidden:
          pass
      else:
        await interaction.response.send_message('Please do not change your display name after placing a bid. If you believe you received this message in error, please message an officer')
    else:
      self.auctions.get(self.id).BidderID.append(interaction.user.id)
      self.auctions.get(self.id).itemBids.append(price)
      self.auctions.get(self.id).itemBidders.append(interaction.user.display_name)

      await interaction.response.send_message('Bid for ' + self.auctions.get(self.id).itemName + ' accepted for {:,} Plat.'.format(price), ephemeral = True)
      try:
        await interaction.user.send('Bid for ' + self.auctions.get(self.id).itemName + ' accepted for {:,} Plat.'.format(price))
      except discord.Forbidden:
        pass
  
  async def on_error(self, interaction: discord.Interaction, error):
    if self.id not in self.auctions:
      await interaction.response.send_message("Auction not active", ephemeral = True)
    else:
      await interaction.response.send_message("Enter a valid number", ephemeral = True)


#Button class for bid
class placeABid(discord.ui.View):
  def __init__(self, id, item):
    super().__init__(timeout = None)
    
    self.id = id
    self.item = item
    

  @discord.ui.button(label="Place Bid", style=discord.ButtonStyle.green)
  async def placeBid(self, interaction: discord.Interaction, button: discord.ui.Button):
    #Testing
    global auctions
    self.auctions = auctions
    self.auctions.get(self.id).button = self
    #End Testing
    await interaction.response.send_modal(Bid_Modal(self.id, self.item))

#Multiple buttons for bidding
class itemButton(discord.ui.Button):
  def __init__(self, id, item):
    super().__init__(label = item, style=discord.ButtonStyle.green)

    self.id = id
    self.item = item

  async def callback(self, interaction):
    await interaction.response.send_modal(Bid_Modal(self.id, self.item))

class activeAuctions(discord.ui.View):
  def __init__(self, auctions):
    super().__init__(timeout = None)
    
    self.auctions = auctions

    for x, y in self.auctions.items():
      self.add_item(itemButton(x, y.itemName))




# Place a Bid
@tree.command(
  name = "bid",
  description = "Place a Bid",
  guild = discord.Object(id=guildID)
)
async def bid(interaction: discord.Interaction, id: str, price: int):
  if interaction.channel_id != channelID: return

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



# List active bids
@tree.command(
  name = "activebids",
  description = "List the currently active bids",
  guild = discord.Object(id=guildID)
)
async def activebids(interaction: discord.Interaction):
  if interaction.channel_id != channelID: return

  await interaction.response.defer(ephemeral=True)
  await asyncio.sleep(4)

  global auctions

  activeBids = ""

  if auctions == {}:
    await interaction.followup.send("There are no active Bids", ephemeral=True)
  else:
    #for x, y in auctions.items():
      #activeBids = activeBids + '\n**' + y.itemName + "**\n" + "/bid id:" + x + " price: \n"

    await interaction.followup.send(view = activeAuctions(auctions), ephemeral=True)
    


# Start bids
@tree.command(
  name = "startbids",
  description = "Start a bid",
  guild = discord.Object(id=guildID)
)
@discord.app_commands.checks.has_role("Leadership")
async def startbids(interaction: discord.Interaction, item: str):
  if interaction.channel_id != channelID: return

  await interaction.response.defer()
  await asyncio.sleep(4)

  global auctions

  ch1 = '%20'
  ch2 = '%27'
  
  for id in auctions:
    if item == auctions.get(id).itemName:
      await interaction.followup.send(item + " already up for auction, try again when the current one as completed")
      return

  replaceSpaces = item
  replaceSpaces = replaceSpaces.replace(' ',ch1)
  replaceSpaces = replaceSpaces.replace('\'',ch2)        
  z = ''.join(random.sample(string.ascii_letters, 4))
  auctions.update({z:Bids()})
  auctions.get(z).itemName = item

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
        if itemName != None:
          itemName = itemName.get_text()
          itemName = itemName.strip()
          txt = thing.find('table', {"class" : 'eqitem'})
          itemStats = txt.get_text()
        else:
          itemName = item

  bidCommand = '**/bid id:' + z + ' price: **'

  embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats + "\n>>> To BID copy/paste the entire example below and place your offer within the provided box.\n" + bidCommand + '\n')


  await interaction.followup.send("**" + item + "**", embed=embed, view = placeABid(z, item))




#Ending Bids
@tree.command(
  name = "endbids",
  description = "End All Bids",
  guild = discord.Object(id=guildID)
)
@discord.app_commands.checks.has_role("Leadership")
async def endbids(interaction: discord.Interaction):
  if interaction.channel_id != channelID: return

  global auctions

  currentTopBid = 0        

  if auctions == {}:
    await interaction.response.send_message("There are no active Bids")
  else:
    await interaction.response.defer()
    await asyncio.sleep(4)

    winners = []
    #Testing
    for i in auctions.values():
      i.button.disabled = True
    #End Testing

    for i in auctions.values():            
    
      currentTopBid = 0
      highestBid = 0
      count = 0
      prevHighest = 0
      prevBid = 0
      
      if i.itemBids != []:
        for l in i.itemBids:
          if l > highestBid:
            prevHighest = highestBid
            highestBid = l
            currentTopBid = count
            
          else:
            prevBid = prevHighest
            if (l > prevBid):
              prevHighest = l
              
          count = count + 1  
      else:
        await interaction.followup.send("No one bid on **" + i.itemName + "**.")
        continue
        
        
          
      winners.append([i.itemName, i.itemBidders[currentTopBid], prevHighest + 1, i.BidderID[currentTopBid]])
      
      try:
        await interaction.user.send('**' + i.itemName + ':**\n' + str(i.BidderID) + '\n' + str(i.itemBidders) + '\n' + str(i.itemBids))
      except discord.Forbidden:
        pass

    winningBids = ""


    for p in winners:
      user = await client.fetch_user(p[3])
      try:
        await user.send("You won **" + p[0] + "** for **{:,}** platinum".format(p[2]))
      except discord.Forbidden:
        pass
      winningBids = winningBids + "**" + p[0] + "** won by **" + p[1] + "** for ** {:,} ** platinum\n".format(p[2])


    try:
      await interaction.user.send('**All Winners:**\n' + str(winners))
    except discord.Forbidden:
      pass
    
    await interaction.followup.send(winningBids)

    auctions = {}
    del winners
      


#End Bid on specific Item
@tree.command(
  name = "endbid",
  description = "End Bid on item with id",
  guild = discord.Object(id=guildID)
)
@discord.app_commands.checks.has_role("Leadership")
async def endbid(interaction: discord.Interaction, id:str):
  if interaction.channel_id != channelID: return

  global auctions

  currentTopBid = 0        

  if id not in auctions:
    await interaction.response.send_message("There are no active Bid with that ID")
  else:
    await interaction.response.defer()
    await asyncio.sleep(2)         
    
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
      await interaction.followup.send("**" + auctions[id].itemName + "** won by **" + auctions[id].itemBidders[currentTopBid] + "** for **{:,}** platinum".format(prevHighest + 1))
  
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
  
   
    

    del auctions[id]


#Item Lookup
@tree.command(
  name = "search",
  description = "Search for an Item",
  guild = discord.Object(id=guildID)
)
async def search(interaction: discord.Interaction, item: str):

  await interaction.response.defer()
  await asyncio.sleep(4)


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





client.run(os.environ["DISCORD_TOKEN"])

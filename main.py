import discord, asyncio
from discord import ui, app_commands
import random
import string
from discord import member
import requests
from bs4 import BeautifulSoup
import re
import os 
import sqlite3
from datetime import date

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
    if not self.synced:
      #await tree.sync(guild = discord.Object(id=guildID))
      self.synced = True
      global auctions 
      global memberList
      global bidCommand
      auctions = {}
      
    print(f"I have logged in as {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)

#Multiple Server Test


CLEANR = re.compile('<.*?>')

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext


#Modal window for Bids
class Bid_Modal(ui.Modal, title = "Default"):

  #bidAmount = ui.TextInput(label = "How much would you like to bid?", style = discord.TextStyle.short, placeholder = "100000", required = True)

  def __init__(self, id, item, oldbid):
    super().__init__(timeout = None)
    #global auctions
    if oldbid == None:
      self.bidAmount = discord.ui.TextInput(label = "How much?", style = discord.TextStyle.short, placeholder = "100000", required = True)
    else:
      self.bidAmount = discord.ui.TextInput(label = "How much? Previous bid: {:,}".format(oldbid), style = discord.TextStyle.short, placeholder = "100000", required = True)
    self.add_item(self.bidAmount)
    self.title = item[:45]
    self.id = id
    self.auctions = auctions
  
    






  
  async def on_submit(self, interaction: discord.Interaction):
    #price = int(self.children[0].value) #What? can I change this to bidAmount now?
    price = int(self.bidAmount.value)
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

class inactiveAuction(ui.Modal, title="Auction is Inactive"):
  def __init__(self):
    super().__init__(timeout = 5)


#Button class for bid
class placeABid(discord.ui.View):
  def __init__(self, id, item):
    super().__init__(timeout = None)
    
    self.id = id
    self.item = item

  @discord.ui.button(label="Place Bid", style=discord.ButtonStyle.green, custom_id = "bidButton")
  async def placeBid(self, interaction: discord.Interaction, button: discord.ui.Button):
    global auctions
    self.auctions = auctions
    self.interaction = interaction
    self.button = button

    price = None

    if self.auctions.get(self.id) is not None:
      if interaction.user.display_name in auctions.get(self.id).itemBidders:
        ind = auctions.get(self.id).itemBidders.index(interaction.user.display_name)
        price = auctions.get(self.id).itemBids[ind]
      await interaction.response.send_modal(Bid_Modal(self.id, self.item, price))
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
  def __init__(self, id, item):
    super().__init__(label = item, style=discord.ButtonStyle.green)

    self.id = id
    self.item = item

  price = None

  async def callback(self, interaction):
    if interaction.user.display_name in auctions.get(self.id).itemBidders:
        ind = auctions.get(self.id).itemBidders.index(interaction.user.display_name)
        price = auctions.get(self.id).itemBids[ind]
    await interaction.response.send_modal(Bid_Modal(self.id, self.item, price))

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
  #guild = discord.Object(id=guildID)
)
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



# List active Auctions
@tree.command(
  name = "activeauctions",
  description = "List the currently active Auctions"
)
async def activeauctions(interaction: discord.Interaction):

  await interaction.response.defer(ephemeral=True)
  await asyncio.sleep(4)

  global auctions

  activeAuctions = ""

  if auctions == {}:
    await interaction.followup.send("There are no active Auctions", ephemeral=True)
  else:
    await interaction.followup.send(view = activeAuctions(auctions), ephemeral=True)
    


# Start an auction
@tree.command(
  name = "startauction",
  description = "Start an Auction"
)
@discord.app_commands.checks.has_role("Leadership")
async def startauction(interaction: discord.Interaction, item: str):

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

  embed = discord.Embed(title = "**" + itemName + "**", url=link, description = itemStats + "\n**BidBot Item ID: " + z + "**\n")

  auctions.get(z).theView = placeABid(z, item)
  

  message = await interaction.followup.send("**" + item + "**", embed=embed, view = auctions.get(z).theView)

  auctions.get(z).message = message.id


#Cancel an auction
@tree.command(
  name = "cancel",
  description = "Cancel an Auction"
)
@discord.app_commands.checks.has_role("Leadership")
async def cancel(interaction: discord.Interaction, id:str):
  await interaction.response.defer(ephemeral=True)
  await asyncio.sleep(4)

  channel = interaction.channel
  message = await channel.fetch_message(auctions[id].message)
  await message.edit(content="**" + auctions[id].itemName + "** auction has been canceled.", embed = None, view = None)
  
  await interaction.followup.send("**" + auctions[id].itemName + "** has been canceled")

  del auctions[id]
  

#Ending Bids
@tree.command(
  name = "endauctions",
  description = "End All Auctions",
)
@discord.app_commands.checks.has_role("Leadership")
async def endauctions(interaction: discord.Interaction):

  global auctions

  currentTopBid = 0        

  if auctions == {}:
    await interaction.response.send_message("There are no active Auctions")
  else:
    await interaction.response.defer()
    await asyncio.sleep(4)

    winners = []
    for i in auctions.values():
      await i.theView.disableButton(i.message, interaction)

    for i in auctions.values():
      
      key = next(k for k, v in auctions.items() if v == i)
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
      
      connection = sqlite3.connect("database.db")
      cursor = connection.cursor()
      today = date.today().strftime('%Y-%m-%d')

      cursor.execute("""INSERT INTO auctions ('id', 'seq_id', 'auction_date', 'item_name', 'winner_name', 'winning_price')
        VALUES (?,(SELECT COALESCE(MAX(seq_id), 0) + 1 FROM auctions WHERE id = ?), ?, ?, ?, ?) RETURNING seq_id""", (key, key, today, i.itemName, i.itemBidders[currentTopBid], prevHighest + 1))

      comb = list(zip(i.itemBidders, i.itemBids))
      data = []
      for item in comb:
          data.append((key,cursor.fetchone()[0]) + item)

      cursor.executemany("""INSERT INTO bids ('auction_id', 'seq_id', 'bidder_name', 'bid_amount')
        VALUES (?,?, ?, ?)""", (data))

      connection.commit()
      connection.close()

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
    
    try:
      await interaction.followup.send(winningBids)
    except discord.HTTPException:
      pass

    
    auctions = {}
    del winners
      


#End Bid on specific Item
@tree.command(
  name = "endauction",
  description = "End Auction on an item with id"
)
@discord.app_commands.checks.has_role("Leadership")
async def endauction(interaction: discord.Interaction, id:str):

  global auctions

  currentTopBid = 0        

  if id not in auctions:
    await interaction.response.send_message("There are no active Auction with that ID")
  else:
    await interaction.response.defer()
    await asyncio.sleep(2)         
    
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

    cursor.execute("""INSERT INTO auctions ('id', 'seq_id', 'auction_date', 'item_name', 'winner_name', 'winning_price')
        VALUES (?,(SELECT COALESCE(MAX(seq_id), 0) + 1 FROM auctions WHERE id = ?, ?, ?, ?, ?) RETURNING seq_id""", (key, key, today, i.itemName, i.itemBidders[currentTopBid], prevHighest + 1))

    comb = list(zip(auctions[id].itemBidders, auctions[id].itemBids))
    data = []
    for item in comb:
        data.append((key,cursor.fetchone()[0]) + item)

   # cursor.execute("""INSERT INTO bids ('auction_id', 'bidder_name', 'bid_amount')
   #     VALUES (?, ?, ?)""", (key, auctions[id].itemBidders, auctions[id].itemBids))

    cursor.executemany("""INSERT INTO bids ('auction_id', 'bidder_name', 'bid_amount')
        VALUES (?, ?, ?)""", (data))

    connection.commit()
    connection.close()

    del auctions[id]

      
#Item Lookup
@tree.command(
  name = "search",
  description = "Search for an Item",
  #guild = discord.Object(id=guildID)
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

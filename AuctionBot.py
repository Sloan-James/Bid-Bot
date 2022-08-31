import discord, asyncio
from discord import app_commands
import random
import string



class Bids:
  def __init__(self):
    self.itemName = str
    self.itemBids = []
    self.itemBidders = []

global guildID
guildID = 1005697782859960350

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
      global biddingOpen
      global memberList
      auctions = {}
      biddingOpen = 'CLOSED'
      
    print(f"I have logged in as {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)


# Place a Bid
@tree.command(
  name = "bid",
  description = "Place a Bid",
  guild = discord.Object(id=guildID)
)
@discord.app_commands.checks.has_any_role("Leadership", "Member")
async def bid(interaction: discord.Interaction, id: str, price: int):
  if interaction.channel_id != 1005993249565048893: return

  global auctions
  if id in auctions:
    if (biddingOpen=='OPEN'):
      auctions.get(id).itemBids.append(price)
      auctions.get(id).itemBidders.append(interaction.user.display_name)

      await interaction.response.send_message('Bid for ' + auctions.get(id).itemName + ' accepted for ' + str(price) + ' Plat.', ephemeral = True)
      await interaction.user.send('Bid for ' + auctions.get(id).itemName + ' accepted for ' + str(price) + ' Plat.')
    else:
      await interaction.response.send_message('Failed Bid, Try again', ephemeral = True)
      await interaction.user.send('Failed Bid, Try again')
      return
  else:
    await interaction.response.send_message("No active auction under that ID", ephemeral = True)
    return



# Start bids
@tree.command(
  name = "startbids",
  description = "Start a bid",
  guild = discord.Object(id=guildID)
)
@discord.app_commands.checks.has_role("Leadership")
async def startbids(interaction: discord.Interaction, item: str):
  if interaction.channel_id != 1005993249565048893: return

  global biddingOpen
  global auctions
  biddingOpen = 'OPEN'
  ch1 = '%20'
  ch2 = '%27'
  
  replaceSpaces = item
  replaceSpaces = replaceSpaces.replace(' ',ch1)
  replaceSpaces = replaceSpaces.replace('\'',ch2)        
  z = ''.join(random.sample(string.ascii_letters, 4))
  auctions.update({z:Bids()})
  auctions.get(z).itemName = item

  
  await interaction.response.send_message("**" + item + "**\n" + 
                                          '> https://eq.magelo.com/items?q=' + replaceSpaces +
                                         '\n>>> To BID copy/paste the entire example below and place your offer within the provided box.\n' +
                                         '`/bid id:' + z + ' price: `\n')


#Ending Bids
@tree.command(
  name = "endbids",
  description = "End All Bids",
  guild = discord.Object(id=guildID)
)
@discord.app_commands.checks.has_role("Leadership")
async def endbids(interaction: discord.Interaction):
  if interaction.channel_id != 1005993249565048893: return

  global auctions
        
  currentTopBid = 0        

  if auctions == {}:
    await interaction.response.send_message("There are no active Bids")
  else:
    await interaction.response.defer()
    await asyncio.sleep(2)

    winners = []
    
    for i in auctions.values():            
    
      currentTopBid = 0
      highestBid = 0
      count = 0
      prevHighest = 0
      prevBid = 0
      
      print(i.itemBids)
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
        await interaction.followup.send("No one bid on " + i.itemName + ".")
        continue
        
        
          
      winners.append([i.itemName, i.itemBidders[currentTopBid], prevHighest + 1])
  
    for p in winners: 
      await interaction.followup.send("**" + p[0] + "** won by **" + p[1] + "** for **" + str(p[2]) + "** platinum")
  
    await interaction.user.send('**' + i.itemName + ':**\n' + str(i.itemBidders) + '\n' + str(i.itemBids)) 
    print('**' + i.itemName + ':**\n' + str(i.itemBidders) + '\n' + str(i.itemBids))

    biddingOpen = 'CLOSED'
    auctions = {}
    del winners
      



client.run('MTAxNDQzNDg1NTMzOTE3NTk0Ng.GQ5184.6GDsYYSMfvjRQePSQi_eYuJFYOi2C1MxVYR57k')
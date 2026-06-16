#End Bid on specific Item
def endauction(id:str):

  global auctions

  currentTopBid = 0        

  if id not in auctions:
    await interaction.response.send_message("There are no active Auction with that ID")
  else:
    interaction.response.defer()
    #await asyncio.sleep(2)         
    
    #Disable Button
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

        #Winner announce
      await interaction.followup.send("**" + auctions[id].itemName + "** won by **" + auctions[id].itemBidders[currentTopBid]  + "** for **{:,}** platinum".format(prevHighest + 1))
  
       #Sends data to invoker
      try:
        await interaction.user.send('**' + auctions[id].itemName + ':**\n' + str(auctions[id].BidderID) + '\n' + str(auctions[id].itemBidders) + '\n' + str(auctions[id].itemBids) + '\nWinnner:\n' + auctions[id].itemName + '\n' + auctions[id].itemBidders[currentTopBid] + '\n{:,}'.format(prevHighest +1))
      except discord.Forbidden:
        pass

    # Sends message to winner
      user = await client.fetch_user(auctions[id].BidderID[currentTopBid])
      try:
        await user.send("You won **" + auctions[id].itemName + "** for **{:,}** platinum".format(prevHighest + 1)) 
      except discord.Forbidden:
        pass

    # When no one bids on an auction
    else:
      await interaction.followup.send("No one bid on " + auctions[id].itemName + ".")
  
      #Saves data
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    today = date.today().strftime('%Y-%m-%d')

    cursor.execute("""INSERT INTO auctions ('id', 'seq_id', 'auction_date', 'item_name', 'winner_name', 'winning_price')
        VALUES (?,(SELECT COALESCE(MAX(seq_id), 0) + 1 FROM auctions WHERE id = ?, ?, ?, ?, ?) RETURNING seq_id""", (key, key, today, i.itemName, i.itemBidders[currentTopBid], prevHighest + 1))

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

    #Removes auction data
    del auctions[id]
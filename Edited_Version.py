from collections import _OrderedDictValuesView
import requests,asyncio,locale,telegram,json,threading,os,websockets
from telegram.ext import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
locale.setlocale(locale.LC_ALL,"en_US.UTF8")
token = "6180819073:AAG0Q58j8BiJo92YyenF6-2-kq0hfdCu7qQ"
updater=Updater(token,update_queue=True)
gate = "https://api.gateio.ws/api/v4/spot/tickers"
pairs_url = "https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/pairs"
binance_coin_info = "https://api.binance.com/sapi/v1/capital/config/getall"
kucoin_coin_info = "https://api.kucoin.com/api/v2/currencies/"
binance_ticker = "https://api.binance.com/api/v3/ticker/price"
kucoin_ticker = "https://api.kucoin.com/api/v1/market/allTickers"
order_book = lambda id : "https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/{}/buys?readable=0".format(str(id))
order_book_sell = lambda id : "https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/{}/sells?readable=0".format(str(id))
usdt_price_ramzi_url = "https://publicapi.ramzinex.com/exchange/api/v1.0/exchange/orderbooks/11/sells?readable=0"
priceable = lambda p : locale.currency(p,grouping=1,symbol=0)
main_list = {}
gate_coin = ["ARV_USDT","TONCOIN_USDT"]
kucoin_coin = ["DC-USDT","BITDAO-USDT","ANC-USDT","BONE-USDT","VOLT-USDT","BRISE-USDT","BLUR-USDT","REV-USDT","TEL-USDT","CRO-USDT","KCS-USDT","OKB-USDT","HT-USDT","TITAN-USDT","HEGIC-USDT","VRA-USDT"]
BOX = range(0)
usdt_price = 0
bot_indiviual = telegram.Bot(token=token)
ranges = [[0,10,200],[10,15,250],[15,20,400],[20,40,500],[40,49.9,1000]]
#ranges = [[0,20,200],[20,25,300],[25,35,400],[35,50,1000],[50,100,2000],[100,1000,3000]]
coefficient = {"100LUNC-USDT":["LUNC-USDT",100],"1000BTT-USDT":["BTTC-USDT",1000],
"100XEC-USDT":["XEC-USDT",100],"100SHIB-USDT":["SHIB-USDT",100]}
list_erc20 = ['VRA-USDT', 'HOT-USDT', 'MFT-USDT', 'TITAN-USDT', 'BNT-USDT', 'BADGER-USDT', 'NEXO-USDT', 'WAVES-USDT', 'ENS-USDT', 'API3-USDT', 'QNT-USDT', 'LEVER-USDT', 'OOKI-USDT', 'LOKA-USDT', 'HEGIC-USDT', '1M-KISHU-USDT', 'HT-USDT', 'OMG-USDT', 'OKB-USDT', 'KCS-USDT', 'CRV-USDT', 'GRT-USDT', 'AMP-USDT', 'DENT-USDT', '100STARL-USDT', 'CRO-USDT', 'AUDIO-USDT', 'DYDX-USDT', 'ENJ-USDT', 'HEX-USDT', 'MKR-USDT', 'PUNDIX-USDT', 'COMP-USDT', 'TEL-USDT', 'REV-USDT']
busdt = ["FTTBUSD","SRMBUSD","BTTCBUSD","KEYBUSD","AGIXBUSD","GFTBUSD"]
usdtb = ["FTTUSDT","SRMUSDT","BTTCUSDT","KEYUSDT","AGIXUSDT","GFTUSDT"]
users_json="users.json"
coins_json="coins.json"
networks_json="networks.json"
with open(users_json,"r") as file:
   main_json = json.load(file)
with open(coins_json,"r") as file:
   coinsjson = json.load(file)
with open(networks_json,"r") as file:
   networks = json.load(file)
counter = 1
block_list = {}
ticker_binance = {}
def allowed(diff,tprice):
   a,b = 0,0
   for i in ranges:
      if (i[2]*10**4 <= float(diff) and i[0]*10**7 <= float(tprice) <= i[1]*10**7):
         b = 1
         break
   if b == 0 and float(tprice) >= 50*10**7 and float(tprice)*0.025 <= float(diff):
      b = 1
   if b == 1 and float(tprice) >= 80*10**7 and float(diff) >= 20*10**6:
      a = 1
   return a,b
def get_chain(coin,diff,rprice,id):
   global usdt_price
   erc20_diff = float(main_json["erc20_diff"])*usdt_price
   networks_diff = float(main_json["networks_diff"])
   try:
      if coin in list_erc20:
         return float(diff)-erc20_diff
      else:
         if diff > 2000000:
            return float(diff)-networks_diff
         else:
            return -1
   except: 
      return -1
async def message_to_admin(message):
   for admin in main_json["admin"]:
      try:
         id = main_json["users"][admin][0]
         await bot_indiviual.send_message(id, text=message)
      except:
         continue
async def start(update, context):
    """
    This asynchronous function handles the start command of the bot. It takes the 
    update and context parameters required for the Telegram API.

    It reads a JSON file containing the users' information, and adds the current 
    user to the list if it's not already there. If the user is an admin, the 
    keyboard also contains some additional options.

    Args:
        update (telegram.Update): The update object required by the Telegram API.
        context (telegram.ext.CallbackContext): The context object required by the 
            Telegram API.

    Returns:
        None
    """
    try:
        # Define the keyboard buttons for users
        user_buttons = [
            [telegram.KeyboardButton("Buy/Sell")],
            [telegram.KeyboardButton("Black List")],
            [telegram.KeyboardButton("Add")]
        ]
        # Read the users' data from the JSON file
        with open(users_json, "r") as file:
            main_json = json.load(file)
            username = update.message.chat.username.lower()
            # If the user is not already in the list, add them
            if username not in main_json["users"]:
                main_json["users"][username] = [update.message.chat.id, 1, 0]
                main_json["ban"][username] = []
                # Write the updated data back to the JSON file
                with open(users_json, "w") as file:
                    json.dump(main_json, file)
                # Notify the admin that a user has been added
                await message_to_admin("یوزر با یوزرنیم {} به لیست اضافه شد".format(username))
                # Send a message to the user with the keyboard
                user_keyboard = telegram.ReplyKeyboardMarkup(user_buttons, resize_keyboard=True)
                await update.message.reply_text(text="یوزر شما به لیست یوزر ها اضافه شد ", reply_markup=user_keyboard)
        # If the user is an admin, show the additional options
        if username in main_json["admin"]:
            admin_buttons = user_buttons + [
                [telegram.KeyboardButton("Users")],
                [telegram.KeyboardButton('ERC20 : {}'.format(main_json["erc20_diff"]))],
                [telegram.KeyboardButton('NETWORKS : {}'.format(main_json["networks_diff"]))]
            ]
            admin_keyboard = telegram.ReplyKeyboardMarkup(admin_buttons, resize_keyboard=True)
            await update.message.reply_text(text="Menu", reply_markup=admin_keyboard)
        # If the user is a regular user, show the basic options
        elif username in main_json["users"]:
            user_keyboard = telegram.ReplyKeyboardMarkup(user_buttons, resize_keyboard=True)
            await update.message.reply_text(text="Menu", reply_markup=user_keyboard)
        # If the user is not in the list, show a basic message
        else:
            await update.message.reply_text(text="Menu")
    except Exception:
        pass
async def user_list(update, context):
   """
   Asynchronously lists users based on their usernames. This function takes in two parameters:
   
   - update: an object that represents an incoming Telegram message.
   - context: an object that contains additional information about the message.
   
   This function does not return anything.
   """
   admin_username = update.message.chat.username.lower()
   if admin_username in main_json["admin"]:
      with open(users_json, "r") as users_file:
         users = json.load(users_file)["users"]
         for user in users:
               inline_keyboard = [
                  [InlineKeyboardButton(text="حذف", callback_data=f"delete@{user}")],
                  [InlineKeyboardButton(text="تمام رنج ها", callback_data=f"access@{user}")],
                  [InlineKeyboardButton(text="رنج خصوصی", callback_data=f"deny@{user}")]
               ]
               reply_markup = InlineKeyboardMarkup(inline_keyboard)
               await update.message.reply_text(text=user, reply_markup=reply_markup)
async def change_erc20_diff(update,context):
   text = update.message.text
   if text == 'cancel':
      await start(update,context)
      return ConversationHandler.END
   if text.isnumeric() == False:
      await update.message.reply_text(text="عدد وارد کنید")
      await start(update,context)
      return ConversationHandler.END
   main_json["erc20_diff"] = text
   with open(users_json,"w") as writer:
      json.dump(main_json,writer)
   await update.message.reply_text(text="تغییر کرد : {}".format(text))
   await start(update,context)
   return ConversationHandler.END
async def change_networks_diff(update,context):
   text = update.message.text
   if text == 'cancel':
      await start(update,context)
      return ConversationHandler.END
   if text.isnumeric() == False:
      await update.message.reply_text(text="عدد وارد کنید")
      await start(update,context)
      return ConversationHandler.END
   main_json["networks_diff"] = text
   with open(users_json,"w") as writer:
      json.dump(main_json,writer)
   await update.message.reply_text(text="تغییر کرد : {}".format(text))
   await start(update,context)
   return ConversationHandler.END
async def inlines(update,context):
   if update.message.chat.username.lower() in main_json["users"]:
      with open(users_json,"r") as users:
         ban = json.load(users)["ban"][update.message.chat.username.lower()]
         if len(ban) == 0:
            await update.message.reply_text(text="ارزی در لیست نیست")
         else:
            inlinekeyboard = [[InlineKeyboardButton(text=coin,callback_data="delete_coin@"+coin)] for coin in ban]
            rp = InlineKeyboardMarkup(inlinekeyboard)
            await update.message.reply_text(text="ارز ها",reply_markup=rp)
async def turnoff(update,context):
   try:
      if update.message.chat.username.lower() in main_json["users"].keys():
         if main_json["users"][update.message.chat.username.lower()][1] == 1:
            main_json["users"][update.message.chat.username.lower()][1] = 0
            with open(users_json,"w") as file:
               json.dump(main_json,file)
            await update.message.reply_text(text="خاموش شد")
         else:
            main_json["users"][update.message.chat.username.lower()][1] = 1
            with open(users_json,"w") as file:
               json.dump(main_json,file)
            await update.message.reply_text(text="روشن شد")
   except:
      await update.message.reply_text(text="ناموفق بود")
async def handler(update,context):
   try:
      if update.callback_query.message.chat.username.lower() in main_json["users"]:
         query = update.callback_query.data
         if "@" in query and update.callback_query.message.chat.username.lower() in main_json["users"]:
            is_admin =  update.callback_query.message.chat.username.lower() in main_json["admin"]
            new_query = query.split("@")
            if new_query[0] == "block":
               if update.callback_query.message.chat.username.lower() in block_list.keys():
                  block_list[update.callback_query.message.chat.username.lower()].append(new_query[1])
                  await update.callback_query.edit_message_text(text="بلاک شد")
               else:
                  block_list[update.callback_query.message.chat.username.lower()] = [new_query[1]]
                  await update.callback_query.edit_message_text(text="بلاک شد")
            elif new_query[0] == "delete" and is_admin:
               deleted_user = new_query[1]
               if deleted_user not in main_json["madmin"]:
                  with open(users_json,"r") as files:
                     del main_json["users"][deleted_user]
                     with open(users_json,"w") as writer:
                        json.dump(main_json,writer)
                     await update.callback_query.edit_message_text(text="حدف شد")
            elif new_query[0] == "access" and is_admin:
               edited_user = new_query[1]
               if edited_user not in main_json["madmin"]:
                  main_json["users"][edited_user][2] = 1
                  with open(users_json,"w") as writer:
                     json.dump(main_json,writer)
                  await update.callback_query.edit_message_text(text="روشن شد")
            elif new_query[0] == "deny" and is_admin:
               edited_user = new_query[1]
               if edited_user not in main_json["madmin"]:
                  main_json["users"][edited_user][2] = 0
                  with open(users_json,"w") as writer:
                     json.dump(main_json,writer)
                  await update.callback_query.edit_message_text(text="خاموش شد")
            elif new_query[0] == "delete_coin":
               main_json["ban"][update.callback_query.message.chat.username.lower()].remove(new_query[1])
               with open(users_json,"w") as file:
                  json.dump(main_json,file)
               await update.callback_query.edit_message_text(text="حذف شد")
   except:
      await update.callback_query.edit_message_text(text="ناموفق بود")
async def inital_erc20_diff(update,context):
   if update.message.chat.username.lower() in main_json["users"]:
      if update.message.chat.username.lower() in main_json["admin"]:
         list=[[telegram.KeyboardButton("cancel")]]
         rp=telegram.ReplyKeyboardMarkup(list,resize_keyboard=True)
         await update.message.reply_text(text="مقدار را وارد کنید",reply_markup=rp)
         return ERC20_BOX
async def inital_networks_diff(update,context):
   if update.message.chat.username.lower() in main_json["users"]:
      #if update.message.chat.username.lower() in main_json["admin"]:
         list=[[telegram.KeyboardButton("cancel")]]
         rp=telegram.ReplyKeyboardMarkup(list,resize_keyboard=True)
         await update.message.reply_text(text="مقدار را وارد کنید",reply_markup=rp)
         return NETWORKS_BOX
async def addcoin(update,context):
   if update.message.chat.username.lower() in main_json["users"]:
      #if update.message.chat.username.lower() in main_json["admin"]:
         list=[[telegram.KeyboardButton("cancel")]]
         rp=telegram.ReplyKeyboardMarkup(list,resize_keyboard=True)
         await update.message.reply_text(text="کوین را وارد کنید",reply_markup=rp)
         return BOX
async def addcointext(update,context):
   try:
      text = update.message.text
      if text == 'cancel':
         await start(update,context)
         return ConversationHandler.END
      main_json["ban"][update.message.chat.username.lower()].append(text)
      with open(users_json,"w") as writer:
         json.dump(main_json,writer)
      await update.message.reply_text(text="کوین اضافه شد")
      await start(update,context)
      return ConversationHandler.END
   except:
      await update.message.reply_text(text="ناموفق بود")
      await start(update,context)
      return ConversationHandler.END
async def return1(update,context):
   await start(update,context)
   return ConversationHandler.END
ERC20_BOX,NETWORKS_BOX = range(0),range(0)
conv_change_erc20_diff = ConversationHandler(
   entry_points=[MessageHandler(filters.Regex("^ERC20"),inital_erc20_diff)],
        states={
            ERC20_BOX: [MessageHandler(filters.TEXT & ~filters.COMMAND,change_erc20_diff)],
        },
        fallbacks=[CommandHandler("cancel",return1)],
    )
conv_change_networks_diff = ConversationHandler(
   entry_points=[MessageHandler(filters.Regex("^NETWORKS"),inital_networks_diff)],
        states={
            NETWORKS_BOX: [MessageHandler(filters.TEXT & ~filters.COMMAND,change_networks_diff)],
        },
        fallbacks=[CommandHandler("cancel",return1)],
    )
conv_make_button = ConversationHandler(
   entry_points=[MessageHandler(filters.Regex("Add"),addcoin)],
        states={
            BOX: [MessageHandler(filters.TEXT & ~filters.COMMAND,addcointext)],
        },
        fallbacks=[CommandHandler("cancel",return1)],
    )
async def usdt_dispatcher():
   global usdt_price
   while 1:
      try:
         usdt_price = requests.get(usdt_price_ramzi_url).json()["data"][-1][0]
         await asyncio.sleep(3)
         continue
      except:
         continue
async def max_profit():
   global main_list
   while 1:
      try:
         coins = requests.get(pairs_url).json()["data"]
         for i in coins:
            if (i["quote_currency_symbol"]["en"] == "irr"):
               main_list[str(i["base_currency_symbol"]["en"]).upper()+"-USDT"] = i["pair_id"]
         await asyncio.sleep(10)
      except:
         continue
async def check_buy():
   global main_list
   global counter
   global usdt_price
   global ticker_binance
   while True:
      try:
         global_coins = {}
         ticker_gate = requests.get(gate).json()
         ticker_kucoin = requests.get(kucoin_ticker).json()["data"]["ticker"]
         for i in ticker_gate:
            try:
               if i["currency_pair"] in gate_coin:
                  global_coins[i["currency_pair"].split("_")[0]+"-USDT"] = i["last"]
            except:
               continue
         for i,p in ticker_binance.items():
            try:
               if i.endswith("BUSD") or i.endswith("USDT"):
                  if i in busdt:
                     global_coins[i.split("BUSD")[0]+"-USDT"] = p
                  elif i not in usdtb:
                     global_coins[i.split("USDT")[0]+"-USDT"] = p
            except:
               continue
         for i in ticker_kucoin:
            try:
               if i["symbol"] in kucoin_coin:
               #    # global_coins[i["symbol"]] = i["high"]
                  global_coins[i["symbol"]] = i["last"]

            except:
               continue
         for key,value in main_list.items():
            try:
               if key in list(coefficient.keys()):
                  coe = coefficient[key][1]
                  now_price = float(global_coins[coefficient[key][0]])
               else:
                  now_price = float(global_coins[key])
                  coe = 0
            except KeyError:
               continue
            orders_sell = requests.get(order_book_sell(value)).json()["data"][:5]
            for order in orders_sell:
               amount = float(order[1]) if coe == 0 else float(order[1])/coe
               total = float(order[2]) if coe == 0 else float(order[2])/coe
               diff = float(float(now_price)*float(amount))*usdt_price-total
               chains_diff = get_chain(key,diff,order[0],2)
               if chains_diff != -1:
                  diff = chains_diff
               diff = float(diff)
               is_allowed = allowed(diff,order[2])
               # text = "Diff : {}".format(priceable(diff)) if chains_diff == -1 else  "Diff : {}".format(priceable(diff))
               # text += "\nTPrice : {}\nBUY : {}\nRPrice : {}\nAmount : {}\nGPrice : {}\nUSDT : {}\n".format(priceable(float(order[2])),key,priceable(float(order[0])),priceable(amount),priceable(float(now_price)),priceable(usdt_price))
               # text += "{}".format(counter)
               # print(text)
               if is_allowed[1]:
                  text = "Diff : {}".format(priceable(diff)) if chains_diff == -1 else  "Diff : {}".format(priceable(diff))
                  text += "\nTPrice : {}\nBUY : {}\nRPrice : {}\nAmount : {}\nGPrice : {}\nUSDT : {}\n".format(priceable(float(order[2])),key,priceable(float(order[0])),priceable(amount),priceable(float(now_price)),priceable(usdt_price))
                  text += "{}".format(counter)
                  inlinekeyboard = [[InlineKeyboardButton(text="بلاک",callback_data="block@"+"BUY_"+str(order[2])[:3]+key+"_"+str(amount))]]
                  rp = InlineKeyboardMarkup(inlinekeyboard)
                  if coe != 0:
                     text += "\nCoe : {}".format(str(coe))
                  for username,ids in main_json["users"].items():
                     try:
                        is_blocked = 1
                        if username in block_list.keys():
                           is_blocked = "BUY_"+str(order[2])[:3]+key+"_"+str(amount) not in block_list[username]
                        if ids[2]:
                           if key not in main_json["ban"][username] and is_blocked:
                              await bot_indiviual.send_message(chat_id=ids[0], text=text,reply_markup=rp)
                              await asyncio.sleep(0.01)
                        elif ids[2] == 0 and is_allowed[0]:
                           if key not in main_json["ban"][username] and is_blocked:
                              await bot_indiviual.send_message(chat_id=ids[0], text=text,reply_markup=rp)
                              await asyncio.sleep(0.01)
                     except:
                        continue
                  counter += 1
         for _,ids in main_json["users"].items():
            try:
               if ids[1]:
                  await bot_indiviual.send_message(chat_id=ids[0], text="BUY RECYCLING ... ")
                  await asyncio.sleep(0.01)
            except Exception as e:
               print(e)
               continue
      except Exception as e:
         print(e)

      await asyncio.sleep(3)

async def check_sell():
   global main_list
   global counter
   global usdt_price
   global ticker_binance
   while 1:
      try:
         global_coins = {}
         ticker_gate = requests.get(gate).json()
         ticker_kucoin = requests.get(kucoin_ticker).json()["data"]["ticker"]
         for i in ticker_gate:
            try:
               if i["currency_pair"] in gate_coin:
                  global_coins[i["currency_pair"].split("_")[0]+"-USDT"] = i["last"]
            except:
               continue
         for i,p in ticker_binance.items():
            try:
               if i.endswith("BUSD") or i.endswith("USDT"):
                  if i in busdt:
                     global_coins[i.split("BUSD")[0]+"-USDT"] = p
                  elif i not in usdtb:
                     global_coins[i.split("USDT")[0]+"-USDT"] = p
            except:
               continue
         for i in ticker_kucoin:
            try:
               if i["symbol"] in kucoin_coin:
                  # global_coins[i["symbol"]] = i["high"]
                  global_coins[i["symbol"]] = i["last"]

            except:
               continue
         for key,value in main_list.items():
            try:
               if key in list(coefficient.keys()):
                  coe = coefficient[key][1]
                  now_price = float(global_coins[coefficient[key][0]])
               else:
                  now_price = float(global_coins[key])
                  coe = 0
            except KeyError:
               continue
            orders = requests.get(order_book(value)).json()["data"][:5]
            for order in orders:
               amount = float(order[1]) if coe == 0 else float(order[1])/coe
               total = float(order[2]) if coe == 0 else float(order[2])/coe
               diff = total-(float(now_price)*float(amount)*float(usdt_price))
               chains_diff = get_chain(key,diff,order[0],1)
               if chains_diff != -1:
                  diff = chains_diff
               diff = float(diff)
               is_allowed = allowed(diff,order[2])
               # text = "Diff : {}".format(priceable(diff)) if chains_diff == -1 else  "Diff : {}".format(priceable(diff))
               # text += "\nTPrice : {}\nSELL : {}\nRPrice : {}\nAmount : {}\nGPrice : {}\nUSDT : {}\n".format(priceable(float(order[2])),key,priceable(float(order[0])),priceable(amount),priceable(float(now_price)),priceable(usdt_price))
               # text += "{}".format(counter)
               # print(text)
               if is_allowed[1]:
                  text = "Diff : {}".format(priceable(diff)) if chains_diff == -1 else  "Diff : {}".format(priceable(diff))
                  text += "\nTPrice : {}\nSELL : {}\nRPrice : {}\nAmount : {}\nGPrice : {}\nUSDT : {}\n".format(priceable(float(order[2])),key,priceable(float(order[0])),priceable(amount),priceable(float(now_price)),priceable(usdt_price))
                  text += "{}".format(counter)
                  inlinekeyboard = [[InlineKeyboardButton(text="بلاک",callback_data="block@"+"SELL_"+str(order[2])[:3]+key+"_"+str(amount))]]
                  rp = InlineKeyboardMarkup(inlinekeyboard)
                  if coe != 0:
                     text += "\nCoe : {}".format(str(coe))
                  for username,ids in main_json["users"].items():
                     try:
                        is_blocked = 1
                        if username in block_list.keys():
                           is_blocked = "SELL_"+str(order[2])[:3]+key+"_"+str(amount) not in block_list[username]
                        if ids[2]:
                           if key not in main_json["ban"][username] and is_blocked:
                              await bot_indiviual.send_message(chat_id=ids[0], text=text,reply_markup=rp)
                              await asyncio.sleep(0.01)
                        elif ids[2] == 0 and is_allowed[0]:
                           if key not in main_json["ban"][username] and is_blocked:
                              await bot_indiviual.send_message(chat_id=ids[0], text=text,reply_markup=rp)
                              await asyncio.sleep(0.01)
                     except:
                        continue
                  counter += 1
         for _,ids in main_json["users"].items():
            try:
               if ids[1]:
                  await bot_indiviual.send_message(chat_id=ids[0], text="SELL RECYCLING ... ")
                  await asyncio.sleep(0.01)
            except Exception as e:
               print(e)
               continue
      except Exception as e:
         print(e)
         continue
      await asyncio.sleep(3)
async def binance_socket():
   global ticker_binance
   coin_types = dict(coinsjson).keys()
   updated_ticker_binance = {}
   while True:
      try:
         result = requests.get(binance_ticker).json()
         for i in result:
             if i["symbol"] in coin_types:
               updated_ticker_binance[i["symbol"]] = i["price"]
         ticker_binance = updated_ticker_binance
         await asyncio.sleep(3)
      except:
         continue
def run1():
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(asyncio.gather(
      max_profit()
   ))
def run2():
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(asyncio.gather(
      check_sell(),check_buy()
   ))
# def run3():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(check_buy())
def run4():
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(usdt_dispatcher())
def run5():
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   loop.run_until_complete(binance_socket())
if __name__ == "__main__":
   bot = Application.builder().token(token).build()
   bot.add_handler(CommandHandler("start",start))
   bot.add_handler(CallbackQueryHandler(handler))
   bot.add_handler(conv_make_button)
   bot.add_handler(conv_change_networks_diff)
   bot.add_handler(conv_change_erc20_diff)
   bot.add_handler(MessageHandler(filters.Regex("Users"),user_list))
   bot.add_handler(MessageHandler(filters.Regex("Buy/Sell"),turnoff))
   bot.add_handler(MessageHandler(filters.Regex("Black List"),inlines))

   threading.Thread(target=run2).start()
   threading.Thread(target=run1).start()
   # threading.Thread(target=run3).start()
   threading.Thread(target=run4).start()
   threading.Thread(target=run5).start()
   bot.run_polling(1,pool_timeout=5,timeout=15)

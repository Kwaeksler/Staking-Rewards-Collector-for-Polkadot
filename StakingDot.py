# |--------------------------------------------------------------------------------------
# | Repository: Staking-Rewards-Collector-for-Polkadot
# | Description: Create a JSON-Report with Staking-Reward-Informations for Polkadot
# | Version: 1.0
# | Author: Daniel H.
# | Author URI: https://github.com/Kwaeksler
# | License: GNU General Public License v3.0
# |--------------------------------------------------------------------------------------

import json
import time
import requests
import os.path
from datetime import datetime
from requests.structures import CaseInsensitiveDict
from _functions.functions import checkAmount, getSimpleHistoryPrice, getAccurateHistoryPrice

t1 = time.perf_counter()
em = 0

### Configuration #############################################################
API_Key = ""
Wallet_Address = ""
File_Name = 'DOTRewards'                        # Without file extension - Example: 'Rewards'
Prices = 'No'        	                        # Possible values: 'Fast' or 'Accurate' or 'No'
Only_Updates = True                             # Possible values: True or False
Debug = True                                    # Possible values: True or False
###############################################################################
### CoinTracking Configuration: ###############################################
###############################################################################
CointrackingCSV = True                        # Possible values: True or False
CSV_File_Name = 'DOT_Rewards_Cointracking'    # Without file extension - Example: 'Rewards_Cointracking'
CT_Exchange = "Polkadot Rewards"              # Optional column for Import
CT_TradeGroup = ""                            # Optional column for Import
CT_Comment = "DOT Staking Reward"             # Optional column for Import
###############################################################################

### Check Configuration
if not (Prices == 'Fast' or Prices == 'Accurate' or Prices == 'No'):
    print(f"\nFehler: Der Wert der Variable 'Prices' muss 'Fast', 'Accurate' oder 'No' sein - Das Programm wurde beendet!\n")
    if Debug == True:
        print("-------------------------------------------------------------------------------")
        print("\nDrücke 'Enter', um das Fenster zu schließen ...")
        input()
    exit()

if not Wallet_Address:
    print(f"\nFehler: Es wurde keine Wallet-Adresse gesetzt - Das Programm wurde beendet!\n")
    if Debug == True:
        print("-------------------------------------------------------------------------------")
        print("\nDrücke 'Enter', um das Fenster zu schließen ...")
        input()
    exit()

if not (Only_Updates == True or Only_Updates == False):
    print(f"\nFehler: Der Wert der Variable 'Only_Updates' muss True oder False sein - Das Programm wurde beendet!\n")
    if Debug == True:
        print("-------------------------------------------------------------------------------")
        print("\nDrücke 'Enter', um das Fenster zu schließen ...")
        input()
    exit()

### Starting Skript, get Subscan.io Information
print(f"\nStatus: Die Konfiguration wurde erfolgreich überprüft, das Skript wird ausgeführt ...\n")
URL = "https://polkadot.api.subscan.io/api/scan/account/reward_slash"
File_Name = File_Name + ".json"
CSV_File_Name = CSV_File_Name + ".csv"

headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"
headers["X-API-Key"] = API_Key
payload = '{"row": 100, "page": 0, "address": "' + Wallet_Address + '"}'

r = requests.post(URL, headers=headers, data=payload)
rewards_json = r.json()

### Check HTTPS-Request to Subscan.io
if r.ok is not True:
    print(f"Fehler: Verbindungsaufbau mit Subscan.io nicht möglich (Error-Code: {r.status_code}) - Das Programm wurde beendet!\n")
    if Debug == True:
        print("-------------------------------------------------------------------------------")
        print("\nDrücke 'Enter', um das Fenster zu schließen ...")
        input()
    exit()
elif rewards_json['message'] == 'Success':
    print("Status: Verbindungsaufbau mit Subscan.io war erfolgreich\n")

### This is where the magic happens :-) #######################################
fileexists = os.path.exists(File_Name)

if Only_Updates == True and fileexists == True:
    ### If 'Only_Updates' is set to True
    f = open (File_Name, "r")
    file_data = json.loads(f.read())
    f.close()

    results = file_data
    lastID = file_data[-1]['ID']
    nextID = lastID + 1
    reward_count = rewards_json['data']['count']
    reward_diff = reward_count - lastID
    data_id = reward_diff - 1

    if reward_diff > 0:
        if reward_diff > 1:
            print(f"Status: Es sind {reward_diff} neue Datensätze vorhanden, Informationen werden abgerufen\n")
            if reward_diff > 100:
                queries = reward_diff // 10
                remainder = reward_diff-(queries*10)

                if remainder > 0:
                    queries=queries+1

                maxentries = queries*10                
                page = queries - 1
                RewardID = reward_count - maxentries + 1

                while queries > 0: # > 0
                    page = queries - 1
                    payload = '{"row": 10, "page": ' + str(page) + ', "address": "' + Wallet_Address + '"}'
                    r = requests.post(URL, headers=headers, data=payload)
                    rewards_json = r.json()

                    ########## CHECK STATUS ##########
                    if r.ok is not True:
                        if r.status_code == 429:
                            print("-------------------------------------------------------------------------------")
                            print(f"Status: Zu viele API-Anfragen bei Subscan.io - Skript wird für {r.headers['Retry-After']} Sekunde(n) pausiert und anschließend fortgesetzt ...")
                            print("-------------------------------------------------------------------------------\n")
                            time.sleep(int(r.headers["Retry-After"]))

                            r = requests.post(URL, headers=headers, data=payload)
                            rewards_json = r.json()
                        else:
                            print(f"Fehler: Verbindungsaufbau mit Subscan.io nicht möglich (Error-Code: {r.status_code}) - Das Programm wurde beendet!\n")
                            if Debug == True:
                                print("-------------------------------------------------------------------------------")
                                print("\nDrücke 'Enter', um das Fenster zu schließen ...")
                                input()
                            exit()
                    elif rewards_json['message'] == 'Success':
                        print("Status: Verbindungsaufbau mit Subscan.io war erfolgreich\n")

                    entries = len(rewards_json['data']['list'])        
                     
                    while entries > 0:
                        if RewardID > lastID:
                            reward_amount = rewards_json['data']['list'][entries-1]['amount']
                            reward_amount = int(reward_amount)
                            reward_amount = checkAmount(reward_amount)
                            reward_timestamp_unix = rewards_json['data']['list'][entries-1]['block_timestamp']
                            reward_timestamp_dt = datetime.fromtimestamp(reward_timestamp_unix)
                            reward_block = rewards_json['data']['list'][entries-1]['block_num']
                            reward_extrinsic_idx = rewards_json['data']['list'][entries-1]['extrinsic_idx']
                            reward_eventid = rewards_json['data']['list'][entries-1]['event_idx']
                            reward_hash = rewards_json['data']['list'][entries-1]['extrinsic_hash']
                            reward_url = f"https://polkadot.subscan.io/extrinsic/{reward_block}-{reward_extrinsic_idx}?event={reward_block}-{reward_eventid}"
                            
                            ### Get prices, if desired
                            if (Prices == 'Fast' or Prices == 'Accurate'):
                                if Prices == 'Fast':
                                    datum = reward_timestamp_dt
                                    datum = datum.strftime('%d-%m-%Y')
                                    usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                                    dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                                    print(f"Status: 'Einfache' Preise (USDT/EUR & DOT/USD) für Reward-ID: {RewardID} wurden abgefragt\n")
                                else:
                                    usdt = getAccurateHistoryPrice('tether', reward_timestamp_unix, 'eur')
                                    dot = getAccurateHistoryPrice('polkadot', reward_timestamp_unix, 'usd')
                                    
                                    if usdt == 0 or dot == 0:
                                        datum = reward_timestamp_dt
                                        datum = datum.strftime('%d-%m-%Y')
                                        usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                                        dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                                        print(f"Status: Es konnten keine 'Detailierten' Preise für Reward-ID: {RewardID} abgefragt werden, stattdessen wurden 'Einfache' Preise abgefragt\n")
                                    else:
                                        print(f"Status: 'Detailierte' Preise (USDT/EUR & DOT/USD) für Reward-ID: {RewardID} wurden abgefragt\n")

                            else:
                                usdt = 0
                                dot = 0
                                print(f"Status: Es wurden keine Preise (USDT/EUR & DOT/USD) für Reward-ID: {RewardID} abgefragt\n")

                            data = {
                                'ID': RewardID,
                                'Amount': reward_amount,
                                'Date': reward_timestamp_dt,
                                'DOT/USDT': dot,
                                'USDT/EUR': usdt,
                                'Block': reward_block,
                                'EventID': reward_eventid,
                                'HASH': reward_hash,
                                'URL': reward_url
                            }

                            results.append(data)

                        RewardID = RewardID + 1
                        entries = entries -1

                    page = page - 1
                    queries = queries - 1
        else:
            print(f"Status: Es ist ein neuer Datensatz vorhanden, Informationen werden abgerufen\n")
    else:
        em = 1

    while data_id >= 0 and reward_diff <= 100:
        ### Get needed information from the Subscan-Request and format
        reward_amount = rewards_json['data']['list'][data_id]['amount']
        reward_amount = int(reward_amount)
        reward_amount = checkAmount(reward_amount)
        reward_timestamp_unix = rewards_json['data']['list'][data_id]['block_timestamp']
        reward_timestamp_dt = datetime.fromtimestamp(reward_timestamp_unix)
        reward_block = rewards_json['data']['list'][data_id]['block_num']
        reward_extrinsic_idx = rewards_json['data']['list'][data_id]['extrinsic_idx']
        reward_eventid = rewards_json['data']['list'][data_id]['event_idx']
        reward_hash = rewards_json['data']['list'][data_id]['extrinsic_hash']
        reward_url = f"https://polkadot.subscan.io/extrinsic/{reward_block}-{reward_extrinsic_idx}?event={reward_block}-{reward_eventid}"

        ### Get prices, if desired
        if (Prices == 'Fast' or Prices == 'Accurate'):
            if Prices == 'Fast':
                datum = reward_timestamp_dt
                datum = datum.strftime('%d-%m-%Y')
                usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                print(f"Status: 'Einfache' Preise (USDT/EUR & DOT/USD) für Reward-ID: {nextID} wurden abgefragt\n")
            else:
                usdt = getAccurateHistoryPrice('tether', reward_timestamp_unix, 'eur')
                dot = getAccurateHistoryPrice('polkadot', reward_timestamp_unix, 'usd')

                if usdt == 0 or dot == 0:
                    datum = reward_timestamp_dt
                    datum = datum.strftime('%d-%m-%Y')
                    usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                    dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                    print(f"Status: Es konnten keine 'Detailierten' Preise für Reward-ID: {nextID} abgefragt werden, stattdessen wurden 'Einfache' Preise abgefragt\n")
                else:
                    print(f"Status: 'Detailierte' Preise (USDT/EUR & DOT/USD) für Reward-ID: {nextID} wurden abgefragt\n")

        else:
            usdt = 0
            dot = 0
            print(f"Status: Es wurden keine Preise (USDT/EUR & DOT/USD) für Reward-ID: {nextID} abgefragt\n")

        ### Format the data for the JSON-File
        data = {
            'ID': nextID,
            'Amount': reward_amount,
            'Date': reward_timestamp_dt,
            'DOT/USDT': dot,
            'USDT/EUR': usdt,
            'Block': reward_block,
            'EventID': reward_eventid,
            'HASH': reward_hash,
            'URL': reward_url
        }

        results.append(data)
        nextID = nextID + 1
        data_id = data_id - 1

else:
    ### If 'Only_Updates' is set to False or the file does not exists
    if Only_Updates == True and fileexists == False:
        print(f"Status: Die Datei ({File_Name}) existiert nicht, 'Only-Update'-Modus nicht möglich\n")
    if Only_Updates == False and fileexists == True:
        os.remove(File_Name) 
        print("Status: Bestehende Datei wurde gelöscht, da der 'Only-Update'-Modus deaktiviert ist - Der gesamte Staking-Verlauf wird neu erstellt\n")
    
    i = 0
    results = []
    reward_count = rewards_json['data']['count']

    if reward_count > 100:
        queries = reward_count // 10
        remainder = reward_count-(queries*10)
        RewardID = 1

        if remainder > 0:
            queries=queries+1

        while queries > 0:         
            page = queries - 1
            payload = '{"row": 10, "page": ' + str(page) + ', "address": "' + Wallet_Address + '"}'

            r = requests.post(URL, headers=headers, data=payload)
            rewards_json = r.json()

            ########## CHECK STATUS ##########
            if r.ok is not True:
                if r.status_code == 429:
                    print("-------------------------------------------------------------------------------")
                    print(f"Status: Zu viele API-Anfragen bei Subscan.io - Skript wird für {r.headers['Retry-After']} Sekunde(n) pausiert und anschließend fortgesetzt ...")
                    print("-------------------------------------------------------------------------------\n")
                    time.sleep(int(r.headers["Retry-After"]))

                    r = requests.post(URL, headers=headers, data=payload)
                    rewards_json = r.json()
                else:
                    print(f"Fehler: Verbindungsaufbau mit Subscan.io nicht möglich (Error-Code: {r.status_code}) - Das Programm wurde beendet!\n")
                    if Debug == True:
                        print("-------------------------------------------------------------------------------")
                        print("\nDrücke 'Enter', um das Fenster zu schließen ...")
                        input()
                    exit()
            elif rewards_json['message'] == 'Success':
                print("Status: Abfrage der Reward-Informationen bei Subscan.io war erfolgreich\n")

            entries = len(rewards_json['data']['list'])            
            while entries > 0:
                reward_amount = rewards_json['data']['list'][entries-1]['amount']
                reward_amount = int(reward_amount)
                reward_amount = checkAmount(reward_amount)
                reward_timestamp_unix = rewards_json['data']['list'][entries-1]['block_timestamp']
                reward_timestamp_dt = datetime.fromtimestamp(reward_timestamp_unix)
                reward_block = rewards_json['data']['list'][entries-1]['block_num']
                reward_extrinsic_idx = rewards_json['data']['list'][entries-1]['extrinsic_idx']
                reward_eventid = rewards_json['data']['list'][entries-1]['event_idx']
                reward_hash = rewards_json['data']['list'][entries-1]['extrinsic_hash']
                reward_url = f"https://polkadot.subscan.io/extrinsic/{reward_block}-{reward_extrinsic_idx}?event={reward_block}-{reward_eventid}"

                ### Get prices, if desired
                if (Prices == 'Fast' or Prices == 'Accurate'):
                    if Prices == 'Fast':
                        datum = reward_timestamp_dt
                        datum = datum.strftime('%d-%m-%Y')
                        usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                        dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                        print(f"Status: 'Einfache' Preise (USDT/EUR & DOT/USD) für Reward-ID: {RewardID} wurden abgefragt\n")
                    else:
                        usdt = getAccurateHistoryPrice('tether', reward_timestamp_unix, 'eur')
                        dot = getAccurateHistoryPrice('polkadot', reward_timestamp_unix, 'usd')
                        if usdt == 0 or dot == 0:
                            datum = reward_timestamp_dt
                            datum = datum.strftime('%d-%m-%Y')
                            usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                            dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                            print(f"Status: Es konnten keine 'Detailierten' Preise für Reward-ID: {RewardID} abgefragt werden, stattdessen wurden 'Einfache' Preise abgefragt\n")
                        else:
                            print(f"Status: 'Detailierte' Preise (USDT/EUR & DOT/USD) für Reward-ID: {RewardID} wurden abgefragt\n")

                else:
                    usdt = 0
                    dot = 0
                    print(f"Status: Es wurden keine Preise (USDT/EUR & DOT/USD) für Reward-ID: {RewardID} abgefragt\n")

                data = {
                    'ID': RewardID,
                    'Amount': reward_amount,
                    'Date': reward_timestamp_dt,
                    'DOT/USDT': dot,
                    'USDT/EUR': usdt,
                    'Block': reward_block,
                    'EventID': reward_eventid,
                    'HASH': reward_hash,
                    'URL': reward_url
                }

                results.append(data)
                
                RewardID = RewardID + 1 
                entries = entries -1

            page = page - 1
            queries = queries - 1
    
    else: 
        while i < reward_count:
            ### Get needed information from the Subscan-Request and format
            reward_amount = rewards_json['data']['list'][i]['amount']
            reward_amount = int(reward_amount)
            reward_amount = checkAmount(reward_amount)
            reward_timestamp_unix = rewards_json['data']['list'][i]['block_timestamp']
            reward_timestamp_dt = datetime.fromtimestamp(reward_timestamp_unix)
            reward_block = rewards_json['data']['list'][i]['block_num']
            reward_extrinsic_idx = rewards_json['data']['list'][i]['extrinsic_idx']
            reward_eventid = rewards_json['data']['list'][i]['event_idx']
            reward_hash = rewards_json['data']['list'][i]['extrinsic_hash']
            reward_url = f"https://polkadot.subscan.io/extrinsic/{reward_block}-{reward_extrinsic_idx}?event={reward_block}-{reward_eventid}"

            ### Get prices, if desired
            if (Prices == 'Fast' or Prices == 'Accurate'):
                if Prices == 'Fast':
                    datum = reward_timestamp_dt
                    datum = datum.strftime('%d-%m-%Y')
                    usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                    dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                    print(f"Status: 'Einfache' Preise (USDT/EUR & DOT/USD) für Reward-ID: {reward_count-i} wurden abgefragt\n")
                else:
                    usdt = getAccurateHistoryPrice('tether', reward_timestamp_unix, 'eur')
                    dot = getAccurateHistoryPrice('polkadot', reward_timestamp_unix, 'usd')

                    if usdt == 0 or dot == 0:
                        datum = reward_timestamp_dt
                        datum = datum.strftime('%d-%m-%Y')
                        usdt = getSimpleHistoryPrice('tether', datum, 'eur')
                        dot = getSimpleHistoryPrice('polkadot', datum, 'usd')
                        print(f"Status: Es konnten keine 'Detailierten' Preise für Reward-ID: {reward_count-i} abgefragt werden, stattdessen wurden 'Einfache' Preise abgefragt\n")
                    else:
                        print(f"Status: 'Detailierte' Preise (USDT/EUR & DOT/USD) für Reward-ID: {reward_count-i} wurden abgefragt\n")

            else:
                usdt = 0
                dot = 0
                print(f"Status: Es wurden keine Preise (USDT/EUR & DOT/USD) für Reward-ID: {reward_count-i} abgefragt\n")

            ### Format the data for the JSON-File
            data = {
                'ID': reward_count-i,
                'Amount': reward_amount,
                'Date': reward_timestamp_dt,
                'DOT/USDT': dot,
                'USDT/EUR': usdt,
                'Block': reward_block,
                'EventID': reward_eventid,
                'HASH': reward_hash,
                'URL': reward_url
            }

            results.insert(0, data)
            i = i + 1

### End of magic ############################################################## 

### Insert list to JSON-File
with open(File_Name, 'w') as f:
    json.dump(results, f, indent=2, default=str)
f.close()

### Print final statement
fileexists = os.path.exists(File_Name)

if fileexists == True:
    if em == 1:
        print(f"Status: Es sind keine neuen Datensätze vorhanden, es wurden keine Änderungen an der Datei ({File_Name}) durchgeführt")
    else:
        print(f"Status: Die Datei ({File_Name}) wurde erfolgreich erstellt bzw. aktualisiert")
else:
    print(f"\nFehler: Die Datei {File_Name} konnte nicht erstellt bzw. aktualisiert werden, bitte erneut versuchen")

### Creating a CSV-File for https://cointracking.info/import/import_csv/
if CointrackingCSV == True:
    f = open (File_Name, "r")
    file_data = json.loads(f.read())
    f.close()

    lastID = file_data[-1]['ID']
    CSVHeader = '"Type", "Buy Amount", "Buy Currency", "Sell Amount", "Sell Currency", "Fee", "Fee Currency", "Exchange", "Trade-Group", "Comment", "Date", "Tx-ID"'

    fileexists = os.path.exists(CSV_File_Name)
    if fileexists == True:
        os.remove(CSV_File_Name)
 
    i = 0
    with open(CSV_File_Name,'a') as file:
        while i <= lastID-1:
            if i == 0:
                file.write(CSVHeader)

            CSVLine = f'"Staking", "{file_data[i]["Amount"]}", "DOT2", "", "", "", "{CT_TradeGroup}", "{CT_Exchange}", "", "{CT_Comment}", "{file_data[i]["Date"]}", "{file_data[i]["URL"]}"'
            file.write("\n" + CSVLine)

            i = i + 1
    
    file.close()

    fileexists = os.path.exists(CSV_File_Name)
    if fileexists == True:
        print(f"\nStatus: Die CSV-Datei ({CSV_File_Name}) wurde für den CoinTracking-Import erstellt bzw. aktualisiert")

else:
    fileexists = os.path.exists(CSV_File_Name)
    if fileexists == True:
        os.remove(CSV_File_Name)
    
################################################################

### Calculate runtime
t2 = time.perf_counter()
runtime = t2-t1
print("\nInfo: Skript-Laufzeit: %.4f sek.\n" % runtime)

if Debug == True:
    print("-------------------------------------------------------------------------------")
    print("\nDrücke 'Enter', um das Fenster zu schließen ...")
    input()
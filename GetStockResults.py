import pandas as pd
import requests
from datetime import date
import csv
import numpy as np
from datetime import timedelta

# Load the transactions file and filter rows that start with 'Trades'
transactions_file = "Resources/Transaktioner - Exportfil från Aktiemäklaren.csv"
exchange_rate_file = "Resources/Riksgälden Valutakurser 2024.csv"
trades_result_list = pd.DataFrame(columns=['Header', 'Date/Time', 'Quantity', 'TotalQuantityTraded', 'Symbol', "T. Price", "Comm/Fee", "Currency", 'Buying_Prize','Selling_Prize', 'USD_to_SEK', 'TotalBuyingPrize', 'TotalSellingPrize', 'Net_gain'])

trades_result_list_to_K4_PDF = pd.DataFrame(columns=['Date', 'TotalQuantityTraded', 'Symbol', 'TotalBuyingPrize', 'TotalSellingPrize', 'TotalBuyingPrize_perStock', 'TotalSellingPrize_perStock', 'Net_gain', "AdditionalInfo", "TraderName", "PersonalNumber", "CurrentDate"])
important_columns_list = ['Header', "Date/Time", "Quantity", "Symbol", "T. Price", "Comm/Fee", "Currency"]


def extract_additional_info(file_path):
    info = []
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=",", quotechar='"')
        for row in reader:
            if row[0] == "Account Information" and len(row) > 1:  # Skip malformed or incomplete rows
                info.append(row)
    
    info = pd.DataFrame(info)

    info.columns = info.iloc[0]
    info = info[1:][0:]
    info.reset_index(drop=True, inplace=True)
    info = info.reset_index(drop=True)
    return info

# Extract trades from the transactions file
def extract_trades(file_path):
    trades = []
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=",", quotechar='"')
        for row in reader:
            if row[0] == "Trades" and len(row) > 1:  # Skip malformed or incomplete rows
                trades.append(row)
    
    trades = pd.DataFrame(trades)

    trades.columns = trades.iloc[0]
    trades = trades[1:][0:]
    trades.reset_index(drop=True, inplace=True)
    
    return trades

# Load exchange rates and filter for USD to SEK on a specific date
def get_usd_to_sek_rate(file_path, target_date):



    exchange_rate_df = pd.read_csv(file_path, sep=';', encoding='utf-8')
    exchange_rate_df.columns = [col.strip() for col in exchange_rate_df.columns]
    exchange_rate_df['Datum'] = pd.to_datetime(exchange_rate_df['Datum'], format='%Y-%m-%d')
    exchange_rate_df['Värde'] = exchange_rate_df['Värde'].str.replace(',', '.').astype(float)
    target_date_modified = pd.to_datetime(target_date.split()[0][0:-1], format='%Y-%m-%d')


    if exchange_rate_df['Datum'].eq(target_date_modified).any():
        rate = exchange_rate_df[
        (exchange_rate_df['Serie'] == '1 USD') & (exchange_rate_df['Datum'] == target_date_modified)
    ]['Värde']
        
    else:
        # Find the closest date
        nearest_index = exchange_rate_df['Datum'].searchsorted(target_date_modified, side="left")

        if nearest_index >= len(exchange_rate_df):
            nearest_index = len(exchange_rate_df) - 1
        elif nearest_index > 0 and abs((exchange_rate_df['Datum'].iloc[nearest_index] - target_date_modified).days) > abs((exchange_rate_df['Datum'].iloc[nearest_index - 1] - target_date_modified).days):
            nearest_index -= 1
        nearest_date = exchange_rate_df['Datum'].iloc[nearest_index]
        #print(f"Transaction date: {target_date_modified}. Nearest matching date for USD to SEK: {nearest_date}")
        target_date_modified = nearest_date

    rate = exchange_rate_df[
        (exchange_rate_df['Serie'] == '1 USD') & (exchange_rate_df['Datum'] == target_date_modified)
    ]['Värde']

    return rate.values[0] if not rate.empty else None



def Build_trades_result_list(trades_df_local):

    for column in trades_df_local.columns.tolist():
        if column in important_columns_list:

            trades_result_list[column] = trades_df_local[column]

            
    trades_result_list["Quantity"] = trades_result_list["Quantity"].replace("", np.nan)
    trades_result_list["Quantity"] = trades_result_list["Quantity"].str.replace(",", "").astype(float)
            
    for index, row in trades_result_list.iterrows(): 

        if row["Date/Time"] != "":
            
            USD_to_SEK_float = get_usd_to_sek_rate(exchange_rate_file, row["Date/Time"])
            USD_to_SEK_float = float(USD_to_SEK_float)
            trades_result_list.loc[index, "USD_to_SEK"] = USD_to_SEK_float

            if float(row["Quantity"]) > 0:
                trades_result_list.loc[index, "Buying_Prize"] = (
                    float(trades_result_list.loc[index, "T. Price"]) * 
                    float(trades_result_list.loc[index, "Quantity"]) * 
                    USD_to_SEK_float
                    + abs(float(trades_result_list.loc[index, "Comm/Fee"]))*USD_to_SEK_float
                )

            else:
                trades_result_list.loc[index, "Selling_Prize"] = (
                    float(trades_result_list.loc[index, "T. Price"]) * 
                    -float(trades_result_list.loc[index, "Quantity"]) * 
                    USD_to_SEK_float
                    - abs(float(trades_result_list.loc[index, "Comm/Fee"]))*USD_to_SEK_float
                )
        
        
        elif row["Header"] == "SubTotal":
            symbol_to_check = row["Symbol"]  # Change this to the symbol you want to filter
            # Find all rows with the same symbol
            same_symbol_rows = trades_result_list[trades_result_list["Symbol"] == symbol_to_check]
            # Extract the "Buying_Prize" values
            total_qunatity_bought_list = same_symbol_rows["Quantity"].dropna().tolist()
            buying_prizes_list = same_symbol_rows["Buying_Prize"].dropna().tolist()
            selling_prizes_list = same_symbol_rows["Selling_Prize"].dropna().tolist()


            #print(f"Buying_Prize values for symbol {symbol_to_check}: {buying_prizes}")
            TotalQuantityBought = sum(quantity for quantity in total_qunatity_bought_list if quantity > 0)
            TotalBuyingPrize = sum(buying_prizes_list)
            TotalSellingPrize = sum(selling_prizes_list)
            trades_result_list.loc[index, "TotalQuantityTraded"] = TotalQuantityBought
            trades_result_list.loc[index, "TotalBuyingPrize"] = TotalBuyingPrize
            trades_result_list.loc[index, "TotalSellingPrize"] = TotalSellingPrize
            trades_result_list.loc[index, "Net_gain"] = TotalSellingPrize - TotalBuyingPrize


def Build_trades_result_list_to_K4_PDF(trades_result_list_to_K4_PDF_local, PersonalNumber):
    
    today = date.today()
    trades_result_list_to_K4_PDF_local.loc[0, "PaperNumber"] = 1 
    trades_result_list_to_K4_PDF_local.loc[0, "CurrentDate"] = today.strftime("%Y-%m-%d")
    
    info = extract_additional_info(transactions_file)
    info_name_row_index = info[info["Field Name"] == "Name"].index[0]

    trades_result_list_to_K4_PDF_local.loc[0, "TraderName"] = info.loc[info_name_row_index, "Field Value"]
    

    trades_result_list_to_K4_PDF_local.loc[0, "PersonalNumber"] = str(PersonalNumber)
    
    for index, row in trades_result_list.iterrows(): 
        if row["Header"] == "SubTotal":
            trades_result_list_to_K4_PDF_local.loc[index, "TotalQuantityTraded"] = int(abs(row["TotalQuantityTraded"]))
            trades_result_list_to_K4_PDF_local.loc[index, "Symbol"] = row["Symbol"]
            trades_result_list_to_K4_PDF_local.loc[index, "TotalBuyingPrize_perStock"] = row["TotalBuyingPrize"]/abs(row["TotalQuantityTraded"])
            trades_result_list_to_K4_PDF_local.loc[index, "TotalSellingPrize_perStock"] = row["TotalSellingPrize"]/abs(row["TotalQuantityTraded"])
            trades_result_list_to_K4_PDF_local.loc[index, "TotalBuyingPrize"] = row["TotalBuyingPrize"]
            trades_result_list_to_K4_PDF_local.loc[index, "TotalSellingPrize"] = row["TotalSellingPrize"]
            trades_result_list_to_K4_PDF_local.loc[index, "Net_gain"] = row["Net_gain"]


    trades_result_list_to_K4_PDF_local = trades_result_list_to_K4_PDF_local.reset_index(drop=True)
    return trades_result_list_to_K4_PDF_local
            
# Main function to calculate stock gain
def calculate_stock_gain(transactions_file, exchange_rate_file, PersonalNumber):
    trades_df = extract_trades(transactions_file)

    # Assuming trades_df has relevant columns like Quantity, Price, Fees, etc.
    Build_trades_result_list(trades_df)
    return Build_trades_result_list_to_K4_PDF(trades_result_list_to_K4_PDF, PersonalNumber)

PersonalNumber = "123-111"
# Example usage
calculate_stock_gain(transactions_file, exchange_rate_file, PersonalNumber)



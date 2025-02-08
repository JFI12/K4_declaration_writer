from pdfrw import PdfReader, PdfWriter, PdfDict
import GetStockResults
import pandas as pd
import math
import os
# Load the PDF template
template_path = 'Resources/Tom K4 från SKV.pdf'  # Replace with the path to your PDF file
output_path = 'K4_PDF_Map/filled_K4_form.pdf'  # Output file path

transactions_file = "Resources/Transaktioner - Exportfil från Aktiemäklaren.csv"
exchange_rate_file = "Resources/Riksgälden Valutakurser 2024.csv"


imported_data = GetStockResults.calculate_stock_gain(transactions_file, exchange_rate_file)

# Define the data to fill in the form
""" data = {
    # General Information
    'TxtDatFramst[0]': '2023-10-01',  # Example: Date of preparation
    'TxtFler[0]': 'Additional info',  # Example: Additional information
    'TxtSkattskyldig-namn[0]': 'John Doe',  # Example: Taxpayer's name
    'TxtPersOrgNr[0]': '123456-7890',  # Example: Personal/organization number

    # Section A: Marknadsnoterade aktier, aktieindexobligationer, aktieoptioner m.m.
    'TxtAntal[0]': '100',  # Example: Quantity
    'TxtBeteckning[0]': 'AAPL',  # Example: Designation (e.g., stock symbol)
    'TxtForsaljningspris[0]': '15000',  # Example: Selling price in SEK
    'TxtOmkostnadsbelopp[0]': '10000',  # Example: Cost basis in SEK
    'TxtVinst[0]': '5000',  # Example: Profit
    'TxtForlust[0]': '',  # Leave empty if no loss

    # Section B: Återföring av uppskovsbelopp
    'TxtUppskovsbelopp[0]': '2000',  # Example: Deferred amount

    # Section C: Marknadsnoterade obligationer, valuta m.m.
    'TxtAntal[1]': '5000',  # Example: Quantity
    'TxtBeteckning[1]': 'USD',  # Example: Designation (e.g., currency code)
    'TxtForsaljningspris[1]': '45000',  # Example: Selling price in SEK
    'TxtOmkostnadsbelopp[1]': '40000',  # Example: Cost basis in SEK
    'TxtVinst[1]': '5000',  # Example: Profit
    'TxtForlust[1]': '',  # Leave empty if no loss

    # Section D: Övriga värdepapper, andra tillgångar
    'TxtAntal[2]': '10',  # Example: Quantity
    'TxtBeteckning[2]': 'BTC',  # Example: Designation (e.g., Bitcoin)
    'TxtForsaljningspris[2]': '300000',  # Example: Selling price in SEK
    'TxtOmkostnadsbelopp[2]': '200000',  # Example: Cost basis in SEK
    'TxtVinst[2]': '100000',  # Example: Profit
    'TxtForlust[2]': '',  # Leave empty if no loss

    # Summary Section
    'TxtSummaForsaljningspris[0]': '500000',  # Example: Total selling price
    'TxtSummaOmkostnadsbelopp[0]': '400000',  # Example: Total cost basis
    'TxtSummaVinst[0]': '100000',  # Example: Total profit
    'TxtSummaForlust[0]': '',  # Leave empty if no loss
} """

def decode_field_name(encoded_name):
    # Decode each field name


    # Remove the 'FEFF' BOM and convert the hex string to bytes
    hex_string = encoded_name[4:]  # Remove the BOM
    byte_data = bytes.fromhex(hex_string)  # Convert hex to bytes
    # Decode the bytes using UTF-16BE
    decoded_name = byte_data.decode('utf-16be')

    return decoded_name

def calculate_end_sums():
    # Initialize the variables
    TxtForsaljningspris = [0]
    TxtOmkostnadsbelopp = [0]
    TxtVinst = [0]
    TxtForlust = [0]

    # Example decoded_name_result
    decoded_name_result = 'TxtForsaljningspris[0]'

    # Update variables based on decoded_name_result
    match decoded_name_result:
        case 'TxtForsaljningspris[0]':
            TxtForsaljningspris[0] = 100  # Example value
        case 'TxtOmkostnadsbelopp[0]':
            TxtOmkostnadsbelopp[0] = 50   # Example value
        case 'TxtVinst[0]':
            TxtVinst[0] = 30              # Example value
        case 'TxtForlust[0]':
            TxtForlust[0] = 20            # Example value
        case _:
            print("Unknown decoded_name_result")

def Remove_PDFs():
    folder_path = "K4_PDF_Map"  # Replace with your folder path

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):  # Check if it's a file
            os.remove(file_path)

def Create_PDF(data):

    PDF_K4_Number = data.at[0, "TxtFler[0]"]
    #PDF_K4_Number = data["TxtFler[0]"].iloc[0]
    
    # Load the PDF
    template_pdf = PdfReader(template_path) 
    # Fill in the form fields
    for page in template_pdf.pages:

        if page['/Annots']:
            
            for annot in page['/Annots']:
                
                if annot['/Subtype'] == '/Widget' and annot['/T']:
                    field_name = annot['/T'][1:-1]  # Remove parentheses from field name
                    decoded_name_result = decode_field_name(field_name)


                    if decoded_name_result in data.columns:
                        PDF_element = int(annot.get("/StructParent"))
                        data_index = math.floor((PDF_element + 1 )/6)
                        data_index = data_index + (PDF_K4_Number - 1)*11
                        
                        
                        if PDF_element > 62 or (data_index > len(data) - 1):

                            # Save the filled PDF
                            PdfWriter().write(output_path[0:-4] + str(int(PDF_K4_Number)) + output_path[-4:], template_pdf)
                            print(f"Filled PDF saved to {output_path[0:-4] + str(int(PDF_K4_Number)) + output_path[-4:]}")
                            return 
                        
                        value = data.loc[data_index, decoded_name_result]
                      #  print(f'decoded_name_result: {decoded_name_result}, data_index: {data_index}, value: {value}')
                      #  calculate_end_sums(decoded_name_result, value)
  
                        annot.update(PdfDict(V=str(value)))
                        

        
    # Save the filled PDF
    PdfWriter().write(output_path, template_pdf)
    print(f"Filled PDF saved to {output_path}")

def get_input_data():
    input_data = []  # List of dictionaries to collect rows
    max_9_counter = 0
    sum_9_values_gain = 0
    sum_9_values_loss = 0

    for _, row in imported_data.iterrows():
        if row["Symbol"]:

            input_data.append({
                'TxtDatFramst[0]': row["CurrentDate"],
                'TxtFler[0]': row["PaperNumber"],
                'TxtSkattskyldig-namn[0]': row["TraderName"],
                'TxtPersOrgNr[0]': row["PersonalNumber"],
                'TxtBeteckning[0]': row["Symbol"],
                'TxtAntal[0]': row["TotalQuantityTraded"],
                'TxtForsaljningspris[0]': row["TotalSellingPrize_perStock"],
                'TxtOmkostnadsbelopp[0]': row["TotalBuyingPrize_perStock"],
                'TxtVinst[0]': max(0, row["Net_gain"]),
                'TxtForlust[0]': abs(min(0, row["Net_gain"])),
                'TxtSummaVinst[0]': None,
                'TxtSummaForlust[0]': None
            })

            if row["Net_gain"] > 0:
                sum_9_values_gain += row["Net_gain"]
       
            elif row["Net_gain"] <= 0:
                sum_9_values_loss += abs(row["Net_gain"])
                
            max_9_counter += 1
            if max_9_counter == 10:

                max_9_counter = 1
                input_data.append({
                    'TxtDatFramst[0]': None, 
                    'TxtFler[0]': None, 
                    'TxtSkattskyldig-namn[0]': None, 
                    'TxtPersOrgNr[0]': None, 
                    'TxtBeteckning[0]': None, 
                    'TxtAntal[0]': None, 
                    'TxtForsaljningspris[0]': None, 
                    'TxtOmkostnadsbelopp[0]': None, 
                    'TxtVinst[0]': None, 
                    'TxtForlust[0]': None, 
                    'TxtSummaVinst[0]': sum_9_values_gain, 
                    'TxtSummaForlust[0]': sum_9_values_loss
                })
                sum_9_values_gain = 0
                sum_9_values_loss = 0

                input_data.append({
                'TxtDatFramst[0]': imported_data.loc[0, "CurrentDate"], 
                'TxtFler[0]': imported_data.loc[0, "PaperNumber"], 
                'TxtSkattskyldig-namn[0]': imported_data.loc[0, "TraderName"], 
                'TxtPersOrgNr[0]': imported_data.loc[0, "PersonalNumber"], 
                'TxtBeteckning[0]': None, 
                'TxtAntal[0]': None, 
                'TxtForsaljningspris[0]': None, 
                'TxtOmkostnadsbelopp[0]': None, 
                'TxtVinst[0]': None, 
                'TxtForlust[0]': None, 
                'TxtSummaVinst[0]': None, 
                'TxtSummaForlust[0]': None
                })


    if input_data[-1]['TxtPersOrgNr[0]'] is None and input_data[-1]['TxtDatFramst[0]'] is not None:
        input_data = input_data[:-1]  # Remove the last row


    amount_PDF_rows_local = len(input_data)
    print(f'amount_PDF_rows_local: {amount_PDF_rows_local}')
    if amount_PDF_rows_local%11 != 0:
        extra_empy_row_rows_local = 10-amount_PDF_rows_local%11
        
    # Check if the last row's last column is None
    if input_data[-1]['TxtSummaForlust[0]'] is None:
        for row_index in range(1, extra_empy_row_rows_local + 1):
            # Append a new row with specified values
            input_data.append({
                'TxtDatFramst[0]': "",
                'TxtFler[0]': "",
                'TxtSkattskyldig-namn[0]': "",
                'TxtPersOrgNr[0]': "",
                'TxtBeteckning[0]': "",
                'TxtAntal[0]': "",
                'TxtForsaljningspris[0]': "",
                'TxtOmkostnadsbelopp[0]': "",
                'TxtVinst[0]': "",
                'TxtForlust[0]': "",
                'TxtSummaVinst[0]': "",
                'TxtSummaForlust[0]': ""
            })
        input_data.append({
        'TxtDatFramst[0]': None,
        'TxtFler[0]': None,
        'TxtSkattskyldig-namn[0]': None,
        'TxtPersOrgNr[0]': None,
        'TxtBeteckning[0]': None,
        'TxtAntal[0]': None,
        'TxtForsaljningspris[0]': None,
        'TxtOmkostnadsbelopp[0]': None,
        'TxtVinst[0]': None,
        'TxtForlust[0]': None,
        'TxtSummaVinst[0]': sum_9_values_gain,
        'TxtSummaForlust[0]': sum_9_values_loss
        })
                        
    # Convert list of dictionaries to a DataFrame
    input_data = pd.DataFrame(input_data)
    return input_data



Remove_PDFs()
input_data = get_input_data()
amount_PDF_rows = len(input_data)
amount_PDF_pages = math.ceil((amount_PDF_rows)/11)
print(input_data)
for page_index in range(1, amount_PDF_pages + 1):
    input_data.at[0, "TxtFler[0]"] = page_index  # at is faster for single element access
    input_data.at[(page_index-1)*11, "TxtFler[0]"] = page_index  # at is faster for single element access
  #  input_data.loc[0, "TxtFler[0]"] = page_index
    #print(input_data.loc[0, "TxtFler[0]"])
    Create_PDF(input_data)


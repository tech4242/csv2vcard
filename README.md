# python-csv-to-vcard
A Python script that parses a .csv file of contacts and automatically creates vCards. The vCards are super useful for sending your contact details or those of your team. You can also upload them to e.g. Dropbox and use them with QR codes! You can also use them for transering new contacts to Outlook, a new CRM etc. The specific use case in mind was to programmatically create vCards from a list of contacts in a spreadsheet, to be incorporated into business cards.

# Usage

1. Create CSV table with contacts

*CSV file format (easily done in Excel)*

| last_name | first_name | org | title | phone | email | website | street | city | p_code | country |
|---|---|---|---|---|---|---|---|---|---|---|
| ...  |   |   |   |   |   |   |   |   |   |   |

**Important: you should name the columns exactly the same way because they are used as keys to generate the vCards**

2. Download `csv_to_vcard.py`

3. Open python `python3` (gotcha: using Python 3.6 features)

4. Import module `import csv_to_vcard`

5. Run script `csv_to_vcard.csv_to_vcard(your_file_name)`. This will create an /export/ dir with your vCards!

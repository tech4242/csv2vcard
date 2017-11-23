# python-excel-to-vcard
A Python script that parses a .csv file of contacts and automatically creates vCards. The vCards are super useful for QR codes etc. You can also use them for transering new contacts to Outlook, a new CRM etc.

# Usage

1. Create CSV table with contacts

*CSV file format (easily done in Excel)*

| last_name | first_name | org | title | phone | email | website | street | city | p_code | country |
|---|---|---|---|---|---|---|---|---|---|---|
| ...  |   |   |   |   |   |   |   |   |   |   |

**Important: you should name the columns exactly the same way because they are used as keys to generate the vCards**

2. Download `excel_to_vcard.py`

3. Open python `python3` (gotcha: using Python 3.6 features)

4. Import module `import excel_to_vcard`

5. Run script `excel_to_vcard.excel_to_vcard(your_file_name)`. This will create an /export/ dir with your vCards!

# csv2vcard
A Python script that parses a .csv file of contacts and automatically creates vCards. The vCards are super useful for sending your contact details or those of your team. You can also upload them to e.g. Dropbox and use them with QR codes! You can also use them for transferring new contacts to Outlook, a new CRM etc. The specific use case in mind was to programmatically create vCards from a list of contacts in a spreadsheet, to be incorporated into business cards.

# Usage

1. Create CSV table with contacts

*CSV file format (easily done in Excel)*

| last_name | first_name | org | title | phone | email | website | street | city | p_code | country |
|---|---|---|---|---|---|---|---|---|---|---|
| ...  |   |   |   |   |   |   |   |   |   |   |

**Important: you should name the columns exactly the same way because they are used as keys to generate the vCards**

2. `git clone` or download and `cd` to folder

3. Open python `python3` (gotcha: using Python 3.6 features)

4. Import module `from csv2vcard import csv2vcard`

5. Now you have 2 options for running. Both will create an /export/ dir with an example vCards.

  * Test the app with `csv2vcard.test_csv2vcard()`. This will create a Forrest Gump test vCard!
  * Use your real data `csv2vcard.csv2vcard(yourfilename)`. This will create all your vCards!

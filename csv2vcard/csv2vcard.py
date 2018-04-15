from csv2vcard.export_vcard import check_export, export_vcard
from csv2vcard.create_vcard import create_vcard
from csv2vcard.parse_csv import parse_csv


def csv2vcard(csv_filename: str, csv_delimeter: str):
    """
    Main function
    """
    check_export()

    for c in parse_csv(csv_filename, csv_delimeter):
        vcard = create_vcard(c)
        export_vcard(vcard)


def test_csv2vcard():
    """
    Try it out with this mock Forrest Gump contact
    """
    mock_contacts = [{
        "last_name": "Gump", "first_name": "Forrest", "title": "Shrimp Man",
        "org": "Bubba Gump Shrimp Co.",
        "phone": "+49 170 5 25 25 25", "email": "forrestgump@example.com",
        "website": "https://www.linkedin.com/in/forrestgump",
        "street": "42 Plantation St.", "city": "Baytown", "p_code": "30314",
        "country": "United States of America"
    }]
    check_export()
    vcard = create_vcard(mock_contacts[0])
    print(vcard)
    export_vcard(vcard)

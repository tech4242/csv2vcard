import csv
import codecs
import os


def csv_to_vcard(csv_filename: str):
    """
    Main function
    """
    check_export()

    for c in parse_csv(csv_filename):
        vcard = create_vcard(c)
        export_vcard(vcard)


def parse_csv(csv_filename: str):
    """
    Simple csv parser with a ; delimiter
    """
    print("Parsing csv..")
    try:
        with codecs.open(f"{csv_filename}", "r", "utf-8-sig") as f:
            contacts = csv.reader(f, delimiter=";")
            header = next(contacts)  # saves header
            parsed_contacts = [dict(zip(header, row)) for row in contacts]
            return parsed_contacts
    except IOError:
        print(f"I/O error for {csv_filename}")
        return []


def create_vcard(contact: dict):
    """
    The mappings used below are from https://www.w3.org/TR/vcard-rdf/#Mapping
    """
    vc_begin = "BEGIN:VCARD\n"
    vc_version = "VERSION:3.0\n"
    vc_name = f"N;CHARSET=UTF-8:{contact['last_name']};{contact['first_name']};;;\n"
    vc_title = f"TITLE;CHARSET=UTF-8:{contact['title']}\n"
    vc_org = f"ORG;CHARSET=UTF-8:{contact['org']}\n"
    vc_phone = f"TEL;TYPE=WORK,VOICE:{contact['phone']}\n"
    vc_email = f"EMAIL;TYPE=WORK:{contact['email']}\n"
    vc_website = f"URL;TYPE=WORK:{contact['website']}\n"
    vc_address = f"ADR;TYPE=WORK;CHARSET=UTF-8:{contact['street']};{contact['city']};{contact['p_code']};{contact['country']}\n"
    vc_end = "END:VCARD\n"

    vc_filename = f"{contact['last_name'].lower()}_{contact['first_name'].lower()}.vcf"
    vc_output = vc_begin + vc_version + vc_name + vc_title + vc_org + vc_phone + vc_email + vc_website + vc_address + vc_end

    vc_final = {
        "filename" : vc_filename,
        "output" : vc_output
    }

    return vc_final


def export_vcard(vc_final):
    """
    Exporting a vCard to /export/
    """
    try:
        with open(f"export/{vc_final['filename']}", "w") as f:
            f.write(vc_final['output'])
            f.close()
            print(f"Created 3.0 vCard for {vc_final['output']['last_name']}, {vc_final['output']['first_name']}.")
    except IOError:
        print(f"I/O error for {vc_final['filename']}")


def check_export():
    """
    Checks if export folder exists in directory
    """
    if not os.path.exists("export"):
        os.makedirs("export")


def test_csv_to_vcard():
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
    create_vcard(mock_contacts[0])

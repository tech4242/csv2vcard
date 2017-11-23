import csv
import codecs
import os


def parse_csv(csv_filename: str):
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
    vc_filename = f"{contact['last_name'].lower()}_{contact['first_name'].lower()}.vcf"
    vc_begin = "BEGIN:VCARD\n"
    vc_version = "VERSION:4.0\n"
    vc_name = f"N;charset=utf-8:{contact['last_name']};{contact['first_name']};;;\n"
    vc_title = f"TITLE;charset=utf-8:{contact['title']}\n"
    vc_org = f"ORG;charset=utf-8:{contact['org']}\n"
    vc_phone = f"TEL;type=work,voice:{contact['phone']}\n"
    vc_email = f"EMAIL;type=work:{contact['email']}\n"
    vc_website = f"URL;type=work:{contact['website']}\n"
    vc_address = f"ADR;type=work;charset=utf-8:{contact['street']};{contact['city']};{contact['p_code']};{contact['country']}\n"
    vc_end = "END:VCARD\n"

    # check if the export directory exists
    if not os.path.exists("export"):
        os.makedirs("export")

    # save vCard to /export/
    try:
        with open(f"export/{vc_filename}", "w") as f:
            f.writelines([vc_begin, vc_version, vc_name, vc_title, vc_org, vc_phone, vc_email, vc_website, vc_address, vc_end])
            f.close()
            print(f"Created vCard for {contact['last_name']}, {contact['first_name']}.")
    except IOError:
        print(f"I/O error for {vc_filename}")


def excel_to_vcard(csv_filename: str):
    # mock with Forrest Gump
    mock_contacts = [{"last_name": "Gump", "first_name": "Forrest", "title": "Shrimp Man", "org": "Bubba Gump Shrimp Co.",
                 "phone": "+49 170 5 25 25 25", "email": "forrestgump@example.com",
                 "website": "https://www.linkedin.com/in/forrestgump",
                 "street": "42 Plantation St.", "city": "Baytown", "p_code": "30314",
                 "country": "United States of America"}]
    for c in parse_csv(csv_filename):
        create_vcard(c)

def parse_excel():
    print("Parsing excel..")
    # parse excel
    return []


def create_vcard(contact: dict):
    """
    The mappings used below are from https://www.w3.org/TR/vcard-rdf/#Mapping
    """
    vc_begin = "BEGIN:VCARD\n"
    vc_version = "VERSION:4.0\n"
    vc_name = f"N;charset=utf-8:{contact['last_name']};{contact['first_name']};;;\n"
    vc_title = f"TITLE;charset=utf-8:{contact['title']}\n"
    vc_org = f"ORG;charset=utf-8:{contact['org']}\n"
    vc_phone = f"TEL;type=work,voice:{contact['phone']}\n"
    vc_email = f"EMAIL;type=work:{contact['email']}\n"
    vc_linkedin = f"URL;type=work:{contact['linkedin']}\n"
    vc_address = f"ADR;type=work;charset=utf-8:{contact['address']['street']};{contact['address']['city']};{contact['address']['p_code']};{contact['address']['country']}\n"
    vc_end = "END:VCARD\n"

    fo = open(f"{contact['last_name'].lower()}_{contact['first_name'].lower()}.vcf", "w")
    fo.writelines([vc_begin, vc_version, vc_name, vc_title, vc_org, vc_phone, vc_email, vc_linkedin, vc_address, vc_end])
    fo.close()

    print(f"Created vCard for {contact['last_name']}")


def excel_to_vcard():
    #contacts = parse_excel()
    # mock with Forrest Gump
    contacts = [{"last_name": "Gump", "first_name": "Forrest", "title": "Shrimp Man", "org": "Bubba Gump Shrimp Co.",
                 "phone": "+49 170 5 25 25 25", "email": "forrestgump@example.com",
                 "linkedin": "https://www.linkedin.com/in/forrestgump",
                 "address": {"street": "42 Plantation St.", "city": "Baytown", "p_code": "30314",
                             "country": "United States of America"}}]
    for c in contacts:
        create_vcard(c)

def parse_excel():
    print("Parsing excel..")
    # parse excel
    return []


def create_vcard(contact):
    vc_begin = "begin:vcard\n"
    vc_version = "version:4.0\n"
    vc_name = f"n;charset=utf-8:{contact['last_name']};{contact['first_name']};;;\n"
    vc_title = f"title;charset=utf-8:{contact['title']}\n"
    vc_org = f"org;charset=utf-8:{contact['org']}\n"
    vc_phone = f"tel;type=work,voice:{contact['phone']}\n"
    vc_end = "end:vcard\n"

    fo = open(f"{contact['last_name'].lower()}.vcf", "w")
    fo.writelines([vc_begin, vc_version, vc_name, vc_title, vc_org, vc_phone, vc_end])
    fo.close()

    print(f"Created vCard for {contact['last_name']}")


def excel_to_vcard():
    #contacts = parse_excel()
    # mock with Forrest Gump
    contacts = [{"last_name": "Gump", "first_name": "Forrest", "title": "Shrimp Man", "org": "Bubba Gump Shrimp Co.",
                 "phone": "+49 170 5 25 25 25"}]
    for c in contacts:
        create_vcard(c)

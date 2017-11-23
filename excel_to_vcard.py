def parse_excel():
    print("Parsing excel..")
    # parse excel
    return []


def create_vcard(contact):
    print("Creating vCard for" + contact.name)
    # output vcf file
    return None


def excel_to_vcard():
    contacts = parse_excel()
    for c in contacts:
        create_vcard(c)

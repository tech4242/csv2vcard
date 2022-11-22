def create_vcard(contact: dict):
    """
    The mappings used below are from https://www.w3.org/TR/vcard-rdf/#Mapping
    """
    vc_begin = "BEGIN:VCARD\n"
    vc_version = "VERSION:3.0\n"
    vc_name = f"N;CHARSET=UTF-8:{contact.get('last_name', '')};{contact.get('first_name', '')};;;\n"
    vc_fullname = f"FN;CHARSET=UTF-8:{contact.get('first_name', '')} {contact.get('last_name', '')}\n"
    vc_title = f"TITLE;CHARSET=UTF-8:{contact.get('title', '')}\n" if contact.get('title', '') != '' else ""
    vc_org = f"ORG;CHARSET=UTF-8:{contact.get('org', '')}\n" if contact.get('org', '') != '' else ""
    vc_phone = f"TEL;TYPE=WORK,VOICE:{contact.get('phone', '')}\n" if contact.get('phone', '') != '' else ""
    vc_email = f"EMAIL;TYPE=WORK:{contact.get('email', '')}\n" if contact.get('email', '') != '' else ""
    vc_website = f"URL;TYPE=WORK:{contact.get('website', '')}\n" if contact.get('website', '') != '' else ""
    vc_address = f"ADR;TYPE=WORK;CHARSET=UTF-8:{contact.get('street', '')};{contact.get('city', '')};{contact.get('p_code', '')};{contact.get('country', '')}\n"
    vc_end = "END:VCARD\n"

    vc_filename = f"{contact.get('last_name', '').lower()}_{contact.get('first_name', '').lower()}.vcf"
    vc_output = vc_begin + vc_version + vc_name + vc_title + vc_org + vc_phone + vc_email + vc_website + vc_address + vc_end

    vc_final = {
        "filename" : vc_filename,
        "output" : vc_output,
        "name" : contact.get('first_name', '') + contact.get('last_name', ''),
    }

    return vc_final

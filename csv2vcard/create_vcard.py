"""vCard generation for csv2vcard."""

from __future__ import annotations

import logging

from csv2vcard.models import Contact, VCardOutput, VCardVersion

logger = logging.getLogger(__name__)


def create_vcard(
    contact: dict[str, str] | Contact,
    version: VCardVersion = VCardVersion.V3_0,
) -> dict[str, str]:
    """
    Create a vCard from a contact.

    Args:
        contact: Contact data (dict or Contact object)
        version: vCard version to generate (3.0 or 4.0)

    Returns:
        Dictionary with 'filename', 'output', and 'name' keys
        (backwards compatible format)
    """
    # Normalize to Contact object
    contact_obj = Contact.from_dict(contact) if isinstance(contact, dict) else contact

    if version == VCardVersion.V4_0:
        output = _create_vcard_4(contact_obj)
    else:
        output = _create_vcard_3(contact_obj)

    # Generate safe filename (prevents path traversal)
    filename = contact_obj.get_safe_filename()
    name = f"{contact_obj.first_name} {contact_obj.last_name}".strip()

    logger.debug(f"Created vCard {version.value} for {name}")

    # Return dict for backwards compatibility
    return {
        "filename": filename,
        "output": output,
        "name": name,
    }


def create_vcard_typed(
    contact: dict[str, str] | Contact,
    version: VCardVersion = VCardVersion.V3_0,
) -> VCardOutput:
    """
    Create a vCard from a contact with typed return.

    Args:
        contact: Contact data (dict or Contact object)
        version: vCard version to generate (3.0 or 4.0)

    Returns:
        VCardOutput dataclass
    """
    result = create_vcard(contact, version)
    return VCardOutput(
        filename=result["filename"],
        output=result["output"],
        name=result["name"],
        version=version,
    )


def _create_vcard_3(contact: Contact) -> str:
    """
    Generate vCard 3.0 format (RFC 2426).

    Args:
        contact: Contact object

    Returns:
        vCard 3.0 formatted string
    """
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N;CHARSET=UTF-8:{contact.last_name};{contact.first_name};;;",
        f"FN;CHARSET=UTF-8:{contact.first_name} {contact.last_name}",
    ]

    # Optional fields - only include if non-empty
    if contact.title:
        lines.append(f"TITLE;CHARSET=UTF-8:{contact.title}")
    if contact.org:
        lines.append(f"ORG;CHARSET=UTF-8:{contact.org}")
    if contact.phone:
        lines.append(f"TEL;TYPE=WORK,VOICE:{contact.phone}")
    if contact.email:
        lines.append(f"EMAIL;TYPE=WORK:{contact.email}")
    if contact.website:
        lines.append(f"URL;TYPE=WORK:{contact.website}")

    # Address - only if at least one component is present
    if any([contact.street, contact.city, contact.p_code, contact.country]):
        # ADR format: PO Box;Extended;Street;City;Region;PostalCode;Country
        adr = (
            f"ADR;TYPE=WORK;CHARSET=UTF-8:;;{contact.street};"
            f"{contact.city};;{contact.p_code};{contact.country}"
        )
        lines.append(adr)

    lines.append("END:VCARD")
    return "\n".join(lines) + "\n"


def _create_vcard_4(contact: Contact) -> str:
    """
    Generate vCard 4.0 format (RFC 6350).

    Args:
        contact: Contact object

    Returns:
        vCard 4.0 formatted string
    """
    lines = [
        "BEGIN:VCARD",
        "VERSION:4.0",
        f"N:{contact.last_name};{contact.first_name};;;",
        f"FN:{contact.first_name} {contact.last_name}",
    ]

    # Optional fields - only include if non-empty
    # Note: CHARSET is not used in vCard 4.0 (UTF-8 is mandatory)
    if contact.title:
        lines.append(f"TITLE:{contact.title}")
    if contact.org:
        lines.append(f"ORG:{contact.org}")
    if contact.phone:
        lines.append(f"TEL;TYPE=work,voice;VALUE=uri:tel:{contact.phone}")
    if contact.email:
        lines.append(f"EMAIL;TYPE=work:{contact.email}")
    if contact.website:
        lines.append(f"URL;TYPE=work:{contact.website}")

    # Address
    if any([contact.street, contact.city, contact.p_code, contact.country]):
        adr = f"ADR;TYPE=work:;;{contact.street};{contact.city};;{contact.p_code};{contact.country}"
        lines.append(adr)

    lines.append("END:VCARD")
    return "\n".join(lines) + "\n"

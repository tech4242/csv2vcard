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
    name = contact_obj.get_formatted_name()

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


def _escape_vcard_value(value: str) -> str:
    """
    Escape special characters in vCard values.

    Args:
        value: Raw string value

    Returns:
        Escaped string safe for vCard
    """
    # Escape backslashes first, then other special chars
    value = value.replace("\\", "\\\\")
    value = value.replace(",", "\\,")
    value = value.replace(";", "\\;")
    value = value.replace("\n", "\\n")
    return value


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
    ]

    # N field: LastName;FirstName;MiddleName;Prefix;Suffix
    n_parts = [
        _escape_vcard_value(contact.last_name),
        _escape_vcard_value(contact.first_name),
        _escape_vcard_value(contact.middle_name),
        _escape_vcard_value(contact.name_prefix),
        _escape_vcard_value(contact.name_suffix),
    ]
    lines.append(f"N;CHARSET=UTF-8:{';'.join(n_parts)}")

    # FN field: Formatted name
    fn = contact.get_formatted_name()
    lines.append(f"FN;CHARSET=UTF-8:{_escape_vcard_value(fn)}")

    # Optional fields - only include if non-empty
    if contact.nickname:
        lines.append(f"NICKNAME;CHARSET=UTF-8:{_escape_vcard_value(contact.nickname)}")

    if contact.gender:
        # vCard 3.0 doesn't have GENDER, use X-GENDER extension
        lines.append(f"X-GENDER:{_escape_vcard_value(contact.gender)}")

    if contact.birthday:
        # Format: YYYYMMDD or YYYY-MM-DD
        bday = contact.birthday.replace("-", "")
        lines.append(f"BDAY:{bday}")

    if contact.anniversary:
        # vCard 3.0 uses X-ANNIVERSARY extension
        anniv = contact.anniversary.replace("-", "")
        lines.append(f"X-ANNIVERSARY:{anniv}")

    if contact.title:
        lines.append(f"TITLE;CHARSET=UTF-8:{_escape_vcard_value(contact.title)}")

    if contact.role:
        lines.append(f"ROLE;CHARSET=UTF-8:{_escape_vcard_value(contact.role)}")

    if contact.org:
        lines.append(f"ORG;CHARSET=UTF-8:{_escape_vcard_value(contact.org)}")

    # Phone numbers - backwards compatible single phone
    if contact.phone:
        lines.append(f"TEL;TYPE=WORK,VOICE:{contact.phone}")

    # Multi-type phone numbers (v0.5.0)
    if contact.phone_cell:
        lines.append(f"TEL;TYPE=CELL:{contact.phone_cell}")
    if contact.phone_home:
        lines.append(f"TEL;TYPE=HOME,VOICE:{contact.phone_home}")
    if contact.phone_work:
        lines.append(f"TEL;TYPE=WORK,VOICE:{contact.phone_work}")
    if contact.phone_fax:
        lines.append(f"TEL;TYPE=FAX:{contact.phone_fax}")

    # Email - backwards compatible single email
    if contact.email:
        lines.append(f"EMAIL;TYPE=WORK:{contact.email}")

    # Multi-type email (v0.5.0)
    if contact.email_home:
        lines.append(f"EMAIL;TYPE=HOME:{contact.email_home}")
    if contact.email_work:
        lines.append(f"EMAIL;TYPE=WORK:{contact.email_work}")

    if contact.website:
        lines.append(f"URL;TYPE=WORK:{contact.website}")

    # Address (default/work) - only if at least one component is present
    if any([contact.street, contact.city, contact.region, contact.p_code, contact.country]):
        # ADR format: PO Box;Extended;Street;City;Region;PostalCode;Country
        adr_parts = [
            "",  # PO Box
            "",  # Extended address
            _escape_vcard_value(contact.street),
            _escape_vcard_value(contact.city),
            _escape_vcard_value(contact.region),
            _escape_vcard_value(contact.p_code),
            _escape_vcard_value(contact.country),
        ]
        lines.append(f"ADR;TYPE=WORK;CHARSET=UTF-8:{';'.join(adr_parts)}")

    # Home address (v0.5.0)
    if any([contact.home_street, contact.home_city, contact.home_region,
            contact.home_p_code, contact.home_country]):
        adr_parts = [
            "",  # PO Box
            "",  # Extended address
            _escape_vcard_value(contact.home_street),
            _escape_vcard_value(contact.home_city),
            _escape_vcard_value(contact.home_region),
            _escape_vcard_value(contact.home_p_code),
            _escape_vcard_value(contact.home_country),
        ]
        lines.append(f"ADR;TYPE=HOME;CHARSET=UTF-8:{';'.join(adr_parts)}")

    # Media fields (v0.5.0)
    if contact.photo:
        lines.append(_format_media_field_v3("PHOTO", contact.photo))
    if contact.logo:
        lines.append(_format_media_field_v3("LOGO", contact.logo))

    # New vCard fields (v0.5.0)
    if contact.categories:
        lines.append(f"CATEGORIES;CHARSET=UTF-8:{_escape_vcard_value(contact.categories)}")

    if contact.geo:
        # vCard 3.0 GEO format: lat;lon
        geo = contact.geo.replace(",", ";")
        lines.append(f"GEO:{geo}")

    if contact.tz:
        lines.append(f"TZ:{_escape_vcard_value(contact.tz)}")

    if contact.key:
        lines.append(_format_key_field_v3(contact.key))

    if contact.note:
        lines.append(f"NOTE;CHARSET=UTF-8:{_escape_vcard_value(contact.note)}")

    # Add REV timestamp
    lines.append(f"REV:{Contact.generate_rev()}")

    # Add UID
    lines.append(f"UID:{contact.generate_uid()}")

    lines.append("END:VCARD")
    return "\n".join(lines) + "\n"


def _format_media_field_v3(field_name: str, value: str) -> str:
    """Format PHOTO or LOGO field for vCard 3.0."""
    if value.startswith(("http://", "https://")):
        return f"{field_name};VALUE=URI:{value}"
    else:
        # Assume base64 encoded data
        # Try to detect image type from data or default to JPEG
        if value.startswith("/9j/"):
            media_type = "JPEG"
        elif value.startswith("iVBOR"):
            media_type = "PNG"
        elif value.startswith("R0lGOD"):
            media_type = "GIF"
        else:
            media_type = "JPEG"
        return f"{field_name};ENCODING=b;TYPE={media_type}:{value}"


def _format_key_field_v3(value: str) -> str:
    """Format KEY field for vCard 3.0."""
    if value.startswith(("http://", "https://")):
        return f"KEY;VALUE=URI:{value}"
    else:
        # Assume base64 encoded key data
        return f"KEY;ENCODING=b:{value}"


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
    ]

    # N field: LastName;FirstName;MiddleName;Prefix;Suffix
    n_parts = [
        _escape_vcard_value(contact.last_name),
        _escape_vcard_value(contact.first_name),
        _escape_vcard_value(contact.middle_name),
        _escape_vcard_value(contact.name_prefix),
        _escape_vcard_value(contact.name_suffix),
    ]
    lines.append(f"N:{';'.join(n_parts)}")

    # FN field: Formatted name
    fn = contact.get_formatted_name()
    lines.append(f"FN:{_escape_vcard_value(fn)}")

    # Optional fields - only include if non-empty
    # Note: CHARSET is not used in vCard 4.0 (UTF-8 is mandatory)
    if contact.nickname:
        lines.append(f"NICKNAME:{_escape_vcard_value(contact.nickname)}")

    if contact.gender:
        # vCard 4.0 GENDER format: single letter (M/F/O/N/U) or ;text
        gender = contact.gender.upper()
        if gender in ("M", "F", "O", "N", "U"):
            lines.append(f"GENDER:{gender}")
        else:
            # Use full text after semicolon
            lines.append(f"GENDER:;{_escape_vcard_value(contact.gender)}")

    if contact.birthday:
        # vCard 4.0 format: YYYYMMDD or --MMDD
        bday = contact.birthday.replace("-", "")
        lines.append(f"BDAY:{bday}")

    if contact.anniversary:
        anniv = contact.anniversary.replace("-", "")
        lines.append(f"ANNIVERSARY:{anniv}")

    if contact.title:
        lines.append(f"TITLE:{_escape_vcard_value(contact.title)}")

    if contact.role:
        lines.append(f"ROLE:{_escape_vcard_value(contact.role)}")

    if contact.org:
        lines.append(f"ORG:{_escape_vcard_value(contact.org)}")

    # Phone numbers - backwards compatible single phone
    if contact.phone:
        lines.append(f"TEL;TYPE=work,voice;VALUE=uri:tel:{contact.phone}")

    # Multi-type phone numbers (v0.5.0)
    if contact.phone_cell:
        lines.append(f"TEL;TYPE=cell;VALUE=uri:tel:{contact.phone_cell}")
    if contact.phone_home:
        lines.append(f"TEL;TYPE=home,voice;VALUE=uri:tel:{contact.phone_home}")
    if contact.phone_work:
        lines.append(f"TEL;TYPE=work,voice;VALUE=uri:tel:{contact.phone_work}")
    if contact.phone_fax:
        lines.append(f"TEL;TYPE=fax;VALUE=uri:tel:{contact.phone_fax}")

    # Email - backwards compatible single email
    if contact.email:
        lines.append(f"EMAIL;TYPE=work:{contact.email}")

    # Multi-type email (v0.5.0)
    if contact.email_home:
        lines.append(f"EMAIL;TYPE=home:{contact.email_home}")
    if contact.email_work:
        lines.append(f"EMAIL;TYPE=work:{contact.email_work}")

    if contact.website:
        lines.append(f"URL;TYPE=work:{contact.website}")

    # Address (default/work)
    if any([contact.street, contact.city, contact.region, contact.p_code, contact.country]):
        adr_parts = [
            "",  # PO Box
            "",  # Extended address
            _escape_vcard_value(contact.street),
            _escape_vcard_value(contact.city),
            _escape_vcard_value(contact.region),
            _escape_vcard_value(contact.p_code),
            _escape_vcard_value(contact.country),
        ]
        lines.append(f"ADR;TYPE=work:{';'.join(adr_parts)}")

    # Home address (v0.5.0)
    if any([contact.home_street, contact.home_city, contact.home_region,
            contact.home_p_code, contact.home_country]):
        adr_parts = [
            "",  # PO Box
            "",  # Extended address
            _escape_vcard_value(contact.home_street),
            _escape_vcard_value(contact.home_city),
            _escape_vcard_value(contact.home_region),
            _escape_vcard_value(contact.home_p_code),
            _escape_vcard_value(contact.home_country),
        ]
        lines.append(f"ADR;TYPE=home:{';'.join(adr_parts)}")

    # Media fields (v0.5.0)
    if contact.photo:
        lines.append(_format_media_field_v4("PHOTO", contact.photo))
    if contact.logo:
        lines.append(_format_media_field_v4("LOGO", contact.logo))

    # New vCard fields (v0.5.0)
    if contact.categories:
        lines.append(f"CATEGORIES:{_escape_vcard_value(contact.categories)}")

    if contact.geo:
        # vCard 4.0 GEO format: geo:lat,lon
        lines.append(f"GEO:geo:{contact.geo}")

    if contact.tz:
        lines.append(f"TZ:{_escape_vcard_value(contact.tz)}")

    if contact.key:
        lines.append(_format_key_field_v4(contact.key))

    if contact.note:
        lines.append(f"NOTE:{_escape_vcard_value(contact.note)}")

    # Add REV timestamp
    lines.append(f"REV:{Contact.generate_rev()}")

    # Add UID
    lines.append(f"UID:urn:uuid:{contact.generate_uid()}")

    lines.append("END:VCARD")
    return "\n".join(lines) + "\n"


def _format_media_field_v4(field_name: str, value: str) -> str:
    """Format PHOTO or LOGO field for vCard 4.0."""
    if value.startswith(("http://", "https://")):
        return f"{field_name}:{value}"
    else:
        # Assume base64 encoded data
        # Try to detect media type from data or default to JPEG
        if value.startswith("/9j/"):
            media_type = "image/jpeg"
        elif value.startswith("iVBOR"):
            media_type = "image/png"
        elif value.startswith("R0lGOD"):
            media_type = "image/gif"
        else:
            media_type = "image/jpeg"
        return f"{field_name};ENCODING=b;MEDIATYPE={media_type}:{value}"


def _format_key_field_v4(value: str) -> str:
    """Format KEY field for vCard 4.0."""
    if value.startswith(("http://", "https://")):
        return f"KEY:{value}"
    else:
        # Assume base64 encoded key data (PGP or similar)
        return f"KEY;MEDIATYPE=application/pgp-keys:{value}"

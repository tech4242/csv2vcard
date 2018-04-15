import csv
import codecs

def parse_csv(csv_filename: str, csv_delimeter: str):
    """
    Simple csv parser with a ; delimiter
    """
    print("Parsing csv..")
    try:
        with codecs.open(f"{csv_filename}", "r", "utf-8-sig") as f:
            contacts = csv.reader(f, delimiter=csv_delimeter)
            header = next(contacts)  # saves header
            parsed_contacts = [dict(zip(header, row)) for row in contacts]
            return parsed_contacts
    except IOError:
        print(f"I/O error for {csv_filename}")
        return []

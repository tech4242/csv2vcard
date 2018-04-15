import os

def export_vcard(vc_final):
    """
    Exporting a vCard to /export/
    """
    try:
        with open(f"export/{vc_final['filename']}", "w") as f:
            f.write(vc_final['output'])
            f.close()
            print(f"Created vCard 3.0 for {vc_final['name']}.")
    except IOError:
        print(f"I/O error for {vc_final['filename']}")


def check_export():
    """
    Checks if export folder exists in directory
    """
    if not os.path.exists("export"):
        print("Creating /export folder...")
        os.makedirs("export")

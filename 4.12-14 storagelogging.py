from colorama import init, Fore, Back, Style
import subprocess
import json
import sys

# Initialize colorama
init(autoreset=True)

def get_storage_account_ids():
    try:
        command = ["az", "storage", "account", "list", "--query", "[].id", "-o", "json"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        storage_account_ids = json.loads(result.stdout)
        return storage_account_ids
    except subprocess.CalledProcessError as e:
        print(
            Back.RED + Fore.WHITE +
            f"Error fetching storage account IDs: {e.stderr.strip()}" +
            Style.RESET_ALL
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(
            Back.RED + Fore.WHITE +
            f"Error decoding JSON response: {e}" +
            Style.RESET_ALL
        )
        sys.exit(1)

def get_default_domain():
    try:
        command = ["az", "account", "list", "--query", "[?isDefault].tenantDefaultDomain", "-o", "json"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        default_domains = json.loads(result.stdout)
        if default_domains:
            return default_domains[0]
        else:
            raise ValueError("No default domain found in account list.")
    except subprocess.CalledProcessError as e:
        print(
            Back.RED + Fore.WHITE +
            f"Error fetching tenant default domain: {e.stderr.strip()}" +
            Style.RESET_ALL
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(
            Back.RED + Fore.WHITE +
            f"Error decoding JSON response: {e}" +
            Style.RESET_ALL
        )
        sys.exit(1)
    except ValueError as e:
        print(
            Back.RED + Fore.WHITE +
            str(e) +
            Style.RESET_ALL
        )
        sys.exit(1)

def generate_links(storage_account_ids, default_domain):
    base_url = "https://portal.azure.com/#@domain.com/resourceidfromstorage/diagnostics"
    links = [base_url.replace("domain.com", default_domain).replace("idfromstorage", storage_id) 
             for storage_id in storage_account_ids]
    return links

def main():
    storage_account_ids = get_storage_account_ids()

    if not storage_account_ids:
        print(
            Back.RED + Fore.WHITE +
            "No storage accounts found. Please ensure you have the necessary permissions." +
            Style.RESET_ALL
        )
        sys.exit(0)

    default_domain = get_default_domain()

    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for 4.12 Ensure Storage Logging is Enabled for Queue Service for 'Read', 'Write', and 'Delete' requests" +
        Style.RESET_ALL
    )
    additional_info_1 = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "4.13 Ensure Storage Logging is Enabled for Blob Service for 'Read', 'Write', and 'Delete' requests" +
        Style.RESET_ALL
    )
    additional_info_2 = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "4.14 Ensure Storage Logging is Enabled for Table Service for 'Read', 'Write', and 'Delete' requests" +
        Style.RESET_ALL
    )

    print(message)
    print(additional_info_1)
    print(additional_info_2)

    links = generate_links(storage_account_ids, default_domain)

    box_width = max(len(link) for link in links) + 4
    border = "+" + "-" * (box_width - 2) + "+"

    print(border)
    for link in links:
        print(f"| {link.ljust(box_width - 4)} |")
    print(border)

if __name__ == "__main__":
    main()

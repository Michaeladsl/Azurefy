from colorama import init, Fore, Back, Style
import subprocess
import json
import sys

# Initialize colorama
init(autoreset=True)

def get_subscription_ids():
    try:
        command = ["az", "account", "list", "--query", "[].id", "-o", "json"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        subscription_ids = json.loads(result.stdout)
        return subscription_ids
    except subprocess.CalledProcessError as e:
        print(
            Back.RED + Fore.WHITE +
            f"Error fetching subscription IDs: {e.stderr.strip()}" +
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

def generate_links(subscription_ids):
    base_url = ("https://portal.azure.com/#view/Microsoft_Azure_Security/"
                "AggregatedManageAssignmentsView.ReactView/environmentId/"
                "%2Fsubscriptions%2F{subscription_id}/setDefinitionId/"
                "%2Fproviders%2FMicrosoft.Authorization%2FpolicySetDefinitions%2F"
                "1f3afdf9-d0c9-4c3d-847f-89da613e70a8")
    links = [base_url.format(subscription_id=sub_id) for sub_id in subscription_ids]
    return links

def main():
    subscription_ids = get_subscription_ids()

    if not subscription_ids:
        print(
            Back.RED + Fore.WHITE +
            "No subscriptions found. Please ensure you are logged into Azure CLI and have the necessary permissions." +
            Style.RESET_ALL
        )
        sys.exit(0)

    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for 3.1.11 Ensure that Microsoft Cloud Security Benchmark policies are not set to 'Disabled'." +
        Style.RESET_ALL
    )
    print(message)

    links = generate_links(subscription_ids)

    box_width = max(len(link) for link in links) + 2
    border = "+" + "-" * (box_width - 1) + "+"

    print(border)
    for link in links:
        print(f"| {link.ljust(box_width - 2)} |")
    print(border)

if __name__ == "__main__":
    main()

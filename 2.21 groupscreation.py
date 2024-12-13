from colorama import init, Fore, Back, Style

init(autoreset=True)

def manual_check_message():
    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for \"2.21 Ensure that 'Users can create Microsoft 365 groups in Azure portals, API or PowerShell' is set to 'No'\"" +
        Style.RESET_ALL
    )
    print(message)

    content = [
        "https://entra.microsoft.com/#view/Microsoft_AAD_IAM/GroupsManagementMenuBlade/~/General/menuId/AllGroups"
    ]

    box_width = max(len(line) for line in content) + 4
    border = "+" + "-" * (box_width - 2) + "+"

    print(border)
    for line in content:
        print(f"| {line.ljust(box_width - 4)} |")
    print(border)

if __name__ == "__main__":
    manual_check_message()

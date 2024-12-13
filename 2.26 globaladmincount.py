from colorama import init, Fore, Back, Style

init(autoreset=True)

def manual_check_message():
    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for \"2.26 Ensure fewer than 5 users have global administrator assignment\"" +
        Style.RESET_ALL
    )
    print(message)

    content = [
        "https://portal.azure.com/#view/Microsoft_AAD_IAM/RolesManagementMenuBlade/~/AllRoles/adminUnitObjectId//resourceScope/%2F",
        "  - Search for and select Global Administrator"
    ]

    box_width = max(len(line) for line in content) + 4
    border = "+" + "-" * (box_width - 2) + "+"

    print(border)
    for line in content:
        print(f"| {line.ljust(box_width - 4)} |")
    print(border)

if __name__ == "__main__":
    manual_check_message()

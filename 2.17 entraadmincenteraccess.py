from colorama import init, Fore, Back, Style

init(autoreset=True)

def manual_check_message():
    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for \"2.17 Ensure That 'Restrict access to Microsoft Entra admin center' is Set to 'Yes'\"" +
        Style.RESET_ALL
    )
    print(message)

    content = [
        "https://portal.azure.com/#view/Microsoft_AAD_UsersAndTenants/UserManagementMenuBlade/~/UserSettings"
    ]

    box_width = max(len(line) for line in content) + 4
    border = "+" + "-" * (box_width - 2) + "+"

    print(border)
    for line in content:
        print(f"| {line.ljust(box_width - 4)} |")
    print(border)

if __name__ == "__main__":
    manual_check_message()

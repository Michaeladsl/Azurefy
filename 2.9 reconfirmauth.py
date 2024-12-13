from colorama import init, Fore, Back, Style

init(autoreset=True)

def manual_check_message():
    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for \"2.9 Ensure that 'Number of days before users are asked to reconfirm their authentication information' is not set to '0'\"" +
        Style.RESET_ALL
    )
    print(message)

    content = [
        "https://portal.azure.com/#view/Microsoft_AAD_IAM/PasswordResetMenuBlade/~/Registration"
    ]

    box_width = max(len(line) for line in content) + 4
    border = "+" + "-" * (box_width - 2) + "+"

    print(border)
    for line in content:
        print(f"| {line.ljust(box_width - 4)} |")
    print(border)

if __name__ == "__main__":
    manual_check_message()

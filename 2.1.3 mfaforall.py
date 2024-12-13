from colorama import init, Fore, Back, Style

init(autoreset=True)

def manual_check_message():
    message = (
        Back.GREEN + Fore.LIGHTRED_EX +
        "Manual check required for \"2.1.2 Ensure that 'Multi-Factor Auth Status' is 'Enabled' for all users\"" +
        Style.RESET_ALL
    )
    link = "https://entra.microsoft.com/#view/Microsoft_AAD_IAM/MultifactorAuthenticationConfig.ReactView"

    print(message)

    box_width = len(link) + 4 
    border = "+" + "-" * (box_width - 2) + "+"
    padded_link = f"| {link} |"

    print(border)
    print(padded_link)
    print(border)

if __name__ == "__main__":
    manual_check_message()

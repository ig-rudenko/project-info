def format_bytes(size: int) -> str:
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "К", 2: "М", 3: "Г", 4: "Т"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}Б"


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

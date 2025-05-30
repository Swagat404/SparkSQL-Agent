"""
ANSI color codes for console output.
"""


class ConsoleColors:
    """ANSI color codes for console output"""
    
    # Reset
    RESET = "\033[0m"
    
    # Regular colors
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"
    
    # Bold
    BOLD = "\033[1m"
    BLACK_BOLD = "\033[1;30m"
    RED_BOLD = "\033[1;31m"
    GREEN_BOLD = "\033[1;32m"
    YELLOW_BOLD = "\033[1;33m"
    BLUE_BOLD = "\033[1;34m"
    MAGENTA_BOLD = "\033[1;35m"
    CYAN_BOLD = "\033[1;36m"
    WHITE_BOLD = "\033[1;37m"
    
    # Style aliases
    ERROR = RED_BOLD
    WARNING = YELLOW_BOLD
    SUCCESS = GREEN_BOLD
    INFO = BLUE_BOLD
    HEADER = MAGENTA_BOLD
    
    # Aliases for backward compatibility
    ENDC = RESET
    OKBLUE = BLUE
    OKCYAN = CYAN
    OKGREEN = GREEN
    FAIL = RED
    BOLD = BOLD 
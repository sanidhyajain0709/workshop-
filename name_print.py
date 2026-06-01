# Print your name in a green colored box with white text
# Uses ANSI escape codes — works in any modern terminal

name = "SANIDHYA"   # 👈 Change this to your name

# ANSI color codes
GREEN_BG    = "\033[42m"   # Green background
WHITE_TEXT  = "\033[97m"   # Bright white text
BOLD        = "\033[1m"    # Bold
RESET       = "\033[0m"    # Reset all styles

padding = 4  # spaces on left and right of the name

inner    = f"  {name}  "          # name with side padding
width    = len(inner) + padding * 2
border   = " " * width

top_bottom = f"{GREEN_BG}{WHITE_TEXT}{BOLD}{border}{RESET}"
middle     = f"{GREEN_BG}{WHITE_TEXT}{BOLD}{' ' * padding}{inner}{' ' * padding}{RESET}"

print()
print(top_bottom)   # top padding row
print(middle)       # name row
print(top_bottom)   # bottom padding row
print()
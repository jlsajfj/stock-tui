import curses
import time
import random
import pyfiglet
import sys
import requests
from akashic_logging import log_info


def get_stock_price(symbol: str) -> float:
    # CNBC API endpoint
    url = f"https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={symbol}&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1"

    # Make a request to the CNBC API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Extract the relevant fields: last price and percentage change
        if (
            data["FormattedQuoteResult"]["FormattedQuote"][0]["ExtendedMktQuote"]
            is not None
        ):
            return float(
                data["FormattedQuoteResult"]["FormattedQuote"][0]["ExtendedMktQuote"][
                    "last"
                ]
            )
        return float(data["FormattedQuoteResult"]["FormattedQuote"][0]["last"])
    else:
        raise Exception(f"Failed to fetch stock data: {response.status_code}")


def main(stdscr):
    log_info("Starting the stock price tracker")
    last_price = None

    # Clear screen
    stdscr.clear()

    # Hide cursor
    curses.curs_set(0)

    # Initialize color pairs
    curses.start_color()
    curses.use_default_colors()

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

    # Stock symbol (you can change this to any symbol you want)
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "PSNY"

    # Create pyfiglet text
    figlet = pyfiglet.Figlet(font="moscow")

    while True:
        # Get the current stock price
        try:
            current_price = get_stock_price(symbol)
            log_info(f"Retrieved stock price for {symbol}: ${current_price:.2f}")
        except Exception as e:
            log_info(f"Error retrieving stock price: {str(e)}", level="ERROR")
            continue

        current_color = (1000, 1000, 1000)
        if last_price is not None and last_price != current_price:
            if current_price > last_price:
                current_color = (0, 1000, 0)
            else:
                current_color = (1000, 0, 0)

        if symbol == "PSNY" and last_price is not None:
            change_delta = ((current_price - last_price) / last_price) * 100
            if change_delta > 0:
                log_info(f"Change delta for PSNY: {change_delta:.2f}%", level="DEBUG")
            elif change_delta < 0:
                log_info(f"Change delta for PSNY: {change_delta:.2f}%", level="ERROR")
            else:
                log_info(f"Change delta for PSNY: 0.00%")

        last_price = current_price

        # Generate ASCII art for the price
        price_text = ".\n" + figlet.renderText(f"${current_price:.2f}")
        price_lines = price_text.replace("#", "█").split("\n")
        max_line_length = max(len(line) for line in price_lines)

        # Create a new window for the stock price
        price_win = curses.newwin(
            len(price_lines),
            max_line_length + 3,
            height // 2 - len(price_lines) // 2,
            width // 2 - max_line_length // 2 - 2,
        )

        for _ in range(10):
            curses.init_color(10, current_color[0], current_color[1], current_color[2])
            curses.init_pair(1, 10, -1)

            current_color = tuple(min(1000, x + 200) for x in current_color)
            # Clear the window
            stdscr.clear()
            price_win.clear()
            price_win.box()

            price_win.addstr(1, 2, symbol + ":")
            price_win.attron(curses.color_pair(1))
            # Display the ASCII art stock price
            for i, line in enumerate(price_lines[2:]):
                price_win.addstr(i + 2, 2, line)
            price_win.attroff(curses.color_pair(1))
            price_win.refresh()
            time.sleep(0.1)

        time.sleep(1)
        log_info(f"Updated display for {symbol}")


# Run the main function
curses.wrapper(main)

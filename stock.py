import curses
import time
import random
import pyfiglet
import sys
import requests
from akashic_logging import log_info
import datetime
import pytz
from collections import defaultdict
import multiprocessing
from enum import Enum

class Color(Enum):
    RED = (1000, 0, 0)
    GREEN = (0, 1000, 0)
    WHITE = (1000, 1000, 1000)

PRICES_TO_KEEP_TRACK = 20

def get_stock_price(symbol: str) -> float:
    # CNBC API endpoint
    url = f"https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={symbol}&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1"

    # Make a request to the CNBC API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Extract the relevant fields: last price and percentage change
        ny_time = datetime.datetime.now(pytz.timezone("America/New_York"))
        market_open = ny_time.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = ny_time.replace(hour=16, minute=0, second=0, microsecond=0)
        if ny_time < market_open or ny_time > market_close:
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

    # Clear screen
    stdscr.clear()

    # Hide cursor
    curses.curs_set(0)

    # Initialize color pairs
    curses.start_color()
    curses.use_default_colors()

    # Create pyfiglet text
    figlet = pyfiglet.Figlet(font="moscow")

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

    # Stock symbol (you can change this to any symbol you want)
    symbols = [s.upper() for s in sys.argv[1:]] if len(sys.argv) > 1 else ["PSNY"]

    stock_prices = defaultdict(lambda: [1])

    while True:
        multi_pricelines = [[] for _ in range(8)]
        current_colors = []
        # Get the current stock price
        for symbol in symbols:
            try:
                current_price = get_stock_price(symbol)
                stock_prices[symbol].append(current_price)
                stock_prices[symbol][1:PRICES_TO_KEEP_TRACK+1]
                log_info(f"Retrieved stock price for {symbol}: ${current_price:.2f}")
            except Exception as e:
                log_info(f"Error retrieving stock price: {str(e)}", level="ERROR")
                continue

            current_color = Color.WHITE.value
            current_price = stock_prices[symbol][-1]
            last_price = stock_prices[symbol][-2]
            if current_price > last_price:
                current_color = Color.GREEN.value
            elif current_price < last_price:
                current_color = Color.RED.value

            if symbol == "PSNY":
                change_delta = ((current_price - last_price) / last_price) * 100
                if change_delta > 0:
                    log_info(f"Change delta for PSNY: {change_delta:.2f}%", level="DEBUG")
                elif change_delta < 0:
                    log_info(f"Change delta for PSNY: {change_delta:.2f}%", level="ERROR")
            current_colors.append(current_color)

            # Generate ASCII art for the price
            price_text = ".\n" + figlet.renderText(f"${stock_prices[symbol][-1]:.2f}")
            price_lines = price_text.replace("#", "█").split("\n")[1:]
            price_lines = [f'{symbol}: '] + price_lines
            max_line_length = max(len(line) for line in price_lines)

            price_lines = [a.ljust(max_line_length + 3, " ") for a in price_lines]
            for i in range(len(price_lines)):
                multi_pricelines[i].append(price_lines[i])

        # Create a new window for the stock price
        multi_pricelines_str = ["    ".join(a) for a in  multi_pricelines]
        max_multi_pricelines =  max(map(len, multi_pricelines_str))
        price_win = curses.newwin(
            len(multi_pricelines_str) + 4,
            max_multi_pricelines + 4,
            height // 2 - len(multi_pricelines_str) // 2,
            width // 2 - max_multi_pricelines // 2 - 2,
        )

        for color_gradient_idx in range(10):
            # Clear the window
            stdscr.clear()
            price_win.clear()
            price_win.box()

            # Display the ASCII art stock price
            for i, lines in enumerate(multi_pricelines):
                start_x = 2
                for line_idx, ticker_line in enumerate(lines):
                    current_color = tuple(min(1000, x + color_gradient_idx * 200) for x in current_colors[line_idx])
                    curses.init_color(line_idx + 20, current_color[0], current_color[1], current_color[2])
                    curses.init_pair(line_idx+1, line_idx + 20, -1)
                    formatted_ticker_line = f" {ticker_line}|  " if line_idx != len(lines) -1 else ticker_line
                    price_win.addstr(i + 2, start_x, formatted_ticker_line, curses.color_pair(line_idx+1))
                    start_x += len(formatted_ticker_line)

            price_win.refresh()
            time.sleep(0.1)
        time.sleep(1)
        log_info(f"Updated display for {symbols}")


# Run the main function
curses.wrapper(main)

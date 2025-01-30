import requests
import time
import board
import displayio
import framebufferio
import rgbmatrix
import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font

url = "https://api.github.com/graphql"
USERNAME = "your_github_username"
TOKEN = "your_github_token"
current_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
one_year_ago = time.strftime(
    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 365 * 86400)
)

query = """
{
  user(login: "%s") {
    contributionsCollection(from: "%s", to: "%s") {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
""" % (USERNAME, one_year_ago, current_date)

headers = {"Authorization": f"Bearer {TOKEN}"}
response = requests.post(url, json={"query": query}, headers=headers)
data = response.json()

if "errors" in data:
    print("Errors:", data["errors"])
else:
    contributions = []
    if "data" in data and data["data"] is not None:
        calendar = data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]
        total_contributions = calendar["totalContributions"]

        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                contributions.append(day["contributionCount"])
    else:
        print("No contribution data found or an error occurred.")
        contributions = []
        total_contributions = 0

    avg_per_day = total_contributions / 365 if contributions else 0
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    for count in reversed(contributions):
        if count > 0:
            current_streak += 1
        else:
            break

    for count in contributions:
        if count > 0:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

    print(f"Total contributions: {total_contributions}")
    print(f"Avg per day: {avg_per_day:.2f}")
    print(f"Current streak: {current_streak}")
    print(f"Longest streak: {longest_streak}")

    displayio.release_displays()
    matrix = rgbmatrix.RGBMatrix(
        width=64,
        height=32,
        bit_depth=4,
        rgb_pins=[board.D6, board.D5, board.D9, board.D11, board.D10, board.D12],
        addr_pins=[board.A5, board.A4, board.A3, board.A2],
        clock_pin=board.D13,
        latch_pin=board.D0,
        output_enable_pin=board.D1,
    )

    display = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)
    main_group = displayio.Group()
    display.root_group = main_group

    # Create contribution heatmap - now using 52x7 for full year
    bitmap = displayio.Bitmap(52, 7, 5)
    palette = displayio.Palette(5)

    palette[0] = 0x000000
    palette[1] = 0x002200
    palette[2] = 0x004400
    palette[3] = 0x008800
    palette[4] = 0x00FF00

    max_contrib = max(contributions) if contributions else 1
    for i, count in enumerate(contributions[-364:]):
        x = i // 7
        y = i % 7
        level = min(4, int((count / max_contrib) * 4))
        bitmap[x, y] = level

    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    tile_grid.x = 0
    tile_grid.y = 0
    main_group.append(tile_grid)

    FONT = bitmap_font.load_font("5x5FontMonospaced-5.bdf")

    stats_labels = [
        f"TC: {total_contributions}",
        f"Avg: {avg_per_day:.1f}",
        f"CS: {current_streak}",
        f"LS: {longest_streak}",
    ]
    for i, label_text in enumerate(stats_labels):
        line = adafruit_display_text.label.Label(
            FONT,
            text=label_text,
            color=0xFFFFFF,
        )
        line.x = 0
        line.y = 11 + i * 6
        main_group.append(line)
    while True:
        time.sleep(300)

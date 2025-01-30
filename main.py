import requests
import time
import board
import displayio
import framebufferio
import rgbmatrix
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

USERNAME = "your_github_username"
TOKEN = "your_github_token"
url = "https://api.github.com/graphql"

query = f"""
{{
  user(login: "{USERNAME}") {{
    contributionsCollection {{
      contributionCalendar {{
        totalContributions
        weeks {{
          contributionDays {{
            date
            contributionCount
          }}
        }}
      }}
    }}
  }}
}}
"""

headers = {"Authorization": f"Bearer {TOKEN}"}
response = requests.post(url, json={"query": query}, headers=headers)
data = response.json()

if "errors" in data:
    print("Errors:", data["errors"])
    exit(1)

contributions = []
if data.get("data"):
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total_contributions = calendar["totalContributions"]

    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            contributions.append(day["contributionCount"])
else:
    print("No data available.")
    exit(1)


if len(contributions) < 365:
    contributions = [0] * (365 - len(contributions)) + contributions

avg_per_day = total_contributions / 365
current_streak = longest_streak = temp_streak = 0


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


bitmap = displayio.Bitmap(53, 7, 5)
palette = displayio.Palette(5)


palette[0] = 0x000000
palette[1] = 0x002200
palette[2] = 0x004400
palette[3] = 0x008800
palette[4] = 0x00FF00

max_contrib = max(contributions) if contributions else 1

start_index = len(contributions) % 7
for i, count in enumerate(contributions):
    x = (i + start_index) // 7
    y = (i + start_index) % 7
    level = min(4, int((count / max_contrib) * 4)) if max_contrib > 0 else 0
    bitmap[x, y] = level


tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
main_group.append(tile_grid)


FONT = bitmap_font.load_font("5x5FontMonospaced-5.bdf")
colors = [0xFF5733, 0x33FF57, 0x3357FF, 0xFFD700]

stats_labels = [
    f"TC: {total_contributions}",
    f"Avg: {avg_per_day:.1f}",
    f"CS: {current_streak}",
    f"LS: {longest_streak}",
]

for i, label_text in enumerate(stats_labels):
    line = Label(
        FONT,
        text=label_text,
        color=colors[i % len(colors)],
    )
    line.x = 0
    line.y = 11 + i * 6
    main_group.append(line)

while True:
    time.sleep(300)

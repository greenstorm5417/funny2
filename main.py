import asyncio
import requests
import keyboard
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from time import sleep
import aiohttp

# Service presets to cycle through (improved descriptions)
service_presets = [
    ("Nave", "Prelude (Preparation before the service begins)"),
    ("Mid-Nave", "After Priests Walk In (Pause after the priests walk in)"),
    ("Reader", "1st Reader (First scripture reading)"),
    ("Mid-Nave", "After 1st Reader (Pause after the first reading)"),
    ("Reader", "2nd Reader (Second scripture reading)"),
    ("Mid-Nave", "After 2nd Reader (Pause after the second reading)"),
    ("Gospel", "Gospel (Reading from the Gospels)"),
    ("Mid-Nave", "Transition to Children's Chapel (Move children to the chapel)"),
    ("Child Chapel", "Children's Chapel (Focus on the children’s segment)"),
    ("Sermon", "Sermon (Main teaching or homily)"),
    ("Mid-Nave", "Confession of Sin (Congregation confesses sins)"),
    ("Altar", "Communion (Distribution of communion elements)"),
    ("Mid-Nave", "Rest of Service (Final prayers, announcements, dismissal)")
]

# Step 1: Get the session token using aiohttp
async def get_session():
    url = "http://192.168.0.5/api/config/session"
    payload = {
        "username": "admin",
        "password": "admin"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 201:  # 201 is for created
                    cookies = response.cookies
                    session_cookie = cookies.get('session')

                    if session_cookie:
                        return session_cookie.value
                    else:
                        return "No session cookie was set."
                else:
                    return f"Failed to get a valid response. Status Code: {response.status}"

        except aiohttp.ClientError as e:
            return f"An error occurred: {e}"

# Step 2: Function to send a request for a specific preset using requests
def send_preset(session_token, preset_id):
    url = "http://192.168.0.5/api/config/video/input/0/device/preset"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Cookie": f"session={session_token}",
        "DNT": "1",
        "Host": "192.168.0.5",
        "Origin": "http://192.168.0.5",
        "Referer": "http://192.168.0.5/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "X-Requested-With": "XMLHttpRequest"
    }
    payload = {
        "recall": {
            "id": preset_id
        }
    }

    # Make the POST request with requests
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 204:
        return "Preset successfully sent"
    else:
        return f"Failed to send preset. Status: {response.status_code}, Response: {response.text}"

# Function to create a layout showing previous, current, and next presets
def create_preset_layout(current_idx):
    layout = Layout()

    # Handle when there is no current preset selected (initial state)
    if current_idx == -1:
        return Panel("[bold red]No preset selected. Press space to begin.[/bold red]", title="No Active Preset", border_style="dim")
    
    # Previous preset (if it exists)
    prev_preset = service_presets[current_idx - 1] if current_idx > 0 else ("None", "")
    layout.split_row(
        Panel(f"Previous: {prev_preset[0]}\nAction: {prev_preset[1]}", title="Previous Preset", border_style="dim"),
        Panel(f"Current: {service_presets[current_idx][0]}\nAction: {service_presets[current_idx][1]}", title="Current Preset", border_style="bold green"),
        Panel(f"Next: {service_presets[current_idx + 1][0]}\nAction: {service_presets[current_idx + 1][1]}", title="Next Preset", border_style="dim") if current_idx < len(service_presets) - 1 else Panel("No next preset", title="Next Preset", border_style="dim")
    )

    return layout

# Function to display the control bar at the bottom
def create_control_bar():
    return Panel("[bold cyan]Controls:[/bold cyan] [green]Space[/green] - Next | [green]B[/green] - Previous", title="Control Bar", height=3)

# Main function to handle cycling through presets using keyboard inputs
async def cycle_presets(session_token):
    console = Console()
    current_idx = -1  # Start with no active preset

    # Real-time display using Rich
    with Live(console=console, refresh_per_second=10) as live:
        while True:
            layout = Layout()
            layout.split_column(
                create_preset_layout(current_idx),  # Show the preset layout
                create_control_bar()  # Add the control bar at the bottom
            )
            live.update(layout)

            if keyboard.is_pressed("space"):  # Move forward
                current_idx = min(current_idx + 1, len(service_presets) - 1)  # Increment but stop at last preset
                live.update(create_preset_layout(current_idx))  # Update immediately
                send_preset(session_token, current_idx)  # Send the request synchronously
                sleep(0.5)  # Avoid multiple fast presses

            elif keyboard.is_pressed("b"):  # Move backward
                if current_idx > 0:
                    current_idx -= 1
                live.update(create_preset_layout(current_idx))  # Update immediately
                send_preset(session_token, current_idx)  # Send the request synchronously
                sleep(0.5)  # Avoid multiple fast presses

            if current_idx == len(service_presets) - 1:  # Exit after the last preset
                console.print("[bold green]End of service presets. Exiting...[/bold green]")
                break

# Main async function to get session and start cycling presets
async def main():
    console = Console()

    # Get the session token
    console.print("[bold cyan]Getting session token...[/bold cyan]")
    session_token = await get_session()

    if "Failed" in session_token:
        console.print(f"[bold red]Error: {session_token}[/bold red]")
        return

    console.print(f"[bold green]Session token acquired: {session_token}[/bold green]")

    # Start cycling through presets and sending them
    await cycle_presets(session_token)

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())

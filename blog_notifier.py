
import requests
from bs4 import BeautifulSoup
import discord
import asyncio
import os
import time

# Configuration
BLOG_URL = os.environ.get("BLOG_URL")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID"))
CHECK_INTERVAL = 300  # seconds (5 minutes)
STORAGE_FILE = "last_post.txt"

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

    async def setup_hook(self) -> None:
        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def my_background_task(self):
        await self.wait_until_ready()
        while not self.is_closed():
            await check_blog_and_notify()
            await asyncio.sleep(CHECK_INTERVAL)

async def check_blog_and_notify():
    try:
        response = requests.get(BLOG_URL)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the latest post title and URL (Adapt this to your blog's HTML structure)
        # Example: Assuming the blog uses <article> tags with a link inside
        latest_post = soup.find("article")
        if latest_post:
            link = latest_post.find("a")
            if link:
                post_title = link.text.strip()
                post_url = link["href"]

                # Check if this post is new
                last_post = load_last_post()
                if post_url != last_post.get("url"):
                    # Send Discord notification
                    await send_discord_notification(post_title, post_url)

                    # Save the new post information
                    save_last_post(post_title, post_url)
                else:
                    print("No new posts.")
            else:
                print("Could not find link in latest post.")
        else:
            print("Could not find latest post.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching blog: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def send_discord_notification(title, url):
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="New Blog Post", description=title, url=url)
        await channel.send(embed=embed)
        print(f"Notification sent to Discord: {title} - {url}")
    else:
        print(f"Could not find channel with ID {DISCORD_CHANNEL_ID}")

def load_last_post():
    try:
        with open(STORAGE_FILE, "r") as f:
            title = f.readline().strip()
            url = f.readline().strip()
            return {"title": title, "url": url}
    except FileNotFoundError:
        return {"title": "", "url": ""}

def save_last_post(title, url):
    with open(STORAGE_FILE, "w") as f:
        f.write(title + "\\n")
        f.write(url + "\\n")

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

async def main():
    await client.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

# ---------------------------------------------------------------
# 🔸 Shashank YT-API Project
# 🔹 Developed & Maintained by: Shashank Shukla (https://github.com/itzshukla)
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by ItzShukla
# ---------------------------------------------------------------

import asyncio
import os
import re
from typing import Union
import aiohttp
from youtubesearchpython.__future__ import VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from SHUKLAMUSIC import LOGGER
from ..utils.formatters import time_to_seconds

# API URL
YOUR_API_URL = None
FALLBACK_API_URL = "https://shrutibots.site"

# Load API URL from pastebin or fallback
async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("ShuklaMusic.platforms.Youtube.py")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pastebin.com/raw/rLsBhAQa", timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    YOUR_API_URL = (await response.text()).strip()
                    logger.info("API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
                    logger.info("Using fallback API URL")
    except Exception:
        YOUR_API_URL = FALLBACK_API_URL
        logger.info("Using fallback API URL")

# Ensure API URL is loaded
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass

# Helper to download file from API
async def download_file(video_id: str, type_: str) -> str:
    global YOUR_API_URL
    logger = LOGGER("ShuklaMusic.platforms.Youtube.py")

    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            YOUR_API_URL = FALLBACK_API_URL

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp3" if type_ == "audio" else "mp4"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

    if os.path.exists(file_path):
        logger.info(f"[LOCAL] File exists: {file_path}")
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{YOUR_API_URL}/download",
                params={"url": video_id, "type": type_},
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status != 200:
                    logger.error(f"API returned status {response.status}")
                    return None
                data = await response.json()
                stream_url = data.get("stream_url")
                if not stream_url:
                    logger.error("No stream_url in API response")
                    return None

                async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=600)) as f:
                    with open(file_path, "wb") as out:
                        async for chunk in f.content.iter_chunked(16384):
                            out.write(chunk)
        logger.info(f"[DOWNLOADED] {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Download failed for {video_id}: {e}")
        return None

# Specific download functions
async def download_song(link: str) -> str:
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    return await download_file(video_id, "audio")

async def download_video(link: str) -> str:
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    return await download_file(video_id, "video")

# Helper shell command
async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

# YouTube API wrapper
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            if downloaded_file:
                return downloaded_file, True
            else:
                return None, False
        except Exception as e:
            logger = LOGGER("ShuklaMusic.platforms.Youtube.py")
            logger.error(f"Download failed: {e}")
            return None, False

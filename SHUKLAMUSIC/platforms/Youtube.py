# ---------------------------------------------------------------
# 🔸 EchoWave Music Bot - YouTube API Integration
# 🔹 Powered by: EchoWave Music Bot API (https://ytapi--pixelvoyager43.replit.app)
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love for EchoWave Music Bot
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

# EchoWave API Configuration
ECHOWAVE_API_URL = "https://ytapi--pixelvoyager43.replit.app/api/musicbot"
ECHOWAVE_API_KEY = "ytdl_u-ifSkuYaQ3DLyTZwdRHY21iE9TvLsE__0l1qNDqTAY"
ECHOWAVE_HEADERS = {"Authorization": f"Bearer {ECHOWAVE_API_KEY}"}

# Fallback API (if needed)
FALLBACK_API_URL = "https://shrutibots.site"

logger = LOGGER("EchoWave.platforms.Youtube.py")

# Test EchoWave API connection
async def test_echowave_api():
    """Test if EchoWave API is accessible"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{ECHOWAVE_API_URL}/status",
                headers=ECHOWAVE_HEADERS,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ EchoWave API connected: {data.get('status', 'online')}")
                    return True
                else:
                    logger.error(f"❌ EchoWave API returned status {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ EchoWave API connection failed: {e}")
        return False

# Initialize API connection
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(test_echowave_api())
    else:
        loop.run_until_complete(test_echowave_api())
except RuntimeError:
    pass

# Helper to download file using EchoWave API
async def download_file_echowave(video_id: str, type_: str) -> str:
    """Download file using EchoWave Music Bot API"""
    logger.info(f"🎵 EchoWave API: Downloading {type_} for {video_id}")
    
    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    ext = "mp3" if type_ == "audio" else "mp4"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
    
    # Check if file already exists
    if os.path.exists(file_path):
        logger.info(f"[LOCAL] File exists: {file_path}")
        return file_path
    
    try:
        async with aiohttp.ClientSession() as session:
            # Use EchoWave API download endpoint
            download_url = f"{ECHOWAVE_API_URL}/download"
            params = {
                "video_id": video_id,
                "quality": "medium",
                "format": "mp3" if type_ == "audio" else "mp4"
            }
            
            logger.info(f"🔍 EchoWave API: Requesting download for {video_id}")
            
            async with session.post(
                download_url,
                params=params,
                headers=ECHOWAVE_HEADERS,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status != 200:
                    logger.error(f"❌ EchoWave API returned status {response.status}")
                    return None
                
                data = await response.json()
                
                if not data.get("success"):
                    logger.error("❌ EchoWave API: Download failed")
                    return None
                
                download_link = data.get("download_url")
                if not download_link:
                    logger.error("❌ EchoWave API: No download URL in response")
                    return None
                
                logger.info(f"✅ EchoWave API: Got download URL")
                
                # Download the file from the provided URL
                async with session.get(
                    download_link,
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as file_response:
                    
                    if file_response.status == 200:
                        with open(file_path, "wb") as out:
                            async for chunk in file_response.content.iter_chunked(16384):
                                out.write(chunk)
                        
                        logger.info(f"✅ [DOWNLOADED] {file_path}")
                        return file_path
                    else:
                        logger.error(f"❌ Failed to download file: {file_response.status}")
                        return None
                        
    except Exception as e:
        logger.error(f"❌ EchoWave API download failed for {video_id}: {e}")
        return None

# Fallback download function (original API)
async def download_file_fallback(video_id: str, type_: str) -> str:
    """Fallback download using original API"""
    logger.info(f"🔄 Fallback API: Downloading {type_} for {video_id}")
    
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
                f"{FALLBACK_API_URL}/download",
                params={"url": video_id, "type": type_},
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status != 200:
                    logger.error(f"Fallback API returned status {response.status}")
                    return None
                
                data = await response.json()
                stream_url = data.get("stream_url")
                
                if not stream_url:
                    logger.error("No stream_url in fallback API response")
                    return None
                
                async with session.get(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as f:
                    with open(file_path, "wb") as out:
                        async for chunk in f.content.iter_chunked(16384):
                            out.write(chunk)
                
                logger.info(f"[DOWNLOADED] {file_path}")
                return file_path
                
    except Exception as e:
        logger.error(f"Fallback download failed for {video_id}: {e}")
        return None

# Main download function with EchoWave API + Fallback
async def download_file(video_id: str, type_: str) -> str:
    """Download file using EchoWave API with fallback"""
    
    # Try EchoWave API first
    result = await download_file_echowave(video_id, type_)
    if result:
        return result
    
    # Fallback to original API
    logger.info("🔄 Trying fallback API...")
    return await download_file_fallback(video_id, type_)

# Specific download functions
async def download_song(link: str) -> str:
    """Download audio using EchoWave API"""
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    return await download_file(video_id, "audio")

async def download_video(link: str) -> str:
    """Download video using EchoWave API"""
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

# Enhanced YouTube API wrapper with EchoWave integration
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        logger.info("🎵 EchoWave YouTube API initialized")

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

    async def search_echowave(self, query: str, limit: int = 1):
        """Search using EchoWave API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ECHOWAVE_API_URL}/search",
                    params={"q": query, "limit": limit},
                    headers=ECHOWAVE_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        if results:
                            logger.info(f"✅ EchoWave API: Found {len(results)} results for '{query}'")
                            return results
                    else:
                        logger.error(f"❌ EchoWave search failed: {response.status}")
        except Exception as e:
            logger.error(f"❌ EchoWave search error: {e}")
        
        return []

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        # Try EchoWave API first for better results
        video_id = link.split('v=')[-1] if 'v=' in link else link
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ECHOWAVE_API_URL}/info/{video_id}",
                    headers=ECHOWAVE_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        title = data.get("title", "Unknown")
                        duration = data.get("duration", "0:00")
                        thumbnail = data.get("thumbnail", "")
                        
                        # Convert duration to seconds
                        duration_sec = int(time_to_seconds(duration)) if duration else 0
                        
                        logger.info(f"✅ EchoWave API: Got details for {title}")
                        return title, duration, duration_sec, thumbnail, video_id
        except Exception as e:
            logger.error(f"❌ EchoWave details error: {e}")
        
        # Fallback to original method
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
            logger.info(f"🎵 EchoWave: Starting download for {link}")
            
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            
            if downloaded_file:
                logger.info(f"✅ EchoWave: Download successful - {downloaded_file}")
                return downloaded_file, True
            else:
                logger.error("❌ EchoWave: Download failed")
                return None, False
                
        except Exception as e:
            logger.error(f"❌ EchoWave download error: {e}")
            return None, False

# Initialize the API
logger.info("🎵 EchoWave Music Bot API - YouTube Integration Ready!")
logger.info(f"🔗 API Endpoint: {ECHOWAVE_API_URL}")
logger.info(f"🔑 API Key: {ECHOWAVE_API_KEY[:20]}...")

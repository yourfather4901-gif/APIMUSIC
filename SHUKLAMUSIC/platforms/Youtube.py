# ---------------------------------------------------------------
# 🔸 EchoWave Music Bot - YouTube API Integration (Fixed Version)
# 🔹 Powered by: EchoWave Music Bot API (https://ytapi--pixelvoyager43.replit.app)
# 📅 Copyright © 2025 – All Rights Reserved
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

# Fallback API
FALLBACK_API_URL = "https://shrutibots.site"

logger = LOGGER("EchoWave.platforms.Youtube.py")

# Helper to extract proper video ID
def extract_video_id(url_or_id: str) -> str:
    """Extract proper YouTube video ID from URL or return ID if already clean"""
    if "youtube.com/watch?v=" in url_or_id:
        return url_or_id.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url_or_id:
        return url_or_id.split("youtu.be/")[1].split("?")[0]
    elif len(url_or_id) == 11 and not "/" in url_or_id:
        return url_or_id  # Already a video ID
    else:
        # Try to extract from any URL format
        pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})'
        match = re.search(pattern, url_or_id)
        return match.group(1) if match else url_or_id

# Setup API keys on Replit (call this once)
async def setup_echowave_keys():
    """Setup API keys on Replit deployment"""
    try:
        async with aiohttp.ClientSession() as session:
            # Generate default keys via admin endpoint
            async with session.get(
                "https://ytapi--pixelvoyager43.replit.app/api/admin/generate-default-keys",
                params={"admin_password": "admin123"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    logger.info("✅ EchoWave API keys setup successful")
                    return True
                else:
                    logger.error(f"❌ Failed to setup keys: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Key setup error: {e}")
        return False

# Test EchoWave API and setup keys if needed
async def test_and_setup_echowave_api():
    """Test API and setup keys if needed"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test authentication
            async with session.get(
                f"{ECHOWAVE_API_URL}/search",
                params={"q": "test", "limit": 1},
                headers=ECHOWAVE_HEADERS,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info("✅ EchoWave API authentication working")
                    return True
                elif response.status == 401:
                    logger.info("🔧 Setting up EchoWave API keys...")
                    return await setup_echowave_keys()
                else:
                    logger.error(f"❌ EchoWave API error: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ EchoWave API test failed: {e}")
        return False

# Initialize API
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(test_and_setup_echowave_api())
    else:
        loop.run_until_complete(test_and_setup_echowave_api())
except RuntimeError:
    pass

# Download using EchoWave API (working version)
async def download_file_echowave(video_id: str, type_: str) -> str:
    """Download file using EchoWave API - Working Version"""
    clean_video_id = extract_video_id(video_id)
    logger.info(f"🎵 EchoWave: Downloading {type_} for {clean_video_id}")
    
    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    ext = "mp3" if type_ == "audio" else "mp4"
    file_path = os.path.join(DOWNLOAD_DIR, f"{clean_video_id}.{ext}")
    
    # Check if file exists
    if os.path.exists(file_path):
        logger.info(f"[LOCAL] File exists: {file_path}")
        return file_path
    
    try:
        async with aiohttp.ClientSession() as session:
            # First, ensure keys are setup
            await setup_echowave_keys()
            
            # Wait a moment for keys to be active
            await asyncio.sleep(1)
            
            # Try download with retry
            for attempt in range(3):
                logger.info(f"🔄 EchoWave download attempt {attempt + 1}/3")
                
                try:
                    async with session.post(
                        f"{ECHOWAVE_API_URL}/download",
                        params={"video_id": clean_video_id, "quality": "medium"},
                        headers=ECHOWAVE_HEADERS,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as response:
                        
                        logger.info(f"📡 Response status: {response.status}")
                        
                        if response.status == 401:
                            logger.info("🔧 Auth failed, setting up keys again...")
                            await setup_echowave_keys()
                            await asyncio.sleep(2)
                            continue
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get("success") and data.get("download_url"):
                                download_url = data["download_url"]
                                logger.info(f"✅ Got download URL: {download_url[:50]}...")
                                
                                # Download the file
                                async with session.get(download_url, timeout=aiohttp.ClientTimeout(total=600)) as file_response:
                                    if file_response.status == 200:
                                        with open(file_path, "wb") as out:
                                            async for chunk in file_response.content.iter_chunked(16384):
                                                out.write(chunk)
                                        
                                        logger.info(f"✅ Downloaded: {file_path}")
                                        return file_path
                                    else:
                                        logger.error(f"❌ File download failed: {file_response.status}")
                            else:
                                logger.error(f"❌ Invalid response: {data}")
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ API error {response.status}: {error_text}")
                
                except Exception as e:
                    logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2)
                    continue
            
            logger.error("❌ All EchoWave attempts failed")
            return None
            
    except Exception as e:
        logger.error(f"❌ EchoWave download error: {e}")
        return None

# Fallback download (original method)
async def download_file_fallback(video_id: str, type_: str) -> str:
    """Fallback download using original API"""
    logger.info(f"🔄 Fallback: Downloading {type_} for {video_id}")
    
    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    ext = "mp3" if type_ == "audio" else "mp4"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
    
    if os.path.exists(file_path):
        return file_path
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{FALLBACK_API_URL}/download",
                params={"url": video_id, "type": type_},
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    stream_url = data.get("stream_url")
                    
                    if stream_url:
                        async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=600)) as f:
                            with open(file_path, "wb") as out:
                                async for chunk in f.content.iter_chunked(16384):
                                    out.write(chunk)
                        
                        logger.info(f"✅ Fallback downloaded: {file_path}")
                        return file_path
                
                logger.error(f"❌ Fallback failed: {response.status}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Fallback error: {e}")
        return None

# Main download function
async def download_file(video_id: str, type_: str) -> str:
    """Download with EchoWave + fallback"""
    
    # Try EchoWave first
    result = await download_file_echowave(video_id, type_)
    if result:
        return result
    
    # Try fallback
    logger.info("🔄 Trying fallback API...")
    return await download_file_fallback(video_id, type_)

# Specific download functions
async def download_song(link: str) -> str:
    """Download audio"""
    video_id = extract_video_id(link)
    logger.info(f"🎵 Downloading song: {video_id}")
    return await download_file(video_id, "audio")

async def download_video(link: str) -> str:
    """Download video"""
    video_id = extract_video_id(link)
    logger.info(f"📹 Downloading video: {video_id}")
    return await download_file(video_id, "video")

# Shell command helper
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

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        # Use standard YouTube search for details (more reliable)
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
                logger.info(f"✅ EchoWave: Download successful")
                return downloaded_file, True
            else:
                logger.error("❌ EchoWave: Download failed")
                return None, False
                
        except Exception as e:
            logger.error(f"❌ EchoWave download error: {e}")
            return None, False

logger.info("🎵 EchoWave Music Bot API - Fixed Version Ready!")
logger.info(f"🔗 API: {ECHOWAVE_API_URL}")
logger.info(f"🔑 Key: {ECHOWAVE_API_KEY[:20]}...")

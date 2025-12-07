import time
import asyncio
from pyrogram import filters
from pyrogram.errors import ChannelInvalid
from pyrogram.enums import ChatType, ChatMembersFilter
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from SHUKLAMUSIC import app
from SHUKLAMUSIC.misc import _boot_
from SHUKLAMUSIC.plugins.sudo.sudoers import sudoers_list
from SHUKLAMUSIC.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
    connect_to_chat,
)
from SHUKLAMUSIC.utils.decorators.language import LanguageStart
from SHUKLAMUSIC.utils.formatters import get_readable_time
from SHUKLAMUSIC.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string


# ---- Helper utilities ---------------------------------------------------
def _ensure_markup(obj):
    """
    Accept either InlineKeyboardMarkup or a list-of-rows and return InlineKeyboardMarkup.
    Also sanitize any InlineKeyboardButton that contains user_id to avoid PeerIdInvalid errors.
    If config.OWNER_USERNAME is set, convert user_id buttons to owner URL buttons.
    Otherwise replace user_id with a harmless callback_data to prevent failure.
    """
    if isinstance(obj, InlineKeyboardMarkup):
        rows = obj.inline_keyboard
    else:
        # assume it's a list of rows like [[btn, btn], [btn]]
        rows = obj

    new_rows = []
    for row in rows:
        new_row = []
        for b in row:
            # If the item is already an InlineKeyboardButton instance, inspect it.
            if isinstance(b, InlineKeyboardButton):
                # If it has a user_id, convert safely
                user_id = getattr(b, "user_id", None)
                if user_id:
                    # Prefer converting to owner username link if available
                    owner_un = getattr(config, "OWNER_USERNAME", None)
                    if owner_un:
                        new_btn = InlineKeyboardButton(text=b.text or "Owner", url=f"https://t.me/{owner_un}")
                    else:
                        # fallback: convert to a noop callback to avoid resolving peer
                        new_btn = InlineKeyboardButton(text=b.text or "Info", callback_data="noop")
                else:
                    # keep button as-is but ensure only supported args are used
                    # recreate button preserving url / callback_data / switch_inline_query etc.
                    if getattr(b, "url", None):
                        new_btn = InlineKeyboardButton(text=b.text, url=b.url)
                    elif getattr(b, "callback_data", None):
                        new_btn = InlineKeyboardButton(text=b.text, callback_data=b.callback_data)
                    elif getattr(b, "switch_inline_query", None):
                        new_btn = InlineKeyboardButton(text=b.text, switch_inline_query=b.switch_inline_query)
                    elif getattr(b, "switch_inline_query_current_chat", None):
                        new_btn = InlineKeyboardButton(
                            text=b.text, switch_inline_query_current_chat=b.switch_inline_query_current_chat
                        )
                    else:
                        # last resort: keep text as a noop callback
                        new_btn = InlineKeyboardButton(text=b.text or "∘", callback_data="noop")
            else:
                # If the item is a dict-like or something else, try to build a button
                try:
                    text = b.get("text")
                    if "url" in b:
                        new_btn = InlineKeyboardButton(text=text, url=b.get("url"))
                    elif "callback_data" in b:
                        new_btn = InlineKeyboardButton(text=text, callback_data=b.get("callback_data"))
                    else:
                        new_btn = InlineKeyboardButton(text=text or "∘", callback_data="noop")
                except Exception:
                    # very defensive fallback
                    new_btn = InlineKeyboardButton(text="∘", callback_data="noop")
            new_row.append(new_btn)
        new_rows.append(new_row)

    return InlineKeyboardMarkup(new_rows)


# ---- /start in private -------------------------------------------
@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    # handle "/start <payload>"
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        # del playlist (guarded in case function not present)
        if name.startswith("del"):
            del_fn = globals().get("del_plist_msg")
            if callable(del_fn):
                try:
                    return await del_fn(client=client, message=message, _=_)
                except Exception:
                    # if it fails just continue (do not crash)
                    pass

        # help payload
        if name.startswith("help"):
            keyboard = help_pannel(_)
            keyboard = _ensure_markup(keyboard)
            return await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )

        # connect_ payload (connect PM to group)
        if name.startswith("connect_"):
            chat_id = name[8:]
            try:
                title = (await app.get_chat(chat_id)).title
            except ChannelInvalid:
                return await message.reply_text(
                    f"ʟᴏᴏʟ ʟɪᴋᴇ ɪ ᴀᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴏғ ᴛʜᴇ ᴄʜᴀᴛ ɪᴅ {chat_id}"
                )

            admin_ids = [
                member.user.id
                async for member in app.get_chat_members(
                    chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                )
            ]
            if message.from_user.id not in admin_ids:
                return await message.reply_text(
                    f"sᴏʀʀʏ sɪʀ ʙᴜᴛ ɪ ᴛʜɪɴᴋ ᴛʜᴀᴛ ʏᴏᴜ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴏғ {title}"
                )

            a = await connect_to_chat(message.from_user.id, chat_id)
            if a:
                return await message.reply_text(f"ʏᴏᴜ ᴀʀᴇ ɴᴏᴡ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ {title}")
            else:
                return await message.reply_text(a)

        # sudo list payload
        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} checked <b>SudoList</b>.\n\n<b>User ID :</b> <code>{message.from_user.id}</code>\n<b>Username :</b> @{message.from_user.username}",
                )
            return

        # info payload (youtube info)
        if name.startswith("inf"):
            m = await message.reply_text("🔎")
            query = str(name).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]

            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                    ],
                ]
            )
            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched_text,
                reply_markup=_ensure_markup(key),
            )
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} viewed <b>Track Info</b>.\n\n<b>User ID :</b> <code>{message.from_user.id}</code>\n<b>Username :</b> @{message.from_user.username}",
                )

         # default /start (no payload)
    else:
        out = private_panel(_)
        await message.reply_video(
            video=config.START_IMG_URL,  # <-- this must be a video URL
            caption=_["start_2"].format(message.from_user.mention, app.mention),
            reply_markup=_ensure_markup(out),
        )
        if await is_on_off(2):
            await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"{message.from_user.mention} started the bot.\n\n"
                     f"<b>User ID :</b> <code>{message.from_user.id}</code>\n"
                     f"<b>Username :</b> @{message.from_user.username}",
            )

        


# ---- /start in groups ---------------------------------------------------
@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    await message.reply_photo(
        photo=config.START_IMG_URL,
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=_ensure_markup(out),
    )
    return await add_served_chat(message.chat.id)


# ---- welcome new members ------------------------------------------------
@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass

            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                await message.reply_photo(
                    config.START_IMG_URL,
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=_ensure_markup(out),
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)


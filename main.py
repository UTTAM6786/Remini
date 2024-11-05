import os
import logging
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.errors import SessionRevoked  # Only importing SessionRevoked
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto
from config import Config
from private_buttons import create_font_buttons, POSITION_SIZE_BUTTONS, GLOW_COLOR_BUTTONS  # Import buttons
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pyrogram Bot Setup
def create_app():
    return Client(
        "logo_creator_bot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        workers=2  # Set number of workers to handle requests faster
    )

# Font options (fonts stored here)
FONT_OPTIONS = [
    {"name": "FIGHTBACK", "path": "fonts/FIGHTBACK.ttf"},
    {"name": "Arial", "path": "fonts/Lobster-Regular.ttf"},
    {"name": "Times New Roman", "path": "fonts/OpenSans-Regular.ttf"},
    {"name": "Courier", "path": "fonts/Pacifico-Regular.ttf"},
    {"name": "Verdana", "path": "fonts/Roboto-Regular.ttf"},
]

# Function to dynamically adjust font size
def get_dynamic_font(image, text, max_width, max_height, font_path=None):
    draw = ImageDraw.Draw(image)
    
    font_size = 100
    while font_size > 10:
        font = ImageFont.truetype(font_path or "fonts/FIGHTBACK.ttf", font_size)
        text_width, text_height = draw.textsize(text, font=font)
        
        if text_width <= max_width and text_height <= max_height:
            return font, text_width, text_height
        
        font_size -= 5

    return font, text_width, text_height

# Function to add 3D text effect with shadow and glow
def add_3d_text(draw, position, text, font, glow_color, text_color, shadow_offset=(5, 5), glow_strength=5):
    x, y = position
    
    # Shadow: Draw the shadow slightly offset from the original position
    shadow_x = x + shadow_offset[0]
    shadow_y = y + shadow_offset[1]
    
    # Draw the shadow in a darker shade
    draw.text((shadow_x, shadow_y), text, font=font, fill="black")

    # Glow effect around the main text (optional, for more depth)
    for offset in range(1, glow_strength + 1):
        draw.text((x - offset, y - offset), text, font=font, fill=glow_color)
        draw.text((x + offset, y - offset), text, font=font, fill=glow_color)
        draw.text((x - offset, y + offset), text, font=font, fill=glow_color)
        draw.text((x + offset, y + offset), text, font=font, fill=glow_color)

    # Main text: Draw the main text on top of the shadow and glow
    draw.text((x, y), text, font=font, fill=text_color)

# Function to add text to the image
async def add_text_to_image(photo_path, text, output_path, x_offset=0, y_offset=0, size_multiplier=1, glow_color="red", font_path=None):
    try:
        user_image = Image.open(photo_path)
        user_image = user_image.convert("RGBA")

        max_width, max_height = user_image.size
        font, text_width, text_height = get_dynamic_font(user_image, text, max_width, max_height, font_path)

        text_width = int(text_width * size_multiplier)
        text_height = int(text_height * size_multiplier)

        x = (max_width - text_width) // 2 + x_offset
        y = (max_height - text_height) // 2 + y_offset
        text_position = (x, y)

        draw = ImageDraw.Draw(user_image)
        add_3d_text(draw, text_position, text, font, glow_color=glow_color, text_color="white", glow_strength=10)

        user_image.save(output_path, "PNG")
        return output_path
    except Exception as e:
        logger.error(f"Error adding text to image: {e}")
        return None

# Reinitialize the bot after session is revoked
async def restart_bot():
    try:
        app.stop()  # Stop the previous client instance
        logger.info("Bot stopped. Restarting the bot.")
        time.sleep(2)  # Giving some time before reinitializing
        app = create_app()  # Reinitialize the bot client
        app.run()  # Start the bot again
    except Exception as e:
        logger.error(f"Error during bot restart: {e}")

# Handler for position adjustments, size changes, and glow color changes
@app.on_callback_query(filters.regex("^(left|right|up|down|smaller|bigger|glow_[a-z]+)$"))
async def button_handler(_, callback_query: CallbackQuery):
    action = callback_query.data
    x_offset, y_offset = (0, 0)  # Default position, replace with actual position logic
    size_multiplier = 1  # Default size multiplier
    text = "Sample Text"  # Replace with the actual user text input
    glow_color = "red"  # Default glow color
    font_path = "fonts/FIGHTBACK.ttf"  # Default font path

    # Adjust position, size, and glow color based on action
    if action == "left":
        x_offset -= 10
    elif action == "right":
        x_offset += 10
    elif action == "up":
        y_offset -= 10
    elif action == "down":
        y_offset += 10
    elif action == "smaller":
        size_multiplier = max(0.5, size_multiplier - 0.1)
    elif action == "bigger":
        size_multiplier = min(2, size_multiplier + 0.1)
    elif action == "glow_red":
        glow_color = "red"
    elif action == "glow_green":
        glow_color = "green"
    elif action == "glow_blue":
        glow_color = "blue"

    # Regenerate the logo with updated settings
    output_path = f"logos/updated_{text}_logo.png"

    result = await add_text_to_image(photo_path, text, output_path, x_offset, y_offset, size_multiplier, glow_color, font_path)

    if result:
        media = InputMediaPhoto(media=output_path, caption="")
        await callback_query.message.edit_media(media=media)
        await callback_query.answer(f"Logo updated with {action}")

# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text("Welcome to Logo Creator Bot! Send a photo to get started.")

# Global error handling using try-except for the main part
try:
    app = create_app()  # Initialize the app
    app.run()
except SessionRevoked as e:
    logger.error(f"Session revoked: {str(e)}. The session has been invalidated.")
    # Restart the bot if session is revoked
    await restart_bot()  # This will reinitialize and restart the bot
except Exception as e:
    logger.error(f"An unexpected error occurred: {str(e)}")
    

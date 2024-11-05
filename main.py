import os
import logging
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from config import Config  # Ensure you have this file for your bot's config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client(
    "logo_creator_bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
)

# Dictionary to store user data (for handling images and text)
user_data = {}

# Function to add refined glow effect to text
def add_refined_glow(draw, position, text, font, glow_color, text_color, glow_strength=5):
    x, y = position
    # Draw glow around the text with limited strength for edges
    for offset in range(1, glow_strength + 1):  # Limit glow strength
        draw.text((x - offset, y - offset), text, font=font, fill=glow_color)
        draw.text((x + offset, y - offset), text, font=font, fill=glow_color)
        draw.text((x - offset, y + offset), text, font=font, fill=glow_color)
        draw.text((x + offset, y + offset), text, font=font, fill=glow_color)
    # Draw the main text in the center with the normal color
    draw.text(position, text, font=font, fill=text_color)

# Function to dynamically adjust text size based on available space
def get_dynamic_font(image, text, max_width, max_height):
    draw = ImageDraw.Draw(image)
    
    font_size = 100
    while font_size > 10:
        font = ImageFont.truetype("fonts/FIGHTBACK.ttf", font_size)
        text_width, text_height = draw.textsize(text, font=font)
        
        # If the text fits within the available space, break the loop
        if text_width <= max_width and text_height <= max_height:
            return font, text_width, text_height
        
        font_size -= 5  # Reduce font size if text is too big

    return font, text_width, text_height

# Function to add text to an image at a specified position
def add_text_to_image(photo_path, text, output_path, x_offset=0, y_offset=0, size_multiplier=1):
    try:
        user_image = Image.open(photo_path)
        user_image = user_image.convert("RGBA")  # Convert to RGBA for transparency

        max_width, max_height = user_image.size
        font, text_width, text_height = get_dynamic_font(user_image, text, max_width, max_height)

        # Apply size multiplier and adjust position
        text_width = int(text_width * size_multiplier)
        text_height = int(text_height * size_multiplier)

        x = (max_width - text_width) // 2 + x_offset
        y = (max_height - text_height) // 2 + y_offset
        text_position = (x, y)

        draw = ImageDraw.Draw(user_image)
        add_refined_glow(draw, text_position, text, font, glow_color="red", text_color="white", glow_strength=10)

        user_image.save(output_path, "PNG")
        return output_path
    except Exception as e:
        logger.error(f"Error adding text to image: {e}")
        return None

# Handler for when a user sends a photo
@app.on_message(filters.photo & filters.private)
async def photo_handler(_, message: Message):
    if message.photo:
        # Save the received photo
        photo_path = f"user_photos/{message.photo.file_id}.jpg"
        await message.download(photo_path)

        # Ask the user to send the logo text
        await message.reply_text("Ab apna logo text bheje.")

        # Store the user's photo path and wait for text
        user_data[message.from_user.id] = {'photo_path': photo_path}

# Handler for receiving text and creating the logo
@app.on_message(filters.text & filters.private)
async def text_handler(_, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.reply_text("Pehle apna photo bheje.")
        return

    if message.text:
        user_text = message.text.strip()

        if not user_text:
            await message.reply_text("Logo text dena hoga.")
            return

        # Get the user's photo path
        photo_path = user_data[user_id]['photo_path']
        output_path = f"logos/{user_text}_logo.png"

        # Add the logo text to the photo and create the initial logo
        result = add_text_to_image(photo_path, user_text, output_path)

        if result:
            # Send the initial logo image to the user with position adjustment buttons
            buttons = [
                [InlineKeyboardButton("⬅️ Left", callback_data="left"),
                 InlineKeyboardButton("⬆️ Up", callback_data="up"),
                 InlineKeyboardButton("⬅️ Right", callback_data="right")],
                [InlineKeyboardButton("⬇️ Down", callback_data="down"),
                 InlineKeyboardButton("🔽 Smaller", callback_data="smaller"),
                 InlineKeyboardButton("🔼 Bigger", callback_data="bigger")]
            ]
            await message.reply_photo(output_path, reply_markup=InlineKeyboardMarkup(buttons))

            # Store the current state of the image and user adjustments
            user_data[user_id]['output_path'] = output_path
            user_data[user_id]['text_position'] = (0, 0)  # Default offset
            user_data[user_id]['size_multiplier'] = 1  # Default size multiplier

# Handler for position adjustments through buttons
@app.on_callback_query(filters.regex("^(left|right|up|down|smaller|bigger)$"))
async def button_handler(_, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_data:
        return

    action = callback_query.data
    user_info = user_data[user_id]
    
    # Extract current position and size multiplier
    x_offset, y_offset = user_info['text_position']
    size_multiplier = user_info['size_multiplier']

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

    # Update user data with new position and size
    user_info['text_position'] = (x_offset, y_offset)
    user_info['size_multiplier'] = size_multiplier

    # Get the photo path and text to re-create the logo with new adjustments
    photo_path = user_info['photo_path']
    text = user_info.get('text', '')  # Keep original text from user
    output_path = f"logos/updated_{text}_logo.png"

    # Regenerate the logo with the new position and size
    add_text_to_image(photo_path, text, output_path, x_offset, y_offset, size_multiplier)

    # Send the updated logo image
    await callback_query.message.edit_photo(output_path)

# Start command handler
@app.on_message(filters.command("start"))
async def start_command(_, message: Message):
    """Welcomes the user with instructions."""
    welcome_text = (
        "👋 Welcome to the Logo Creator Bot!\n\n"
        " • Upload a photo: Send a photo first.\n"
        " • Add logo text: After sending the photo, you can provide the text for the logo.\n"
        " • Receive the logo: After text is added, you'll get your custom logo.\n"
    )

    keyboard = [
        [InlineKeyboardButton("Join 👋", url="https://t.me/BABY09_WORLD")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(welcome_text, reply_markup=reply_markup, disable_web_page_preview=True)

# Main entry point to run the bot
if __name__ == "__main__":
    app.run()
    

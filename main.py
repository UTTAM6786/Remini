import os
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
from random import randint
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User data store
user_data_store = {}

# Adjust font size dynamically
def get_dynamic_font(image, text, max_width, max_height, font_path):
    draw = ImageDraw.Draw(image)
    font_size = 100
    while font_size > 10:
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = draw.textsize(text, font=font)
        if text_width <= max_width and text_height <= max_height:
            return font
        font_size -= 5
    return font

# Define inline keyboard for adjustments with color options
def get_adjustment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Left", callback_data="move_left"),
         InlineKeyboardButton("➡️ Right", callback_data="move_right")],
        [InlineKeyboardButton("⬆️ Up", callback_data="move_up"),
         InlineKeyboardButton("⬇️ Down", callback_data="move_down")],
        [InlineKeyboardButton("🔍 Increase", callback_data="increase_size"),
         InlineKeyboardButton("🔎 Decrease", callback_data="decrease_size")],
        
        # Color selection buttons
        [InlineKeyboardButton("🔴 Red", callback_data="color_red"),
         InlineKeyboardButton("🔵 Blue", callback_data="color_blue"),
         InlineKeyboardButton("🟢 Green", callback_data="color_green"),
         InlineKeyboardButton("⚫ Black", callback_data="color_black"),
         InlineKeyboardButton("🟡 Yellow", callback_data="color_yellow"),
         InlineKeyboardButton("🟠 Orange", callback_data="color_orange"),
         InlineKeyboardButton("🟣 Purple", callback_data="color_purple")],
        
        # Blur effect buttons
        [InlineKeyboardButton("🔵 Blur -", callback_data="blur_decrease"),
         InlineKeyboardButton("🔴 Blur +", callback_data="blur_increase")],
        
        # Font selection buttons
        [InlineKeyboardButton("Deadly Advance Italic", callback_data="font_deadly_advance_italic"),
         InlineKeyboardButton("Deadly Advance", callback_data="font_deadly_advance"),
         InlineKeyboardButton("Trick or Treats", callback_data="font_trick_or_treats"),
         InlineKeyboardButton("Vampire Wars Italic", callback_data="font_vampire_wars_italic"),
         InlineKeyboardButton("Lobster", callback_data="font_lobster")],

        # Download button
        [InlineKeyboardButton("Download JPG", callback_data="download_jpg")]
    ])

# Add text to image with "brushstroke" effect, and blur functionality
async def add_text_to_image(photo_path, text, font_path, text_position, size_multiplier, text_color, blur_radius):
    try:
        user_image = Image.open(photo_path).convert("RGBA")
        max_width, max_height = user_image.size

        # Adjust font size based on size_multiplier
        font = get_dynamic_font(user_image, text, max_width, max_height, font_path)
        font = ImageFont.truetype(font_path, int(font.size * size_multiplier))
        
        # Create a new image for text drawing (text will be drawn here)
        text_image = Image.new("RGBA", user_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_image)
        text_width, text_height = draw.textsize(text, font=font)
        
        # Apply position adjustments
        x = text_position[0]
        y = text_position[1]

        # Brushstroke effect (slightly offset multiple layers of text to create a stroke effect)
        num_strokes = 8  # Number of brush strokes
        for i in range(num_strokes):
            offset_x = randint(-5, 5)  # Random horizontal offset
            offset_y = randint(-5, 5)  # Random vertical offset
            # Add a blurred stroke effect by drawing text in slightly different positions
            draw.text((x + offset_x, y + offset_y), text, font=font, fill="white")  # White outline effect
        
        # Main text in the chosen color
        draw.text((x, y), text, font=font, fill=text_color)

        # Blur the background (excluding text)
        blurred_image = user_image.filter(ImageFilter.GaussianBlur(blur_radius))

        # Composite the blurred image with the text image
        final_image = Image.alpha_composite(blurred_image, text_image)

        # Save the image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            output_path = temp_file.name
            final_image.save(output_path, "PNG")
        
        return output_path
    except Exception as e:
        logger.error(f"Error adding text to image: {e}")
        return None

# Convert image to JPG format (keeping final image with text and modifications)
def convert_to_jpg(png_path):
    try:
        # Open the PNG image
        image = Image.open(png_path)

        # Convert RGBA to RGB (necessary for JPG format)
        rgb_image = image.convert("RGB")

        # Create a temporary file for the JPG image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            jpg_path = temp_file.name
            rgb_image.save(jpg_path, "JPEG", quality=90)  # 90% quality for JPG
            return jpg_path
    except Exception as e:
        logger.error(f"Error converting PNG to JPG: {e}")
        return None

# Save user data
async def save_user_data(user_id, data):
    user_data_store[user_id] = data
    logger.info(f"User {user_id} data saved: {data}")

# Get user data
async def get_user_data(user_id):
    return user_data_store.get(user_id, None)

# Initialize the Pyrogram Client
session_name = "logo_creator_bot"
app = Client(
    session_name,
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    workdir=os.getcwd()
)

@app.on_message(filters.command("start"))
async def start_command(_, message: Message) -> None:
    welcome_text = (
        "👋 Welcome to the Logo Creator Bot!\n\n"
        "With this bot, you can create a custom logo by sending a photo and adding text to it!\n"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Join 👋", url="https://t.me/BABY09_WORLD")]])
    await message.reply_text(welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

@app.on_message(filters.photo & filters.private)
async def photo_handler(_, message: Message) -> None:
    media = message
    file_size = media.photo.file_size if media.photo else 0
    if file_size > 200 * 1024 * 1024:
        return await message.reply_text("Please provide a photo under 200MB.")
    try:
        text = await message.reply("Processing...")
        local_path = await media.download()
        await text.edit_text("Processing your logo...")
        await save_user_data(message.from_user.id, {'photo_path': local_path, 'text': '', 'text_position': (0, 0), 'size_multiplier': 1, 'text_color': 'red', 'font': 'fonts/Deadly Advance.ttf', 'blur_radius': 0})
        await message.reply_text("Please send the text you want for your logo.")
    except Exception as e:
        logger.error(e)
        await text.edit_text("File processing failed.")

@app.on_message(filters.text & filters.private)
async def text_handler(_, message: Message) -> None:
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        await message.reply_text("Please send a photo first.")
        return
    
    if user_data['text']:
        await message.reply_text("You have already entered text for the logo. Proceed with position adjustments.")
        return

    user_text = message.text.strip()
    if not user_text:
        await message.reply_text("You need to provide text for the logo.")
        return
    user_data['text'] = user_text
    await save_user_data(user_id, user_data)

    # Generate logo and show adjustment options
    font_path = user_data['font']  # Default to Deadly Advance font if not set
    output_path = await add_text_to_image(user_data['photo_path'], user_text, font_path, user_data['text_position'], user_data['size_multiplier'], ImageColor.getrgb(user_data['text_color']), user_data['blur_radius'])

    if output_path is None:
        await message.reply_text("There was an error generating the logo. Please try again.")
        return

    await message.reply_photo(photo=output_path, reply_markup=get_adjustment_keyboard())

@app.on_callback_query()
async def callback_handler(_, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data or not user_data.get("photo_path"):
        await callback_query.answer("Please upload a photo first.", show_alert=True)
        return

    # Adjust position, size, or color based on button pressed
    if callback_query.data == "move_left":
        user_data['text_position'] = (user_data['text_position'][0] - 20, user_data['text_position'][1])
    elif callback_query.data == "move_right":
        user_data['text_position'] = (user_data['text_position'][0] + 20, user_data['text_position'][1])
    elif callback_query.data == "move_up":
        user_data['text_position'] = (user_data['text_position'][0], user_data['text_position'][1] - 20)
    elif callback_query.data == "move_down":
        user_data['text_position'] = (user_data['text_position'][0], user_data['text_position'][1] + 20)
    elif callback_query.data == "increase_size":
        user_data['size_multiplier'] *= 1.1
    elif callback_query.data == "decrease_size":
        user_data['size_multiplier'] *= 0.9
    elif callback_query.data == "color_red":
        user_data['text_color'] = "red"
    elif callback_query.data == "color_blue":
        user_data['text_color'] = "blue"
    elif callback_query.data == "color_green":
        user_data['text_color'] = "green"
    elif callback_query.data == "color_black":
        user_data['text_color'] = "black"
    elif callback_query.data == "color_yellow":
        user_data['text_color'] = "yellow"
    elif callback_query.data == "color_orange":
        user_data['text_color'] = "orange"
    elif callback_query.data == "color_purple":
        user_data['text_color'] = "purple"
    elif callback_query.data == "blur_decrease":
        user_data['blur_radius'] = max(user_data['blur_radius'] - 1, 0)  # Prevent going below 0
    elif callback_query.data == "blur_increase":
        user_data['blur_radius'] += 1  # Increase blur radius
    elif callback_query.data == "download_jpg":
        # Convert the current final image to JPG and send it
        final_image_path = await add_text_to_image(user_data['photo_path'], user_data['text'], user_data['font'], user_data['text_position'], user_data['size_multiplier'], ImageColor.getrgb(user_data['text_color']), user_data['blur_radius'])
        
        if final_image_path:
            # Convert to JPG
            jpg_path = convert_to_jpg(final_image_path)
            if jpg_path:
                with open(jpg_path, "rb") as jpg_file:
                    await callback_query.message.reply_document(jpg_file, caption="Here is your logo as a JPG file.")
                os.remove(jpg_path)  # Clean up the temporary JPG file after sending it
                os.remove(final_image_path)  # Clean up the temporary PNG file after sending it
            else:
                await callback_query.message.reply_text("Error converting image to JPG.")
        else:
            await callback_query.message.reply_text("Error generating the final logo.")

        return

    await save_user_data(user_id, user_data)

    # Regenerate the logo with the new adjustments
    font_path = user_data.get("font", "fonts/Deadly Advance.ttf")  # Default to Deadly Advance font if no font is set
    output_path = await add_text_to_image(user_data['photo_path'], user_data['text'], font_path, user_data['text_position'], user_data['size_multiplier'], ImageColor.getrgb(user_data['text_color']), user_data['blur_radius'])

    if output_path is None:
        await callback_query.message.reply_text("There was an error generating the logo. Please try again.")
        return

    # Keep the buttons and update the image
    await callback_query.message.edit_media(InputMediaPhoto(media=output_path, caption="Here is your logo with the changes!"), reply_markup=get_adjustment_keyboard())
    await callback_query.answer()

if __name__ == "__main__":
    app.run()
        

import os
import logging
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
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

# Define inline keyboard for adjustments with color, blur options, and download button
def get_adjustment_keyboard(final_image_path=None):
    buttons = [
        [InlineKeyboardButton("↼ʟᴇғᴛ", callback_data="move_left"),
         InlineKeyboardButton("ʀɪɢʜᴛ⇁", callback_data="move_right")],
        [InlineKeyboardButton("↿ᴜᴘ", callback_data="move_up"),
         InlineKeyboardButton("⇃ᴅᴏᴡɴ", callback_data="move_down")],
        [InlineKeyboardButton("⛶ ✙", callback_data="increase_size"),
         InlineKeyboardButton("⛶ –", callback_data="decrease_size")],
        
        # Color selection buttons
        [InlineKeyboardButton("🔴", callback_data="color_red"),
         InlineKeyboardButton("🔵", callback_data="color_blue"),
         InlineKeyboardButton("🟢", callback_data="color_green"),
         InlineKeyboardButton("⚫", callback_data="color_black"),
         InlineKeyboardButton("🟡", callback_data="color_yellow"),
         InlineKeyboardButton("🟠", callback_data="color_orange"),
         InlineKeyboardButton("🟣", callback_data="color_purple")],
        
        # Font selection buttons
        [InlineKeyboardButton("🄵ᴀ", callback_data="font_deadly_advance_italic"),
         InlineKeyboardButton("🄵ʙ", callback_data="font_deadly_advance"),
         InlineKeyboardButton("🄵ᴄ", callback_data="font_trick_or_treats"),
         InlineKeyboardButton("🄵ᴅ", callback_data="font_vampire_wars_italic"),
         InlineKeyboardButton("🄵ᴇ", callback_data="font_lobster")],
        
        # Blur buttons
        [InlineKeyboardButton("ʙʟᴜʀ +", callback_data="blur_plus"),
         InlineKeyboardButton("ʙʟᴜʀ -", callback_data="blur_minus")],

        # Always show the Download button
        [InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ ʏᴏᴜʀ ʟᴏɢᴏ", callback_data="download_logo")]
    ]
    
    return InlineKeyboardMarkup(buttons)

# Add text to image with adjustments and color
async def add_text_to_image(photo_path, text, output_path, font_path, text_position, size_multiplier, text_color):
    try:
        user_image = Image.open(photo_path).convert("RGBA")
        max_width, max_height = user_image.size

        # Adjust font size based on size_multiplier
        font = get_dynamic_font(user_image, text, max_width, max_height, font_path)
        font = ImageFont.truetype(font_path, int(font.size * size_multiplier))
        
        draw = ImageDraw.Draw(user_image)
        text_width, text_height = draw.textsize(text, font=font)
        
        # Apply position adjustments
        x = text_position[0]
        y = text_position[1]

        # Outline effect in white (shadow effect)
        outline_width = 3
        for dx in [-outline_width, outline_width]:
            for dy in [-outline_width, outline_width]:
                draw.text((x + dx, y + dy), text, font=font, fill="white")

        # Apply main text color
        draw.text((x, y), text, font=font, fill=text_color)

        # Save the image to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            output_path = temp_file.name
            user_image.save(output_path, "PNG")
        
        return output_path
    except Exception as e:
        logger.error(f"Error adding text to image: {e}")
        return None

# Apply Blur Effect to the Background Image (without affecting the text)
async def apply_blur(photo_path, blur_intensity):
    try:
        image = Image.open(photo_path).convert("RGBA")
        
        # Apply blur effect to the image (not text)
        blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_intensity))

        # Save the blurred image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            blurred_image.save(temp_file, "PNG")
            return temp_file.name

    except Exception as e:
        logger.error(f"Error applying blur: {e}")
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
        text = await message.reply("❖ ᴘʀᴏᴄᴇssɪɴɢ...")
        local_path = await media.download()
        await text.edit_text("❖ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʟᴏɢᴏ...")
        await save_user_data(message.from_user.id, {'photo_path': local_path, 'text': '', 'text_position': (0, 0), 'size_multiplier': 1, 'text_color': 'red', 'font': 'fonts/Deadly Advance.ttf', 'blur_intensity': 0})
        await message.reply_text("✎ ɴᴏᴡ sᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ʟᴏɢᴏ ᴛᴇxᴛ.")
    except Exception as e:
        logger.error(e)
        await text.edit_text("❖ ғɪʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ғᴀɪʟᴇᴅ.")

@app.on_message(filters.text & filters.private)
async def text_handler(_, message: Message) -> None:
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    if not user_data:
        await message.reply_text("❖ ғɪʀsᴛ sᴇɴᴅ ᴍᴇ ᴀ ᴘʜᴏᴛᴏ ғᴏʀ ʟᴏɢᴏ ʙᴀᴄᴋɢʀᴏᴜᴅ.")
        return
    
    if user_data['text']:
        await message.reply_text("❖ ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴇɴᴛᴇʀᴇᴅ ᴛᴇxᴛ ғᴏʀ ʏᴏᴜʀ ʟᴏɢᴏ. ᴘʀᴏᴄᴇᴅ ᴡɪᴛʜ ᴘᴏsɪᴛɪᴏɴ ᴀᴅᴊᴜsᴛᴍᴇɴᴛs.")
        return

    user_text = message.text.strip()
    if not user_text:
        await message.reply_text("❖ ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴛᴇxᴛ ғᴏʀ ᴛʜᴇ ʟᴏɢᴏ.")
        return
    user_data['text'] = user_text
    await save_user_data(user_id, user_data)

    # Generate logo and show adjustment options
    font_path = user_data['font']  # Default to Deadly Advance font if not set
    output_path = await add_text_to_image(user_data['photo_path'], user_text, None, font_path, user_data['text_position'], user_data['size_multiplier'], ImageColor.getrgb(user_data['text_color']))

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

    # Font selection logic
    if callback_query.data == "font_deadly_advance_italic":
        user_data['font'] = "fonts/Deadly Advance Italic (1).ttf"
    elif callback_query.data == "font_deadly_advance":
        user_data['font'] = "fonts/Deadly Advance.ttf"
    elif callback_query.data == "font_trick_or_treats":
        user_data['font'] = "fonts/Trick or Treats.ttf"
    elif callback_query.data == "font_vampire_wars_italic":
        user_data['font'] = "fonts/Vampire Wars Italic.ttf"
    elif callback_query.data == "font_lobster":
        user_data['font'] = "fonts/Lobster-Regular.ttf"

    await save_user_data(user_id, user_data)

    # Regenerate the logo with the new adjustments
    font_path = user_data.get("font", "fonts/Deadly Advance.ttf")  # Default to Deadly Advance font if no font is set
    output_path = await add_text_to_image(user_data['photo_path'], user_data['text'], None, font_path, user_data['text_position'], user_data['size_multiplier'], ImageColor.getrgb(user_data['text_color']))

    if output_path is None:
        await callback_query.message.reply_text("There was an error generating the logo. Please try again.")
        return

    # Handle the Download Logo button
    if callback_query.data == "download_logo":
        # Convert to JPG format for download
        jpg_path = output_path.replace(".png", ".jpg")
        image = Image.open(output_path)
        image = image.convert("RGB")
        image.save(jpg_path, "JPEG")

        # Send the final logo JPG to the user
        await callback_query.message.reply_document(jpg_path, caption="Here is your final logo!")

        # Clean up the generated files
        os.remove(output_path)
        os.remove(jpg_path)

        # Remove the buttons after sending the final image
        await callback_query.message.edit_text("Your logo is ready for download. Enjoy!", reply_markup=None)
        await callback_query.answer()
        return

    # If the button was not download, update the image with new changes
    await callback_query.message.edit_media(InputMediaPhoto(media=output_path, caption="Here is your logo with the changes!"), reply_markup=get_adjustment_keyboard())
    await callback_query.answer()

if __name__ == "__main__":
    app.run()
    

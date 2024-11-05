import logging
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import pyfiglet  # To generate simple stylish text
import random  # For adding random symbols

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stylish Symbols List (random symbols to add around the text)
stylish_symbols = [
    "❤", "❀", "✰", "☪", "☽", "☁", "⭐", "✿", "☘", "❖", "✧", "☠", "⚡", "✪", "⚔", "❣", "➸", "✦"
]

# Function to convert text to stylish versions using pyfiglet and simple fonts
def convert_to_stylish_text(input_text):
    """Text ko stylish formats mein convert kare."""
    
    # Simple check for valid characters (letters and spaces)
    if not input_text.replace(" ", "").isalnum():
        return "Kripya sirf text daalein, special characters nahi."

    stylish_versions = []
    
    # Create 10 different stylish text versions
    for _ in range(10):
        # Randomize the font style using pyfiglet
        try:
            figlet_version = pyfiglet.figlet_format(input_text, font="slant")  # Using slant font for readability
            stylish_versions.append(figlet_version.strip())
        except Exception as e:
            logger.error(f"Error in pyfiglet: {e}")
        
        # Add stylish symbols around the text for decoration
        symbol = random.choice(stylish_symbols)
        stylish_versions_with_symbols = f"{symbol} {input_text} {symbol}"
        stylish_versions.append(stylish_versions_with_symbols)
    
    return stylish_versions

# Text handler (processing the user input text and generating stylish outputs)
async def text_handler(_, message: Message) -> None:
    """Incoming text messages ko process karein aur stylish text return karein."""
    if message.text:
        user_text = message.text.strip()

        if not user_text:
            await message.reply_text("Kripya kuch text bhejein jise main style kar sakoon.")
            return
        
        # Convert the text to stylish versions with symbols
        stylish_texts = convert_to_stylish_text(user_text)
        
        # Agar text ko convert nahi kar sakte to error message bhejenge
        if isinstance(stylish_texts, str):
            await message.reply_text(stylish_texts)
        else:
            # Har ek stylish version ko user ko bhejna
            for stylish_version in stylish_texts:
                await message.reply_text(stylish_version)

# Main entry point to run the bot
if __name__ == "__main__":
    app = Client(
        "stylish_text_bot_session",  # Session name
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
    )

    if app:
        # Define handlers after the app is created
        app.on_message(filters.text & filters.private)(text_handler)

        # Run the bot
        app.run()
    else:
        logger.error("Client banane mein kuch problem aayi.")

from flask import Flask, request, send_file, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)

API_KEY = "1weekkeysforujjaiwal"
TIMEOUT = 10

def fetch_player_info(uid, region):
    url = f"https://garena-free-fire-official-info-site.vercel.app/player-info?uid={uid}&region={region}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        return response.json() if response.status_code == 200 else {"error": "Unexpected API response"}
    except requests.Timeout:
        return {"error": "API request timed out"}
    except Exception:
        return {"error": "Failed to fetch player info"}

def fetch_images(banner_id, avatar_id):
    try:
        banner_url = f"https://uditanshu-ffitems.vercel.app/item-image?id={banner_id}&key=UDITxTECH"
        avatar_url = f"https://uditanshu-ffitems.vercel.app/item-image?id={avatar_id}&key=UDITxTECH"

        banner_response = requests.get(banner_url, timeout=TIMEOUT)
        avatar_response = requests.get(avatar_url, timeout=TIMEOUT)

        return (banner_response.content, avatar_response.content) if banner_response.status_code == 200 and avatar_response.status_code == 200 else (None, None)
    except Exception:
        return None, None

def load_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def overlay_images(banner_img, avatar_img, player_name, guild_name=None, level=None):
    try:
        banner = Image.open(io.BytesIO(banner_img)).convert("RGBA")
        avatar = Image.open(io.BytesIO(avatar_img)).convert("RGBA").resize((55, 60))
        banner.paste(avatar, (0, 0), avatar)

        draw = ImageDraw.Draw(banner)
        bold_font = load_font("arialbd.ttf", 19)
        guild_font = load_font("arialbd.ttf", 22)
        level_font = load_font("arialbd.ttf", 20)

        draw.text((57, 2), player_name, fill="white", font=bold_font)
        if guild_name:
            draw.text((73, 48), guild_name, fill="#DDDDDD", font=guild_font)
        if level:
            banner_w, banner_h = banner.size
            draw.text((banner_w - 35, banner_h - 12), f"Lvl - {level}", fill="white", font=level_font, stroke_width=1, stroke_fill="black")

        return banner
    except Exception:
        return None

@app.route('/avatar-banner', methods=['GET'])
def generate_image():
    uid = request.args.get('uid')
    region = request.args.get('region')
    key = request.args.get('key')

    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403
    if not uid or not region:
        return jsonify({"error": "Missing uid or region in parameter"}), 400

    player_data = fetch_player_info(uid, region)
    if "error" in player_data:
        return jsonify(player_data), 400

    banner_id = player_data["AccountInfo"].get("AccountBannerId")
    avatar_id = player_data["AccountInfo"].get("AccountAvatarId")
    player_name = player_data["AccountInfo"].get("AccountName", "Player")
    level = str(player_data["AccountInfo"].get("AccountLevel", 0))
    guild_name = player_data.get("GuildInfo", {}).get("GuildName")

    banner_img, avatar_img = fetch_images(banner_id, avatar_id)
    if not banner_img or not avatar_img:
        return jsonify({"error": "Failed to fetch avatar or banner image"}), 500

    final_image = overlay_images(banner_img, avatar_img, player_name, guild_name, level)
    if not final_image:
        return jsonify({"error": "Failed to generate image"}), 500

    img_buffer = io.BytesIO()
    final_image.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    return send_file(img_buffer, mimetype="image/png")

@app.route('/check_key', methods=['GET'])
def check_key():
    return jsonify({"status": "valid" if request.args.get('key') == API_KEY else "invalid"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
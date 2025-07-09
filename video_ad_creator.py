import os
# ---- CRUCIAL: Set this BEFORE any MoviePy import! ----
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"

import json
import random
import datetime
import requests
import pyttsx3
from moviepy.editor import *

# --- SETTINGS ---
PRODUCTS_BASE = "products"
AUDIO_BASE = "audio"
VIDEO_OUT_BASE = "videos"
BRAND = "Bettsiddy Collections"
RESOLUTION = (1080, 1350)
BITRATE = "9000k"
FONTS = {
    "brand": "Arial Black",
    "subtitle": "Segoe UI Bold",
    "fallback": "Arial"
}
TELEGRAM_TOKEN = "8112869961:AAFd_RUFIHSs2EVcOfYZxsruLKKvoGpLHP4"
TELEGRAM_CHAT_ID = "5802469496"
MAX_PER_RUN = 5  # Only 5 videos per run

def list_product_folders(base=PRODUCTS_BASE):
    return sorted([
        os.path.join(base, f) for f in os.listdir(base)
        if os.path.isdir(os.path.join(base, f))
    ])

def list_images(product_folder):
    return [os.path.join(product_folder, f) for f in os.listdir(product_folder)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

def list_music():
    return [os.path.join(AUDIO_BASE, f) for f in os.listdir(AUDIO_BASE)
            if f.lower().endswith('.mp3')]

def pick_next_music(used_file, music_files):
    used = []
    if os.path.exists(used_file):
        with open(used_file, "r") as f:
            used = json.load(f)
    unused = [m for m in music_files if m not in used]
    if not unused:
        unused = music_files
        used = []
    chosen = random.choice(unused)
    used.append(chosen)
    with open(used_file, "w") as f:
        json.dump(used, f)
    return chosen

def tts_to_audio(text, out_path):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    selected_voice = None
    for v in voices:
        if "david" in v.name.lower():
            selected_voice = v.id
            break
    if not selected_voice:
        for v in voices:
            if "mark" in v.name.lower():
                selected_voice = v.id
                break
    if selected_voice:
        engine.setProperty('voice', selected_voice)
    engine.setProperty('rate', 158)
    engine.save_to_file(text, out_path)
    engine.runAndWait()
    return out_path

def get_product_ad_caption(product_name, cache_dir="ad_cache", openai_api_key=None):
    os.makedirs(cache_dir, exist_ok=True)
    safe_name = product_name.replace("/", "_")
    cache_file = os.path.join(cache_dir, f"{safe_name}.txt")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    import openai
    client = openai.OpenAI(api_key=openai_api_key)
    prompt = (
        f"Write a creative, energetic, 2-sentence short video ad for a fashion product called '{product_name}' "
        f"for {BRAND}. Make it catchy and unique. End with a strong call to action, like 'Shop now at Bettsiddy!'"
    )
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80,
        temperature=0.9
    )
    caption = resp.choices[0].message.content.strip()
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(caption)
    return caption

def text_slide(text, size, dur, font_size=64, overlay_color=(0,0,0,170), ypos=None, font=None, shadow=True):
    font = font or FONTS.get("subtitle", "Arial")
    try:
        txt = TextClip(text, fontsize=font_size, font=font, color='white',
                       stroke_width=3, stroke_color='black',
                       size=(size[0]-80, None), method='caption')
    except Exception:
        txt = TextClip(text, fontsize=font_size, color='white',
                       stroke_width=3, stroke_color='black',
                       size=(size[0]-80, None), method='caption')
    box = ColorClip((txt.w+44, txt.h+48), color=overlay_color, ismask=False).set_opacity(0.85)
    yfinal = ypos if ypos is not None else (size[1]//2 - txt.h//2)
    box = box.set_position(('center', yfinal-24))
    txt = txt.set_position(('center', yfinal))
    comps = [box, txt]
    if shadow:
        shadow_box = ColorClip((txt.w+56, txt.h+58), color=(0,0,0), ismask=False).set_opacity(0.25)
        shadow_box = shadow_box.set_position(('center', yfinal-14))
        comps = [shadow_box] + comps
    return CompositeVideoClip(comps, size=size).set_duration(dur).crossfadein(0.5).crossfadeout(0.5)

def animated_emoji(emoji, size, dur, start_y, end_y, font_size=90):
    font = FONTS.get("brand", "Arial")
    try:
        em_clip = TextClip(emoji, fontsize=font_size, font=font, color='white')
    except Exception:
        em_clip = TextClip(emoji, fontsize=font_size, color='white')
    return (em_clip
            .set_position(lambda t: ('center', int(start_y + (end_y - start_y) * (t/dur))))
            .set_duration(dur)
            .crossfadein(0.3)
            .crossfadeout(0.3))

def ken_burns(img_path, size, dur, zoom=1.11):
    img_clip = ImageClip(img_path).resize(size).set_duration(dur)
    return img_clip.resize(lambda t: 1 + (zoom-1)*t/dur)

def repeat_images_to_duration(images, total_duration, static_time=10, min_per=2.8, max_per=5):
    show_time = total_duration - static_time
    n_images = len(images)
    per_image = min(max(show_time / n_images, min_per), max_per)
    cycle = int((show_time + 0.01) // (n_images * per_image)) + 1
    show_total = n_images * cycle
    per_image = show_time / show_total
    images_repeated = (images * cycle)[:show_total]
    return images_repeated, per_image

def create_video_for_product(product_name, images, caption, music_path, out_path, min_total_duration=38):
    size = RESOLUTION
    intro_dur = 3.2
    outro_dur = 4.2
    cta_slide_dur = 2.8
    static_time = intro_dur + outro_dur + cta_slide_dur

    images, per_image_dur = repeat_images_to_duration(images, min_total_duration, static_time=static_time)
    random.shuffle(images)
    slides = []
    slides.append(text_slide(f"{product_name.title()} Drop!", size, intro_dur, font_size=78, overlay_color=(0,21,77,205), ypos=size[1]//2 - 120, font=FONTS["brand"]))
    for idx, img_path in enumerate(images):
        dur = per_image_dur
        img_clip = ken_burns(img_path, size, dur)
        overlay = ColorClip(size, color=(8,110,240)).set_opacity(0.14).set_duration(dur)
        txt = None
        emoji = None
        if idx == 0:
            txt = text_slide(product_name.title(), size, dur, font_size=64, overlay_color=(250,46,130,140), ypos=size[1]-270, font=FONTS["subtitle"])
            emoji = animated_emoji("✨", size, dur, -60, size[1]//2-120)
        elif idx % 2 == 1:
            txt = text_slide("Shop Now!", size, dur, font_size=48, overlay_color=(0,21,77,120), ypos=size[1]-140, font=FONTS["brand"])
            emoji = animated_emoji("👜", size, dur, size[1], size[1]//2+70, font_size=74)
        else:
            txt = text_slide("Your Style. Your Story.", size, dur, font_size=40, overlay_color=(250,46,130,110), ypos=120, font=FONTS["subtitle"])
            emoji = animated_emoji("🌟", size, dur, -20, size[1]//2-30, font_size=66)
        slides.append(CompositeVideoClip([img_clip, overlay, txt, emoji], size=size))
    slides.append(text_slide("Tap link in bio to shop 👆", size, cta_slide_dur, font_size=58, overlay_color=(250,46,130,185), ypos=size[1]//2 + 90, font=FONTS["brand"]))
    outro = ColorClip(size, color=(0,21,77)).set_opacity(0.98).set_duration(outro_dur)
    outro_txt = text_slide(f"{BRAND}\nShop now!\n{product_name.title()}", size, outro_dur, font_size=54, overlay_color=(250,46,130,170), ypos=size[1]//2, font=FONTS["brand"])
    slides.append(CompositeVideoClip([outro, outro_txt, animated_emoji("🚀", size, outro_dur, -100, size[1]//2+30, font_size=90)], size=size))
    video_clip = concatenate_videoclips(slides, method="compose", padding=-0.6)

    # --- TTS ---
    tts_dir = "tts_cache"
    os.makedirs(tts_dir, exist_ok=True)
    safe_name = product_name.replace("/", "_")
    tts_path = os.path.join(tts_dir, f"{safe_name}.mp3")
    if not os.path.exists(tts_path):
        tts_to_audio(caption, tts_path)
    tts_audio = AudioFileClip(tts_path)

    # --- Background music ---
    music_audio = AudioFileClip(music_path)
    if music_audio.duration < video_clip.duration:
        loops = int(video_clip.duration // music_audio.duration) + 1
        music_audio = concatenate_audioclips([music_audio]*loops)
    music_audio = music_audio.subclip(0, video_clip.duration).fx(lambda a: a.volumex(0.27))

    # Mix voice and music
    from moviepy.audio.AudioClip import CompositeAudioClip
    final_audio = CompositeAudioClip([music_audio, tts_audio.volumex(1.18)]).set_duration(video_clip.duration)
    video_clip = video_clip.set_audio(final_audio)
    video_clip = video_clip.set_duration(final_audio.duration)

    video_clip.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        bitrate=BITRATE,
        preset="slow"
    )
    print(f"Saved video: {out_path}")

def send_video_telegram(video_path, product_name):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(video_path, "rb") as video_file:
        files = {"video": video_file}
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": f"New ad for: {product_name}\nShop: bettsiddycollections.store"
        }
        response = requests.post(url, data=data, files=files)
    print("Telegram send:", response.status_code, response.text)

def load_used_folders(used_folders_file):
    if os.path.exists(used_folders_file):
        with open(used_folders_file, "r") as f:
            used = json.load(f)
    else:
        used = []
    return used

def save_used_folders(used_folders_file, used):
    with open(used_folders_file, "w") as f:
        json.dump(used, f)

if __name__ == "__main__":
    # Load API key for OpenAI (for ad copy)
    with open("config/secrets.json") as f:
        secrets = json.load(f)
    OPENAI_API_KEY = secrets["openai"]["api_key"]

    os.makedirs(VIDEO_OUT_BASE, exist_ok=True)
    used_music_file = os.path.join(AUDIO_BASE, ".used_music.json")
    music_files = list_music()
    used_folders_file = os.path.join(PRODUCTS_BASE, ".used_folders.json")
    all_folders = list_product_folders()

    used = load_used_folders(used_folders_file)

    # If all used, reset
    if set(used) >= set(all_folders):
        used = []
        print("All folders have been used. Resetting for a new round.")

    # Get up to MAX_PER_RUN unused folders, in order
    to_process = [folder for folder in all_folders if folder not in used][:MAX_PER_RUN]

    count = 0
    for prod_folder in to_process:
        product_name = os.path.basename(prod_folder)
        print(f"\nProcessing: {product_name}")
        images = list_images(prod_folder)
        if not images:
            print(f"  No images found for {product_name}, skipping.")
            used.append(prod_folder)
            continue
        music_path = pick_next_music(used_music_file, music_files)
        print(f"  Using bgm: {os.path.basename(music_path)}")
        caption = get_product_ad_caption(product_name, openai_api_key=OPENAI_API_KEY)
        today = datetime.date.today().isoformat()
        video_out = os.path.join(VIDEO_OUT_BASE, f"{product_name}_ad_{today}.mp4")
        create_video_for_product(product_name, images, caption, music_path, video_out, min_total_duration=38)
        send_video_telegram(video_out, product_name)
        used.append(prod_folder)
        count += 1
        save_used_folders(used_folders_file, used)  # Save after each to prevent repeat if interrupted

    save_used_folders(used_folders_file, used)
    print(f"Done. Created {count} video(s) this run.")

"""Genera los audios árabes del juego con la voz libre Piper (ar_JO-kareem, licencia MIT).
Uso: gen.py texts.json modelo.onnx carpeta_salida
Las palabras sin vocales se pronuncian con su forma vocalizada (DIAC) para que la voz no adivine."""
import sys, json, hashlib, subprocess, wave, os, re
from piper import PiperVoice, SynthesisConfig
SLOW = SynthesisConfig(length_scale=1.5)   # voz más lenta, para niños

texts = json.load(open(sys.argv[1], encoding="utf-8"))
voice = PiperVoice.load(sys.argv[2])
out = sys.argv[3]
os.makedirs(out, exist_ok=True)

DIAC = {
 # nombres de las letras
 "ألف":"أَلِف","باء":"بَاء","تاء":"تَاء","ثاء":"ثَاء","جيم":"جِيم","حاء":"حَاء","خاء":"خَاء","دال":"دَال","ذال":"ذَال","راء":"رَاء",
 "زاي":"زَاي","سين":"سِين","شين":"شِين","صاد":"صَاد","ضاد":"ضَاد","طاء":"طَاء","ظاء":"ظَاء","عين":"عَيْن","غين":"غَيْن","فاء":"فَاء",
 "قاف":"قَاف","كاف":"كَاف","لام":"لَام","ميم":"مِيم","نون":"نُون","هاء":"هَاء","واو":"وَاو","ياء":"يَاء",
 # palabras de ejemplo, vocabulario y deletreo
 "أسد":"أَسَد","بيت":"بَيْت","تفاحة":"تُفَّاحَة","ثعلب":"ثَعْلَب","جمل":"جَمَل","حصان":"حِصَان","خبز":"خُبْز","دب":"دُبّ","ذرة":"ذُرَة",
 "ريشة":"رِيشَة","زرافة":"زَرَافَة","سمكة":"سَمَكَة","شمس":"شَمْس","صندوق":"صُنْدُوق","ضفدع":"ضِفْدَع","طائرة":"طَائِرَة","ظرف":"ظَرْف",
 "غيمة":"غَيْمَة","فيل":"فِيل","قمر":"قَمَر","كتاب":"كِتَاب","ليمون":"لَيْمُون","مسجد":"مَسْجِد","نجمة":"نَجْمَة","هدية":"هَدِيَّة",
 "وردة":"وَرْدَة","يد":"يَد","قطة":"قِطَّة","كلب":"كَلْب","عصفور":"عُصْفُور","خروف":"خَرُوف","موزة":"مَوْزَة","عنب":"عِنَب",
 "برتقالة":"بُرْتُقَالَة","حليب":"حَلِيب","ماء":"مَاء","نخلة":"نَخْلَة","أحمر":"أَحْمَر","أزرق":"أَزْرَق","أخضر":"أَخْضَر","أصفر":"أَصْفَر",
 "أبيض":"أَبْيَض","أسود":"أَسْوَد","أم":"أُمّ","أب":"أَب","أخ":"أَخ","أخت":"أُخْت","جدة":"جَدَّة","جد":"جَدّ","باب":"بَاب","قلم":"قَلَم",
 # números
 "واحد":"وَاحِد","اثنان":"اِثْنَان","ثلاثة":"ثَلَاثَة","أربعة":"أَرْبَعَة","خمسة":"خَمْسَة","ستة":"سِتَّة","سبعة":"سَبْعَة",
 "ثمانية":"ثَمَانِيَة","تسعة":"تِسْعَة","عشرة":"عَشَرَة",
 # saludos
 "صباح الخير":"صَبَاحُ الْخَيْر","مساء الخير":"مَسَاءُ الْخَيْر","شكرًا":"شُكْرًا","من فضلك":"مِنْ فَضْلِك","نعم":"نَعَم","لا":"لَا",
 "مع السلامة":"مَعَ السَّلَامَة","كيف حالك؟":"كَيْفَ حَالُك؟",
}
# sílabas sueltas (بَ، بِ، بُ…): se alarga un poco la vocal para que suene clara
SYL = re.compile(r"^[ء-ي][َُِ]$")
def speakable(t):
    if t in DIAC: return DIAC[t]
    if SYL.match(t):
        long = {"َ":"ا","ِ":"ي","ُ":"و"}[t[1]]
        return t + long
    return t

index = {}
for t in texts:
    name = hashlib.sha1(("lento|" + t).encode("utf-8")).hexdigest()[:12] + ".mp3"   # nombre nuevo: evita que se oiga la versión antigua guardada
    wav = os.path.join(out, "tmp.wav")
    with wave.open(wav, "wb") as wf:
        voice.synthesize_wav(speakable(t), wf, syn_config=SLOW)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,apad=pad_dur=0.08",
                    "-ac", "1", "-ar", "22050", "-b:a", "48k", os.path.join(out, name)], check=True)
    index[t] = name
os.remove(os.path.join(out, "tmp.wav"))
json.dump(index, open(os.path.join(out, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(index), "audios")

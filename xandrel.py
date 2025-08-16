# xandrel_bot_full_interactive.py
import os
from dotenv import load_dotenv
import asyncio
import discord
import json
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput
from discord import Interaction


# ================== SUNUCU/SES AYARLARI ==================
GUILD_ID = 1400217348232970260
VOICE_CHANNEL_ID = 1400835526709346487
SILENT_MP3_PATH = "0801.mp3"

# ================== INTENTS & BOT ==================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="x!", intents=intents)

# ================== ORTAK YARDIMCI ==================
def formatla(sayi: int | float) -> str:
    return f"{sayi:,}".replace(",", ".")

# ================== SES KANALI MÜZİK DÖNGÜSÜ ==================
async def play_loop(vc: discord.VoiceClient):
    while True:
        try:
            if not vc.is_playing():
                vc.play(discord.FFmpegPCMAudio(SILENT_MP3_PATH))
            await asyncio.sleep(1)
        except Exception:
            await asyncio.sleep(2)

@bot.event
async def on_ready():
    print(f'✅ Xandrel Bot Aktif: {bot.user.name}')
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(VOICE_CHANNEL_ID)
        if channel and isinstance(channel, discord.VoiceChannel):
            try:
                if guild.voice_client and guild.voice_client.is_connected():
                    vc = guild.voice_client
                else:
                    vc = await channel.connect()
                asyncio.create_task(play_loop(vc))
            except Exception as e:
                print(f"❌ Ses kanalına bağlanırken hata: {e}")
    load_gelir()
    load_mal()

# ================== GELİR & MAL SİSTEMİ (JSON KALICI KASA) ==================
fiyatlar = {
    "ethanol": {"satis": 500},
    "meth_pills": {"satis": 500},
    "lithium": {"satis": 500},
    "acetone": {"satis": 500},
    "ammonia": {"satis": 500},
    "meth_lab_kit": {"satis": 500},
    "cement": {"satis": 500},
    "hydrochloric": {"satis": 500},
    "gasoline": {"satis": 500},
    "lockpick": {"satis": 50},
    "advancedlockpick": {"satis": 1000},
    "drill": {"satis": 2000},
    "radio": {"satis": 1000},
    "illegal_gps": {"satis": 10000},
    "armour": {"satis": 5000},
    "ammo_9": {"satis": 900}
}

GELIR_JSON = "gelir.json"
MAL_JSON = "mal.json"
gelir_toplam = 0
mal_data = {}

def load_gelir():
    global gelir_toplam
    if not os.path.exists(GELIR_JSON):
        with open(GELIR_JSON, "w", encoding="utf-8") as f:
            json.dump({"toplam": 0}, f)
    with open(GELIR_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        gelir_toplam = data.get("toplam", 0)

def save_gelir():
    with open(GELIR_JSON, "w", encoding="utf-8") as f:
        json.dump({"toplam": gelir_toplam}, f, ensure_ascii=False, indent=4)

def load_mal():
    global mal_data
    if not os.path.exists(MAL_JSON):
        with open(MAL_JSON, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(MAL_JSON, "r", encoding="utf-8") as f:
        mal_data = json.load(f)

def save_mal():
    with open(MAL_JSON, "w", encoding="utf-8") as f:
        json.dump(mal_data, f, ensure_ascii=False, indent=4)

# ================== GELİR MODAL & DROPDOWN ==================
class GelirModal(Modal):
    def __init__(self, urunler):
        super().__init__(title="💰 Ürün Adetlerini Girin")
        self.urunler = urunler
        self.inputs = []
        for urun in urunler:
            label = urun.replace("_"," ").title().replace("Gps","GPS")
            ti = TextInput(label=label, placeholder="0", required=False)
            self.add_item(ti)
            self.inputs.append((urun, ti))

    async def on_submit(self, interaction: Interaction):
        toplam_satis = 0
        detaylar = []

        for key, field in self.inputs:
            try:
                miktar = int(field.value)
            except:
                miktar = 0
            if miktar > 0:
                satis = fiyatlar[key]["satis"] * miktar
                toplam_satis += satis
                detaylar.append(f"▪ {key.replace('_',' ').title()} × {miktar} → {formatla(satis)}₺")

        embed = discord.Embed(title="💰 Gelir Hesaplama", color=discord.Color.green())
        if detaylar:
            embed.add_field(name="🧾 Ürün Bazlı Gelir", value="\n".join(detaylar), inline=False)
            embed.add_field(name="🏦 Toplam Gelir", value=f"**{formatla(toplam_satis)}₺**", inline=False)
        else:
            embed.description = "Hiç ürün girilmedi."

        # İndirim dropdown'ını göster
        view = GelirIndirimSelectView(toplam_satis)
        await interaction.response.send_message(embed=embed, view=view)


class GelirIndirimSelect(Select):
    def __init__(self, toplam_satis):
        self.toplam_satis = toplam_satis
        options = [
            discord.SelectOption(label="%0 İndirim", value="0"),
            discord.SelectOption(label="%5 İndirim", value="5"),
            discord.SelectOption(label="%10 İndirim", value="10"),
            discord.SelectOption(label="%20 İndirim", value="20"),
        ]
        super().__init__(placeholder="💸 İndirim seçin", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        indirim_orani = int(self.values[0])
        toplam_satis_indirimli = int(self.toplam_satis * (1 - indirim_orani / 100))
        embed = discord.Embed(
            title="💰 Gelir Hesaplama (İndirimli)",
            description=f"Seçilen indirim: %{indirim_orani}\nToplam Gelir: {formatla(toplam_satis_indirimli)}₺",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)


class GelirIndirimSelectView(View):
    def __init__(self, toplam_satis):
        super().__init__(timeout=None)
        self.add_item(GelirIndirimSelect(toplam_satis))


class GelirDropdown(Select):
    def __init__(self):
        options = [discord.SelectOption(label=k.replace("_"," ").title(), value=k) for k in fiyatlar.keys()]
        super().__init__(placeholder="Ürünleri seçin...", min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GelirModal(self.values))


class GelirView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GelirDropdown())


@bot.command()
async def gelir(ctx):
    embed = discord.Embed(
        title="💰 Gelir Takip Sistemi",
        description="Dropdown’dan ürünleri seçin ve ardından adetlerini girin.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=GelirView())

@bot.command()
async def kasagöster(ctx):
    embed = discord.Embed(
        title="🏦 Kasadaki Toplam Gelir",
        description=f"💰 Toplam Gelir: **{formatla(gelir_toplam)}₺**",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

# ================== MAL HESAPLAMA ==================
class MalModal(Modal):
    def __init__(self, urunler):
        super().__init__(title="📦 Mal Adetlerini Girin")
        self.inputs = []
        for urun in urunler:
            label = urun.replace("_"," ").title()
            ti = TextInput(label=label, placeholder="0", required=False)
            self.add_item(ti)
            self.inputs.append((urun, ti))

    async def on_submit(self, interaction: Interaction):
        for key, field in self.inputs:
            try:
                miktar = int(field.value)
            except:
                miktar = 0
            if miktar > 0:
                mal_data[key] = mal_data.get(key, 0) + miktar
        save_mal()
        await interaction.response.send_message("✅ Mallar başarıyla hesaplandı ve kaydedildi.", ephemeral=True)

class MalDropdown(Select):
    def __init__(self):
        options = [discord.SelectOption(label=k.replace("_"," ").title(), value=k) for k in fiyatlar.keys()]
        super().__init__(placeholder="Malları seçin...", min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(MalModal(self.values))

class MalView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MalDropdown())

mal_fiyatlari = {
    "kubar1": 180, "kubar2": 250, "kubar3": 400,
    "meth1": 200, "meth2": 235, "meth3": 275,
    "ot1": 180, "ot2": 250, "ot3": 400
}

class MalMiktarModal(Modal):
    def __init__(self, secilenler):
        super().__init__(title="🌿 Ürün Miktarlarını Girin (kg)")
        self.secilenler = secilenler
        self.inputs = []
        for urun in secilenler:
            label = urun.upper().replace("KUBAR", "Kubar ").replace("METH", "Meth ").replace("OT", "Ot ")
            input_field = TextInput(label=label, placeholder="0", required=False)
            self.add_item(input_field)
            self.inputs.append((urun, input_field))

    async def on_submit(self, interaction: Interaction):
        toplam = 0
        toplam_kg = 0
        detaylar = []
        analiz_listesi = []
        for urun, input_field in self.inputs:
            try:
                kg = int(input_field.value)
            except:
                kg = 0
            if kg > 0:
                birim_fiyat = mal_fiyatlari[urun]
                tutar = kg * birim_fiyat
                toplam += tutar
                toplam_kg += kg
                detaylar.append(f"▪️ {kg} kg × {urun.upper()} → {formatla(tutar)}$")
                analiz_listesi.append((urun.upper(), kg, tutar))

        embed = discord.Embed(title="📦 MAL SATIŞ HESAPLAMA", color=discord.Color.dark_green())
        if detaylar:
            embed.add_field(name="🧮 Detaylı Hesaplama", value="\n".join(detaylar), inline=False)
            embed.add_field(name="💰 Toplam Tutar", value=f"**{formatla(toplam)}$**", inline=False)
            embed.add_field(name="⚖️ Toplam Ağırlık", value=f"{formatla(toplam_kg)} kg", inline=True)
            if analiz_listesi:
                en_pahali = max(analiz_listesi, key=lambda x: x[2])
                embed.add_field(name="💎 En Karlı Satış", value=f"{en_pahali[0]} → {formatla(en_pahali[2])}$", inline=True)
                sirali = sorted(analiz_listesi, key=lambda x: x[2], reverse=True)
                sirali_text = "\n".join([f"{u} → {formatla(t)}$" for u, _, t in sirali])
                embed.add_field(name="📊 Yüksekten Düşüğe", value=sirali_text, inline=False)
        else:
            embed.description = "Hiçbir ürün girilmedi."
        await interaction.response.send_message(embed=embed)

class MalDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🌿 Kubar 1", value="kubar1"),
            discord.SelectOption(label="🌿 Kubar 2", value="kubar2"),
            discord.SelectOption(label="🌿 Kubar 3", value="kubar3"),
            discord.SelectOption(label="🧪 Meth 1", value="meth1"),
            discord.SelectOption(label="🧪 Meth 2", value="meth2"),
            discord.SelectOption(label="🧪 Meth 3", value="meth3"),
            discord.SelectOption(label="🍁 Ot 1", value="ot1"),
            discord.SelectOption(label="🍁 Ot 2", value="ot2"),
            discord.SelectOption(label="🍁 Ot 3", value="ot3"),
        ]
        super().__init__(placeholder="🧾 Mal türlerini seç (birden fazla)", min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(MalMiktarModal(self.values))

class MalDropdownView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MalDropdown())

@bot.command()
async def malhesapla(ctx):
    embed = discord.Embed(
        title="🧮 XANDREL MAL HESAPLAMA",
        description="Aşağıdan mal türlerini seçin, ardından kilogram miktarlarını girin.",
        color=discord.Color.teal()
    )
    await ctx.send(embed=embed, view=MalDropdownView())

# ================== KIYAFET KOMUTU (INTERAKTIF) ==================
kıyafetler = {
    "legal": "legal.png",
    "illegal": "illegal.png"
}

class KiyafetDropdown(Select):
    def __init__(self):
        options = [discord.SelectOption(label=k.title(), value=k) for k in kıyafetler.keys()]
        super().__init__(placeholder="Kıyafet seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        secim = self.values[0]
        embed = discord.Embed(title=f"👕 {secim.title()} Kıyafeti", color=discord.Color.blue())
        embed.set_image(url=f"attachment://{kıyafetler[secim]}")
        await interaction.response.send_message(embed=embed, file=discord.File(kıyafetler[secim]))

@bot.command()
async def kıyafet(ctx):
    view = View()
    view.add_item(KiyafetDropdown())
    embed = discord.Embed(title="👕 Kıyafet Seçimi", description="Dropdown’dan kıyafet seçin.", color=discord.Color.blue())
    await ctx.send(embed=embed, view=view)

# ================== SUNUCU KOMUTU ==================
class SunucuDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BORP | Blue Ocean RolePlay", value="borp")
        ]
        super().__init__(placeholder="Sunucu seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        secim = self.values[0]
        if secim == "borp":
            embed = discord.Embed(
                title="🌊 BORP | Blue Ocean RolePlay",
                description="Xandrel'in rol yaptığı sunucu.",
                color=discord.Color.purple()
            )
            embed.add_field(name="Discord", value="https://discord.gg/borp", inline=False)
            embed.add_field(name="Tanıtım Videosu", value="https://youtu.be/borpvideo", inline=False)
            await interaction.response.send_message(embed=embed)

@bot.command()
async def sunucu(ctx):
    view = View()
    view.add_item(SunucuDropdown())
    embed = discord.Embed(title="🌐 Sunucu Bilgileri", description="Dropdown’dan sunucu seçin.", color=discord.Color.purple())
    await ctx.send(embed=embed, view=view)

# ================== ROLLER KOMUTU ==================
roller = {
    "Patron": "Aile Reisi",
    "Yayıncı": "Streamer",
    "Developer": "Kod Yazıcı",
    "İnfaz Timi Lideri": "Görevli Lider",
    "İnfaz Timi": "Görevli",
    "Xandrel": "Özel Rol",
    "Xandrel Bot": "Bot"
}

class RollerDropdown(Select):
    def __init__(self):
        options = [discord.SelectOption(label=k, description=v) for k, v in roller.items()]
        super().__init__(placeholder="Rol seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        secim = self.values[0]
        embed = discord.Embed(title=f"🎭 {secim} Rolü", description=f"**Görev:** {roller[secim]}", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)

@bot.command()
async def roller(ctx):
    view = View()
    view.add_item(RollerDropdown())
    embed = discord.Embed(title="🎭 Xandrel Roller", description="Dropdown’dan rol seçin.", color=discord.Color.orange())
    await ctx.send(embed=embed, view=view)

# ================== TICKET SİSTEMİ ==================
TICKET_CATEGORY_ID = 1401492549708943490
TICKET_PANEL_CHANNEL = 1400825550716665936
TICKET_YETKILI_ROLLERI = [
    1400217496719462574,
    1400827346159931473,
    1400501394540204032,
    1400522195389911070
]

class TicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎫 Ticket Aç", style=discord.ButtonStyle.green)

    async def callback(self, interaction: Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for role_id in TICKET_YETKILI_ROLLERI:
            role = guild.get_role(role_id)
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ticket oluşturuldu: {channel.mention}", ephemeral=True)

@bot.command()
async def ticketpanel(ctx):
    view = View()
    view.add_item(TicketButton())
    embed = discord.Embed(title="🎫 XANDREL TICKET PANEL", description="Ticket açmak için butona tıklayın.", color=discord.Color.blurple())
    await ctx.send(embed=embed, view=view)

@bot.command()
async def ticketkapat(ctx):
    if ctx.channel.name.startswith("ticket-"):
        await ctx.channel.delete()
    else:
        await ctx.send("❌ Bu komut sadece ticket kanallarında kullanılabilir.")

# ================== YARDIM KOMUTU ==================
@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="📘 XANDREL BOT KOMUTLARI",
        description=(
            "🔸 x!kurallar\n"
            "🔸 x!uyarıkitabesi\n"
            "🔸 x!spreykuralları\n"
            "🔸 x!blackmarket\n"
            "🔸 x!lojistik\n"
            "🔸 x!ittifak\n"
            "🔸 x!hasım\n"
            "🔸 x!hesaplama\n"
            "🔸 x!malfiyat\n"
            "🔸 x!malhesapla\n"
            "🔸 x!kıyafet\n"
            "🔸 x!sunucu\n"
            "🔸 x!roller\n"
            "🔸 x!gelir\n"
            "🔸 x!kasagöster\n"
            "🔸 x!ticketpanel\n"
            "🔸 x!ticketkapat"
        ),
        color=discord.Color.teal()
    )
    await ctx.send(embed=embed)

@bot.command()
async def kasasifirla(ctx):
    global gelir_toplam
    gelir_toplam = 0
    save_gelir()
    await ctx.send("🏦 Kasa başarıyla sıfırlandı. Toplam gelir artık **0₺**.")

# ================== STOK GÖSTER / DÜZENLE ==================
# ================== STOK GÖSTER ==================
@bot.command()
async def stok(ctx):
    if not mal_data:  # mal_data boşsa
        await ctx.send("📦 Stokta ürün bulunmuyor.")
        return

    stok_text = ""
    for urun, miktar in mal_data.items():
        stok_text += f"**{urun.replace('_',' ').title()}**: {miktar}\n"

    embed = discord.Embed(
        title="📦 Güncel Stok",
        description=stok_text,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

class StokModal(Modal):
    def __init__(self, urun):
        super().__init__(title=f"📦 {urun.replace('_',' ').title()} Stok Düzenleme")
        self.urun = urun
        self.miktar_input = TextInput(label="Miktar Değişimi", placeholder="Pozitif artırır, negatif azaltır", required=True)
        self.add_item(self.miktar_input)

    async def on_submit(self, interaction: Interaction):
        global mal_data
        try:
            miktar = int(self.miktar_input.value)
        except:
            await interaction.response.send_message("❌ Geçerli bir sayı girin.", ephemeral=True)
            return
        
        yeni_miktar = mal_data.get(self.urun, 0) + miktar
        if yeni_miktar < 0:
            await interaction.response.send_message(f"❌ İşlem başarısız! {self.urun.replace('_',' ').title()} stoğu 0’dan az olamaz.", ephemeral=True)
            return
        
        mal_data[self.urun] = yeni_miktar
        save_mal()
        await interaction.response.send_message(f"✅ {self.urun.replace('_',' ').title()} stoğu güncellendi. Yeni miktar: {mal_data[self.urun]}", ephemeral=True)

class StokEkleDropdown(Select):
    def __init__(self):
        # Dropdown tüm ürünleri gösterir, mal_data'dan bağımsız
        options = [discord.SelectOption(label=k.replace("_", " ").title(), value=k) for k in fiyatlar.keys()]
        super().__init__(placeholder="Stok eklemek istediğiniz ürünü seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        urun = self.values[0]
        await interaction.response.send_modal(StokModal(urun))

class StokEkleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StokEkleDropdown())

@bot.command()
async def stokekle(ctx):
    embed = discord.Embed(
        title="📦 Stok Güncelleme",
        description="Dropdown’dan ürün seçin ve ardından miktarı girin.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=StokEkleView())

STOCK_FILE = "stok.json"

# stok.json yoksa oluştur
if not os.path.exists(STOCK_FILE):
    with open(STOCK_FILE, "w") as f:
        json.dump({}, f)

def load_stock():
    with open(STOCK_FILE, "r") as f:
        return json.load(f)

def save_stock(stock):
    with open(STOCK_FILE, "w") as f:
        json.dump(stock, f, indent=4)

@bot.command()
async def kurallar(ctx):
    embed = discord.Embed(
        title="📜 XANDREL ANAYASASI - KURALLAR",
        description=(
            "**1.** İhanet affedilmez. Kanla ödenir.\n"
            "**2.** Bilgi sızdırmak, Xandrel’e kurşun sıkmaktır.\n"
            "**3.** Emir, barondan gelir. Sorgulamak yargı getirir.\n"
            "**4.** Düşmana merhamet yoktur. Sadakat ödüllendirilir.\n"
            "**5.** RP ciddiyeti korunmalı, OOC saygı zorunludur.\n\n"
            "🎙 *“Xandrel adına yaşar, Xandrel uğruna ölürüm...”*"
        ),
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed)

@bot.command()
async def uyarıkitabesi(ctx):
    embed = discord.Embed(
        title="🚫 XANDREL UYARI KİTABESİ",
        description=(
            "**1.** Aile içi düzensizlik, uygunsuz davranış anında uyarı sebebidir.\n"
            "**2.** OOC küfür, dalga geçme veya rolü sabote etme yasaktır.\n"
            "**3.** Roller arasında ciddiyet ve disiplin esastır.\n"
            "**4.** Uyarılar 3’e ulaştığında cezai işlem uygulanabilir.\n"
            "**5.** Baron veya Konsül tarafından verilen uyarılar tartışılamaz.\n\n"
            "🔔 *Kurallara uymak, Xandrel'de yaşamanın ilk şartıdır.*"
        ),
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
async def spreykuralları(ctx):
    embed = discord.Embed(
        title="🎨 XANDREL SPREY KURALLARI",
        description=(
            "**1.** Sprey sadece Xandrel’e ait bölgelerde kullanılabilir.\n"
            "**2.** Düşman spreyini silmek için RP yapılmalı ve kanıt sunulmalıdır.\n"
            "**3.** Sprey savunulmalı, bölge korunmalıdır.\n"
            "**4.** Sprey savaşları IC kalmalı, OOC'e taşmamalıdır.\n"
            "**5.** Sprey yalnızca Baron onayıyla değiştirilebilir.\n\n"
            "🖌️ *Bir sprey, bir sokak kadar değerlidir. Xandrel izi kolay silinmez.*"
        ),
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command()
async def blackmarket(ctx):
    embed = discord.Embed(
        title="💰 XANDREL BLACKMARKET FİYATLARI",
        description=(
            "**Ürün | Oyuncuya Satış | Black Market Alış**\n"
            "🔓 Lockpick – 50$ / 40$\n"
            "🛠️ Advanced Lockpick – 100$ / 80$\n"
            "🧨 Drill – 2.000$ / 1.600$\n"
            "📡 Radio – 1.000$ / 800$\n"
            "🛰️ Illegal GPS – 10.000$ / 8.000$\n"
            "⚗️ Methlab – 3.000$ / 2.400$\n"
            "🧪 Acetone – 50$ / 40$\n"
            "🔋 Lithium – 50$ / 40$\n"
            "🛡️ Armour – 4.500$ / 3.600$\n"
            "🔫 Ammo-9 – 900$ / 720$\n\n"
            "📌 Satışlar IC rol ile yapılmalı, log tutulmalıdır."
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command()
async def lojistik(ctx):
    embed = discord.Embed(
        title="📦 XANDREL LOJİSTİK – ALIM FİYATLARI",
        description=(
            "**Ürün | Lojistik Alım Fiyatı**\n"
            "🔓 Lockpick – 25$\n"
            "🛠️ Advanced Lockpick – 50$\n"
            "🧨 Drill – 1.200$\n"
            "📡 Radio – 455$\n"
            "🛰️ Illegal GPS – 4.571$\n"
            "⚗️ Methlab – 1.350$\n"
            "🧪 Acetone – 25$\n"
            "🔋 Lithium – 25$\n"
            "🛡️ Armour – 2.100$\n"
            "🔫 Ammo-9 – 420$\n\n"
            "💰 *Kâr Dağılımı: Lojistik %75 / Black Market %25*"
        ),
        color=discord.Color.dark_blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def ittifak(ctx):
    embed = discord.Embed(
        title="🤝 XANDREL İTTİFAKLARI",
        description="Şu anda aktif bir ittifakımız bulunmamaktadır.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
async def hasım(ctx):
    embed = discord.Embed(
        title="⚔️ XANDREL DÜŞMANLARI",
        description="Şu anda açık bir düşmanlığımız bulunmamaktadır.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
async def malfiyat(ctx):
    embed = discord.Embed(
        title="🧾 XANDREL MALLARI SATIŞ FİYATLARI",
        description=(
            "**🌿 Kubar Satış Fiyatları**\n"
            "▪️ 1 Seviye Kubar – 180$\n"
            "▪️ 2 Seviye Kubar – 250$\n"
            "▪️ 3 Seviye Kubar – 400$\n\n"
            "**🧪 Meth Satış Fiyatları**\n"
            "▪️ 1 Seviye Meth – 200$\n"
            "▪️ 2 Seviye Meth – 235$\n"
            "▪️ 3 Seviye Meth – 275$\n\n"
            "**🍁 Ot Satış Fiyatları**\n"
            "▪️ 1 Seviye Ot – 180$\n"
            "▪️ 2 Seviye Ot – 250$\n"
            "▪️ 3 Seviye Ot – 400$"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Sadece tabloya ait ürünler (₺)
fiyatlar = {
    "ethanol": {"alis": 250, "satis": 500},
    "meth_pills": {"alis": 250, "satis": 500},
    "lithium": {"alis": 250, "satis": 500},
    "acetone": {"alis": 250, "satis": 500},
    "ammonia": {"alis": 250, "satis": 500},
    "meth_lab_kit": {"alis": 250, "satis": 500},
    "cement": {"alis": 250, "satis": 500},
    "hydrochloric": {"alis": 250, "satis": 500},
    "gasoline": {"alis": 250, "satis": 500},
    "lockpick": {"alis": 25, "satis": 50},
    "advancedlockpick": {"alis": 500, "satis": 1000},
    "drill": {"alis": 1000, "satis": 2000},
    "radio": {"alis": 500, "satis": 1000},
    "illegal_gps": {"alis": 5000, "satis": 10000},
    "armour": {"alis": 2500, "satis": 5000},
    "ammo_9": {"alis": 700, "satis": 900}
}

def formatla(amount):
    return f"{amount:,}".replace(",", ".")

# ---------------- MODAL ----------------
class AlisSatisModal(Modal):
    def __init__(self, urunler):
        super().__init__(title="📦 Ürün Miktarlarını Girin (adet/kg)")
        self.urunler = urunler
        self.inputs = []
        for urun in urunler:
            label = urun.replace("_", " ").title().replace("Gps", "GPS")
            ti = TextInput(label=label, placeholder="0", required=False)
            self.add_item(ti)
            self.inputs.append((urun, ti))

    async def on_submit(self, interaction: Interaction):
        toplam_alis = 0
        toplam_satis = 0
        detaylar = []
        for key, field in self.inputs:
            try:
                miktar = int(field.value)
            except:
                miktar = 0
            if miktar > 0:
                alis_tutar = fiyatlar[key]["alis"] * miktar
                satis_tutar = fiyatlar[key]["satis"] * miktar
                toplam_alis += alis_tutar
                toplam_satis += satis_tutar
                ad = key.replace("_", " ").title().replace("Gps", "GPS")
                detaylar.append(f"🔹 {ad} × {miktar} → Alış: {formatla(alis_tutar)}₺ | Satış: {formatla(satis_tutar)}₺")

        embed = discord.Embed(title="📊 ALIŞ – SATIŞ HESAPLAMA", color=discord.Color.green())
        if detaylar:
            embed.add_field(name="🧾 Detaylar", value="\n".join(detaylar), inline=False)
            embed.add_field(name="📥 Toplam Alış", value=f"**{formatla(toplam_alis)}₺**", inline=True)
            embed.add_field(name="📤 Toplam Satış", value=f"**{formatla(toplam_satis)}₺**", inline=True)
            embed.add_field(name="📈 Toplam Kâr (Satış–Alış)", value=f"**{formatla(toplam_satis - toplam_alis)}₺**", inline=False)
        else:
            embed.description = "Hiçbir ürün girilmedi."

        # Embed ve satış toplamını view ile gönderiyoruz
        view = IndirimSelectView(toplam_satis)
        await interaction.response.send_message(embed=embed, view=view)

# ---------------- DROPDOWN İNDİRİM ----------------
class IndirimSelect(Select):
    def __init__(self, toplam_satis):
        self.toplam_satis = toplam_satis
        options = [
            discord.SelectOption(label="%0 İndirim", value="0"),
            discord.SelectOption(label="%5 İndirim", value="5"),
            discord.SelectOption(label="%10 İndirim", value="10"),
            discord.SelectOption(label="%20 İndirim", value="20"),
        ]
        super().__init__(placeholder="💸 İndirim seç", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        indirim_orani = int(self.values[0])
        toplam_satis_indirimli = int(self.toplam_satis * (1 - indirim_orani / 100))
        embed = discord.Embed(
            title="🧮 ALIŞ – SATIŞ HESAPLAMA (İndirimli)",
            description=f"Seçilen indirim: %{indirim_orani}\nToplam Satış: {formatla(toplam_satis_indirimli)}₺",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

class IndirimSelectView(View):
    def __init__(self, toplam_satis):
        super().__init__(timeout=None)
        self.add_item(IndirimSelect(toplam_satis))

# ---------------- ÜRÜN SEÇİM DROPDOWN ----------------
class UrunSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ethanol", value="ethanol"),
            discord.SelectOption(label="Meth Pills", value="meth_pills"),
            discord.SelectOption(label="Lithium", value="lithium"),
            discord.SelectOption(label="Acetone", value="acetone"),
            discord.SelectOption(label="Ammonia", value="ammonia"),
            discord.SelectOption(label="Meth Lab Kit", value="meth_lab_kit"),
            discord.SelectOption(label="Cement", value="cement"),
            discord.SelectOption(label="Hydrochloric", value="hydrochloric"),
            discord.SelectOption(label="Gasoline", value="gasoline"),
            discord.SelectOption(label="Lockpick", value="lockpick"),
            discord.SelectOption(label="Advanced Lockpick", value="advancedlockpick"),
            discord.SelectOption(label="Drill", value="drill"),
            discord.SelectOption(label="Radio (Telsiz)", value="radio"),
            discord.SelectOption(label="Illegal GPS", value="illegal_gps"),
            discord.SelectOption(label="Armour", value="armour"),
            discord.SelectOption(label="Ammo-9", value="ammo_9"),
        ]
        super().__init__(placeholder="🧾 Ürünleri seç (birden fazla)", min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(AlisSatisModal(self.values))

class UrunSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(UrunSelect())

# ---------------- KOMUT ----------------
@bot.command()
async def hesaplama(ctx):
    embed = discord.Embed(
        title="🧮 ALIŞ – SATIŞ HESAPLAMA",
        description="Aşağıdan ürünleri seçin, ardından miktarları girin.",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed, view=UrunSelectView())

# ================== BOT ÇALIŞTIR ==================
load_dotenv()  # .env dosyasını yükle

TOKEN = os.getenv("TOKEN")
print(TOKEN)  # token burada doğru görünmeli

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} online!')

client.run(TOKEN)
import discord
from discord.ext import commands
import sqlite3
import os
from myserver import server_on

GUILD_ID = 1339460291745812622  # แทนค่าด้วย ID จริง
ROLE_ID = 1160150386619977738  # แทนค่าด้วย ID จริง
CHANNEL_ID = 1339519103240634368  # แทนค่าด้วย ID จริง
WELCOME_CHANNEL_ID = 1160171207375716392  # แทนค่าด้วย ID จริง
STEAM_API_KEY = 17659D1B70B6884FB220D41A215EB073

# ตรวจสอบค่าที่จำเป็น
if not DISCORD_BOT_TOKEN:
    print("❌ ERROR: DISCORD_BOT_TOKEN is not set. Please check your .env file.")
    exit(1)

# ตั้งค่าบอทและ Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ฟังก์ชันบันทึกข้อมูลลง SQLite
def save_user_to_db(user_id, steam_id, character_name):
    try:
        with sqlite3.connect("user_data.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (
                user_id INTEGER PRIMARY KEY,
                steam_id TEXT NOT NULL,
                character_name TEXT NOT NULL
            )''')
            cursor.execute('''INSERT OR REPLACE INTO user_info (user_id, steam_id, character_name)
            VALUES (?, ?, ?)''', (user_id, steam_id, character_name))
            conn.commit()
    except Exception as e:
        print(f"❌ Database Error: {e}")

# Modal สำหรับลงทะเบียน
class SteamInfoModal(discord.ui.Modal, title="ลงทะเบียนรับยศ"):
    steam_id = discord.ui.TextInput(label="กรอก Steam ID", placeholder="76561198XXXXXXXXX", required=True)
    character_name = discord.ui.TextInput(label="กรอกชื่อตัวละคร", placeholder="ชื่อในเกมของคุณ", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(ROLE_ID)
        member = interaction.user

        # ตรวจสอบความถูกต้องของข้อมูล
        if len(self.steam_id.value) < 15 or not self.steam_id.value.isdigit():
            await interaction.response.send_message("❌ Steam ID ไม่ถูกต้อง! กรุณากรอกใหม่", ephemeral=True)
            return

        if len(self.character_name.value) < 3:
            await interaction.response.send_message("❌ ชื่อตัวละครต้องมีอย่างน้อย 3 ตัวอักษร", ephemeral=True)
            return

        # บันทึกข้อมูล
        save_user_to_db(member.id, self.steam_id.value, self.character_name.value)
        if role:
            await member.add_roles(role)

        # ส่ง Embed ยืนยัน
        embed = discord.Embed(
            title="🟢 ยืนยันตัวตนสำเร็จ!",
            description=f"คุณได้รับยศ **{role.name if role else 'N/A'}** เรียบร้อยแล้ว!\n\n"
                        f"🆔 **Steam ID:** `{self.steam_id.value}`\n"
                        f"🎮 **ชื่อตัวละคร:** `{self.character_name.value}`",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://example.com/welcome-image.png")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ปุ่มสำหรับเปิด Modal
class RoleButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="ลงทะเบียนรับยศ", style=discord.ButtonStyle.green)
    async def register_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SteamInfoModal())

# คำสั่ง !role สำหรับให้สมาชิกลงทะเบียน (เฉพาะแอดมิน)
@bot.command(name="role", help="ลงทะเบียนรับยศด้วย Steam ID")
@commands.has_permissions(administrator=True)  # เพิ่มการตรวจสอบว่าเป็นแอดมิน
async def role(ctx):
    embed = discord.Embed(
        title="🔰 ลงทะเบียนรับยศ",
        description="กดปุ่ม **ลงทะเบียนรับยศ** ด้านล่างเพื่อกรอกข้อมูลของคุณ!\n\n"
                    "📝 **กรุณากรอก Steam ID และชื่อตัวละครให้ถูกต้อง**",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1339519103240634368/1339857652661878837/Dark_Gray_Simple_Gaming_Logo.png?ex=67b433ad&is=67b2e22d&hm=a2c3d27e43c950d95b38a63597b9c740675e5ed2976e8aec18cd2893fd35c5a3&")
    view = RoleButton()
    await ctx.send(embed=embed, view=view)

# เมื่อบอทออนไลน์
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    print(f'✅ Connected to: {bot.guilds[0].name} (ID: {bot.guilds[0].id})')

# ฟีเจอร์ต้อนรับสมาชิกใหม่
@bot.event
async def on_member_join(member):
    try:
        welcome_channel = await bot.fetch_channel(WELCOME_CHANNEL_ID)
        embed = discord.Embed(
            title="ยินดีต้อนรับ!",
            description=f"🎉 สวัสดี {member.mention}!\nเราหวังว่าคุณจะสนุกไปกับเรา!",
            color=discord.Color.green()
        )
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        await welcome_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ ไม่สามารถส่งข้อความต้อนรับ: {e}")

# ฟีเจอร์บอกลาสมาชิก
@bot.event
async def on_member_remove(member):
    try:
        goodbye_channel = await bot.fetch_channel(WELCOME_CHANNEL_ID)
        await goodbye_channel.send(f"👋 ลาก่อน {member.mention} เราหวังว่าจะได้เจอกันใหม่!")
    except Exception as e:
        print(f"❌ ไม่สามารถส่งข้อความบอกลา: {e}")

server_on()

# รันบอท
bot.run(os.getenv('TOKEN'))

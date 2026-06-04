import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


queue_state = {} 
text_channels = {}  


ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': False,  
    'extract_flat': 'in_playlist',  
    'nocheckcertificate': True,
    'ignoreerrors': True,  
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url', '')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



async def play_next(guild, voice_client):
    guild_id = guild.id
    if guild_id in queue_state and len(queue_state[guild_id]) > 0:
        next_song = queue_state[guild_id].pop(0)  # Pobiera i usuwa pierwszy utwór z listy

        try:
            player = await YTDLSource.from_url(next_song['url'], loop=bot.loop, stream=True)

            
            def after_playing(error):
                if error:
                    print(f"Błąd odtwarzania: {error}")
                fut = asyncio.run_coroutine_threadsafe(play_next(guild, voice_client), bot.loop)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Błąd uruchamiania następnego utworu: {e}")

            voice_client.play(player, after=after_playing)

           
            channel = text_channels.get(guild_id)
            if channel:
                source_emoji = "☁️ SoundCloud" if "soundcloud" in player.webpage_url else "📺 YouTube"
                await channel.send(f'▶️ Teraz gram z kolejki: **{player.title}** ({source_emoji})')

        except Exception as e:
            channel = text_channels.get(guild_id)
            if channel:
                await channel.send(f"❌ Wystąpił błąd przy odtwarzaniu kolejnego utworu. Pomijam...")
            await play_next(guild, voice_client)  
    else:
      
        channel = text_channels.get(guild_id)
        if channel:
            await channel.send("⏹️ Kolejka jest pusta. Zakończono odtwarzanie.")


@bot.event
async def on_ready():
    MY_GUILD = discord.Object(id=854701914041745438)
    bot.tree.copy_global_to(guild=MY_GUILD)
    await bot.tree.sync(guild=MY_GUILD)

    print(f'Zalogowano jako {bot.user}!')
    print('Slash komendy zostały zsynchronizowane na Twoim serwerze.')

@bot.tree.command(name="play", description="Odtwarza muzykę lub playlistę z YouTube/SoundCloud")
@app_commands.describe(
    zapytanie="Link do utworu, PLAYLISTY lub nazwa",
    platforma="Gdzie chcesz wyszukać utwór? (Domyślnie YouTube)"
)
@app_commands.choices(platforma=[
    app_commands.Choice(name="YouTube", value="yt"),
    app_commands.Choice(name="SoundCloud", value="sc")
])
async def play(interaction: discord.Interaction, zapytanie: str, platforma: app_commands.Choice[str] = None):
    await interaction.response.defer()

    if not interaction.user.voice:
        await interaction.followup.send("❌ Musisz najpierw dołączyć do kanału głosowego!")
        return
    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    if not voice_client:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    guild_id = interaction.guild.id
    if guild_id not in queue_state:
        queue_state[guild_id] = []
    text_channels[guild_id] = interaction.channel

    query = zapytanie
    if not zapytanie.startswith(("http://", "https://")):
        query = f"scsearch:{zapytanie}" if (platforma and platforma.value == "sc") else f"ytsearch1:{zapytanie}"

    try:
        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
        if 'entries' in data:
            entries = list(data['entries'])
            for entry in entries:
                if entry:
                    vid_url = entry.get('webpage_url') or entry.get('url')
                    vid_title = entry.get('title', 'Nieznany tytuł')
                    queue_state[guild_id].append({'url': vid_url, 'title': vid_title})

            if len(entries) > 1:
                await interaction.followup.send(f"📋 Dodano **{len(entries)}** utworów z playlisty do kolejki!")
            else:
                await interaction.followup.send(f"🎵 Dodano do kolejki: **{entries[0].get('title')}**")
        else:
            vid_url = data.get('webpage_url') or data.get('url')
            vid_title = data.get('title', 'Nieznany tytuł')
            queue_state[guild_id].append({'url': vid_url, 'title': vid_title})
            await interaction.followup.send(f"🎵 Dodano do kolejki: **{vid_title}**")
        if not voice_client.is_playing() and not voice_client.is_paused():
            await play_next(interaction.guild, voice_client)

    except Exception as e:
        await interaction.followup.send(f"❌ Wystąpił błąd: {str(e)}")


@bot.tree.command(name="skip", description="Pomija obecnie odtwarzany utwór")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("⏭️ Pominięto utwór!")
    else:
        await interaction.response.send_message("Nie ma czego pominąć. Muzyka nie gra.")


@bot.tree.command(name="queue", description="Wyświetla aktualną kolejkę utworów")
async def queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id not in queue_state or len(queue_state[guild_id]) == 0:
        await interaction.response.send_message("Kolejka jest aktualnie pusta.")
        return
    kolejka = queue_state[guild_id]
    lista_tekst = []
    for i, utwor in enumerate(kolejka[:10], start=1):
        lista_tekst.append(f"{i}. **{utwor['title']}**")

    tekst = "🎶 **Obecna kolejka:**\n" + "\n".join(lista_tekst)
    if len(kolejka) > 10:
        tekst += f"\n\n*...i {len(kolejka) - 10} kolejnych.*"
    await interaction.response.send_message(tekst)


@bot.tree.command(name="stop", description="Zatrzymuje muzykę, CZYŚCI KOLEJKĘ i wychodzi")
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in queue_state:
        queue_state[guild_id].clear()

    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        voice_client.stop()
        await voice_client.disconnect()
        await interaction.response.send_message("👋 Zatrzymano muzykę, wyczyszczono kolejkę i opuszczono kanał.")
    else:
        await interaction.response.send_message("Nie jestem na żadnym kanale głosowym.")


@bot.tree.command(name="pause", description="Pauzuje aktualnie odtwarzany utwór")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("⏸️ Zapauzowano muzykę.")
    else:
        await interaction.response.send_message("Obecnie nie gra żadna muzyka.")


@bot.tree.command(name="resume", description="Wznawia odtwarzanie utworu")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("▶️ Wznowiono odtwarzanie.")
    else:
        await interaction.response.send_message("Muzyka nie jest zapauzowana.")


@bot.tree.command(name="czysc_bota", description="Usuwa ostatnie wiadomości bota z tego kanału")
async def czysc_bota(interaction: discord.Interaction, limit: int = 10):
    await interaction.response.defer(ephemeral=True)

    def to_ja(wiadomosc):
        return wiadomosc.author == interaction.client.user

    usuniete = await interaction.channel.purge(limit=limit, check=to_ja)
    await interaction.followup.send(f"Gotowe! Usunięto {len(usuniete)} moich wiadomości.", ephemeral=True)

bot.run("")# Wstaw tutaj token swojego bota

# Bot Muzyczny Discord

Prosty bot muzyczny do Discorda napisany w Pythonie. Odtwarza utwory i playlisty z YouTube oraz SoundCloud, prowadzi kolejkę i pozwala sterować muzyką przez komendy slash.

## Funkcje

- odtwarzanie muzyki z YouTube i SoundCloud
- wyszukiwanie utworów po nazwie
- kolejka odtwarzania z automatycznym przechodzeniem do następnego utworu
- pauza, wznowienie, skip i stop
- czyszczenie wiadomości bota z kanału

## Wymagania

- Python 3.10 lub nowszy
- biblioteka `discord.py`
- `yt-dlp`
- `ffmpeg`

## Instalacja

1. Sklonuj repozytorium:

   ```bash
   git clone https://github.com/Xszklanaa/Bot-muzyczny-discord.git
   cd Bot-muzyczny-discord
   ```

2. Zainstaluj zależności:

   ```bash
   pip install -U discord.py yt-dlp
   ```

3. Upewnij się, że `ffmpeg` jest dostępny w systemie i dodany do `PATH`.

4. W pliku `bot.py` wstaw token swojego bota w miejscu `bot.run("")`.

5. Uruchom aplikację:

   ```bash
   python bot.py
   ```

## Komendy

- `/play` - odtwarza utwór lub playlistę z YouTube/SoundCloud
- `/skip` - pomija aktualny utwór
- `/queue` - pokazuje kolejkę
- `/stop` - zatrzymuje muzykę, czyści kolejkę i rozłącza bota
- `/pause` - pauzuje odtwarzanie
- `/resume` - wznawia odtwarzanie
- `/czysc_bota` - usuwa ostatnie wiadomości bota z kanału

## Uwagi

- Bot synchronizuje komendy slash do konkretnego serwera ustawionego w kodzie.
- W repozytorium nie trzymam `ffmpeg.exe`, bo jest wykluczony przez `.gitignore`.

## Licencja

Brak przypisanej licencji. Jeśli chcesz, możesz dodać własną przed publikacją.
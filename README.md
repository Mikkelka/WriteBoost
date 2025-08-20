# WriteBoost

[![Python](https://img.shields.io/badge/python-v3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Windows](https://img.shields.io/badge/Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](#licens)

**AI-drevet skriveasssistent til Windows - optimér dit skriveri overalt på systemet**

WriteBoost er en Apple Intelligence-inspireret applikation til Windows, der giver dig adgang til Google's Gemini AI overalt på dit system. Med et enkelt tastaturkombination kan du rette grammatik, omskrive tekst, opsummere indhold og meget mere - direkte i enhver applikation.

## ⚡ Hvad kan WriteBoost?

### 🔧 Direkte Teksterstatning (Grå Knapper)
- Vælg vilkårlig tekst på din PC og aktiver WriteBoost med `Ctrl+Space`
- Vælg **Korrektur**, **Omskriv**, **Venlig**, **Professionel**, **Koncis**, **Brugerdefineret** eller **Oversæt til Dansk**
- Din tekst erstattes øjeblikkeligt med den AI-optimerede version. Brug `Ctrl+Z` for at fortryde
- **Visuelt Hint:** Grå knapper indikerer operationer, der erstatter tekst direkte

### 💬 Chat-operationer (Blå Knapper)
- Vælg tekst og vælg **Resumé**, **Nøglepunkter** eller **Tabel** for interaktive analysevindue
- Få smuk markdown-formatering med chat-funktionalitet til opfølgende spørgsmål
- **Visuelt Hint:** Blåtonede knapper indikerer operationer, der åbner interaktive chat-vinduer

### 🤖 Chat-tilstand
- Tryk `Ctrl+Space` uden at vælge tekst for at starte en samtale med Gemini AI
- Vælg mellem forskellige modeller og tænkeniveauer for optimal ydeevne
- Dynamisk tænkning: AI'en beslutter, hvornår den skal tænke for bedre svar
- Gem og fortsæt samtaler med indbygget chat-historik
- Real-time modelskift inden for samtaler

## 🚀 Installation & Opsætning

### Krav
- Windows (testet på Windows 10/11)
- Python 3.8 eller nyere
- Google Gemini API-nøgle (gratis fra [Google AI Studio](https://aistudio.google.com/app/apikey))

### Installation
1. **Installer Python-dependencies:**
   ```bash
   cd Windows
   pip install -r requirements.txt
   ```

2. **Kør applikationen:**
   ```bash
   python main.py
   ```

3. **Opsæt Gemini API:**
   - Hent din gratis API-nøgle fra [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Indtast den i opsætningsvinduet, der vises ved første opstart
   - Konfigurer separate modeller til chat (Gemini 2.5 Flash) og tekstoperationer (Gemini 2.5 Flash Lite) for optimal ydeevne

## 🛠️ Teknologier

Dette projekt er bygget med følgende teknologier:

- **Python 3.8+** - Hovedprogrammeringssprog
- **PySide6 (Qt)** - GUI-framework til brugergrænsefladen
- **Google Gemini AI** - AI-provider til tekstprocessering og chat
- **pynput** - Global hotkey-detektion og tastatur simulation
- **pyperclip** - Udklipsholder-operationer til teksthåndtering
- **markdown2** - Markdown-rendering i svarvinduerne
- **PyInstaller** - Til oprettelse af selvstændige eksekverbare filer

## 🎯 Operationer Forklaret

### 🔧 Direkte Teksterstatning (Grå Knapper)
- **Korrektur:** Grammatik- og stavekontrol
- **Omskriv:** Forbedre formulering og klarhed
- **Venlig/Professionel:** Juster tonefald i din tekst
- **Koncis:** Gør tekst kortere men bevar betydningen
- **Brugerdefineret:** Dine egne kommandoer (f.eks. "Oversæt til fransk", "Tilføj kommentarer til denne kode")
- **Oversæt til Dansk:** Oversæt tekst til dansk

### 💬 Interaktive Chat-vinduer (Blå Knapper)
- **Resumé:** Opret klare og koncise resuméer med opfølgende chat
- **Nøglepunkter:** Udtræk de vigtigste punkter med analysemuligheder
- **Tabel:** Konverter tekst til formaterede markdown-tabeller (kan kopieres til MS Word) med forfiningsmuligheder

**Visuelt Design:** Operationer er farvekodede for let identifikation - blå knapper åbner chat-vinduer, grå knapper erstatter tekst direkte.

## 💡 Tips

### MS Word-brugere
`Ctrl+Space` kan konflikte med Word's "Ryd formatering". For at undgå dette:
- Skift WriteBoost' hotkey til `Ctrl+J` eller `Ctrl+\`` i indstillinger
- Eller deaktiver Word's genvej i Word > Filer > Indstillinger > Tilpas bånd > Tastaturgenveje

**Bemærk:** Word's rich-text-formatering (fed, kursiv, farver) går tabt ved brug af WriteBoost. Overvej at bruge en Markdown-editor som [Obsidian](https://obsidian.md/) for bedre kompatibilitet.

### YouTube Video-resuméer
1. Åbn en YouTube-video
2. Kopiér transskriptionen fra videobeskrivelsen
3. Vælg al tekst og brug WriteBoost "Resumé"

## 🏗️ Bygning

For at oprette en selvstændig eksekverbar fil:
```bash
cd Windows
python pyinstaller-build-script.py
```

Den eksekverbare fil oprettes i `dist/` mappen.

## 📜 Projektoprindelse

Dette projekt er oprindeligt baseret på [theJayTea/WritingTools](https://github.com/theJayTea/WritingTools), men er udviklet så meget videre, at det ikke længere kan betragtes som en fork. 

### 🔄 Væsentlige ændringer fra originalen:
- **Platform-fokus:** Fjernet macOS og Linux support, fokuseret udelukkende på Windows
- **Simplificeret arkitektur:** Omstruktureret kodebasen med manager-baseret arkitektur
- **Chat-funktionalitet:** Tilføjet komplet chat-system med Gemini AI integration
- **Chat-historik:** Persistent chatlagring med mulighed for at genoptage samtaler
- **Forbedret UI:** Redesignet brugergrænsefladen med bedre UX og visual cues
- **AI-provider system:** Modulær AI-provider arkitektur (kun Gemini understøttet)
- **Dansk lokalisering:** Tilføjet danske oversættelser og funktioner

Projektet er nu et selvstændigt værktøj med signifikant anderledes funktionalitet og arkitektur end det oprindelige.

## 🗂️ Projektstruktur

```
WriteBoost/
├── Windows/                    # Hovedapplikation
│   ├── main.py                # Indgangspunkt
│   ├── WritingToolApp.py      # Hovedapplikation
│   ├── *Manager.py            # Modulære managers (Config, Hotkey, etc.)
│   ├── *Provider.py           # AI-provider system
│   ├── ui/                    # UI-komponenter
│   │   ├── ResponseWindow.py  # Chat-vindue
│   │   ├── SettingsWindow.py  # Indstillinger
│   │   └── ...               # Øvrige UI-filer
│   ├── icons/                 # Ikoner og grafik
│   ├── options.json          # Skriveoperation-definitioner
│   └── requirements.txt      # Python-dependencies
├── CLAUDE.md                 # Projekt-dokumentation
└── README.md                 # Denne fil
```

## 🔒 Privatliv

WriteBoost respekterer dit privatliv:
- Indsamler eller gemmer ikke dine skrivedata
- Sender kun tekst til Google's Gemini API, når du eksplicit bruger en funktion
- API-nøgle gemmes lokalt på din enhed
- Chat-historik kan gemmes lokalt (valgfrit) eller slettes, når vinduer lukkes
- Alle data forbliver på din enhed, medmindre eksplicit sendt til AI

Se [Google's Privatlivspolitik](https://policies.google.com/privacy) for information om data sendt til Gemini.

## 🐞 Kendte Problemer

1. **Hotkey virker ikke:** Prøv at skifte til `Ctrl+J` eller `Ctrl+\`` i indstillinger og genstart
2. **Langsom første opstart:** Antivirus-software kan scanne den eksekverbare fil grundigt ved første kørsel

## 🤝 Bidrag

Vi modtager gerne bidrag til WriteBoost! Sådan kan du hjælpe:

1. **Rapporter fejl:** Åbn et issue hvis du finder bugs eller problemer
2. **Foreslå forbedringer:** Del dine idéer til nye funktioner
3. **Send pull requests:** Bidrag med kode-forbedringer eller fejlrettelser
4. **Forbedre dokumentation:** Hjælp med at gøre dokumentationen bedre

**Forventninger til kodekvalitet:**
- Følg eksisterende kodestil og konventioner
- Test dine ændringer grundigt
- Inkluder relevante kommentarer hvor nødvendigt

## 📄 Licens

**[LICENS MANGLER - SKAL TILFØJES]**

Dette projekt mangler i øjeblikket en licens. Det anbefales at tilføje en MIT eller Apache 2.0 licens for at specificere, hvordan andre må bruge koden.

## 📞 Kontakt

For spørgsmål eller support:
- **GitHub Issues:** [Opret et issue](../../issues) for fejlrapporter eller funktionsanmodninger
- **Projektvedligeholder:** [TILFØJ KONTAKTINFORMATION HER]

---

**Lavet af Mikkel** • Drevet af Google Gemini AI • Inspireret af Apple Intelligence • Oprindeligt baseret på [theJayTea/WritingTools](https://github.com/theJayTea/WritingTools)
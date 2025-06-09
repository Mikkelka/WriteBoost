# Writing Tools (Gemini Edition)

**Instantly proofread and optimize your writing system-wide with AI**

Writing Tools is an Apple Intelligence-inspired application for Windows that supercharges your writing with Google's Gemini AI. With one hotkey press system-wide, it lets you fix grammar, optimize text, summarize content, and more.

## ⚡ What can Writing Tools do?

### Writing Tools:
- Select any text on your PC and invoke Writing Tools with `Ctrl+Space`
- Choose **Proofread**, **Rewrite**, **Friendly**, **Professional**, **Concise**, or **Custom Instructions**
- Your text will instantly be replaced with the AI-optimized version. Use `Ctrl+Z` to revert.

### Content Summarization:
- Select text from webpages, documents, emails, etc. with `Ctrl+A`
- Choose **Summary**, **Key Points**, or **Table** after invoking Writing Tools
- Get a pop-up summary with beautiful markdown formatting
- Chat with the summary if you'd like to learn more

### Chat Mode:
- Press `Ctrl+Space` without selecting text to start a conversation with Gemini AI
- Chat history is deleted when you close the window for privacy

## 🚀 Installation & Setup

### Requirements:
- Windows (tested on Windows 10/11)
- Python 3.8 or later
- Google Gemini API key (free from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation:
1. **Install Python dependencies:**
   ```bash
   cd Windows
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **Setup Gemini API:**
   - Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Enter it in the setup window that appears on first launch

## 🎯 Options Explained

**Direct Text Replacement:**
- **Proofread:** Grammar & spelling correction
- **Rewrite:** Improve phrasing and clarity
- **Friendly/Professional:** Adjust tone of your text
- **Concise:** Make text shorter while keeping meaning
- **Custom Instructions:** Your own commands (e.g., "Translate to French", "Add comments to this code")

**Pop-up Window (with chat capability):**
- **Summarize:** Create clear and concise summaries
- **Key Points:** Extract the most important points
- **Table:** Convert text into formatted tables (copy-pastable to MS Word)

## 💡 Tips

### MS Word Users:
The `Ctrl+Space` shortcut may conflict with Word's "Clear Formatting". To avoid this:
- Change Writing Tools hotkey to `Ctrl+J` or `Ctrl+\`` in Settings
- Or disable Word's shortcut in Word > File > Options > Customize Ribbon > Keyboard Shortcuts

**Note:** Word's rich-text formatting (bold, italics, colors) will be lost when using Writing Tools. Consider using a Markdown editor like [Obsidian](https://obsidian.md/) for better compatibility.

### YouTube Video Summaries:
1. Open a YouTube video
2. Copy the transcript from the video description
3. Select all text and use Writing Tools "Summary"

## 🔒 Privacy

Writing Tools respects your privacy:
- Does not collect or store any of your writing data
- Only sends text to Google's Gemini API when you explicitly use a function
- API key is stored locally on your device
- Chat history is deleted when windows are closed

Refer to [Google's Privacy Policy](https://policies.google.com/privacy) for information about data sent to Gemini.

## 🐞 Known Issues

1. **Hotkey not working:** Try changing to `Ctrl+J` or `Ctrl+\`` in Settings and restart
2. **Slow first launch:** Antivirus software may scan the executable extensively on first run

## 🔧 Customization

- **Themes:** Choose between blurry gradient or plain Windows-style theme
- **Dark Mode:** Automatically detects your system theme
- **Hotkey:** Customize the global shortcut key
- **Auto-start:** Enable starting with Windows

## 🏗️ Building

To create a standalone executable:
```bash
cd Windows
python pyinstaller-build-script.py
```

The executable will be created in the `dist/` folder.
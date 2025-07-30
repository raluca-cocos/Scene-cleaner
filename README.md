# Scene Cleaner for Autodesk Maya

**Scene Cleaner** is a powerful script designed to streamline your Maya workflow! From quick scene tidying to optimized exports for game engines and online sharing. Whether you're working under tight deadlines or prepping assets for export to another program, this tool helps you stay organized with minimal hassle.
---

## Perfect For:
- Quick scene organization under tight deadlines
- Effortless separate mesh exports, ideal for moving assets into another program
- Streamlined full-scene exports, great for sharing work online

---

## Key Features:
- Add custom prefixes/suffixes to object names for better control
- Clear construction history with user-defined exceptions
- Export selected or full scenes to FBX or OBJ with ease
- Automatically creates a backup of your original file for peace of mind

---

## Installation & Setup

1. **Download or clone** this repository.
2. **Copy the script files** into your Maya scripts directory:
   - **Windows:** `Documents/maya/scripts`
   - **macOS:** `~/Library/Preferences/Autodesk/maya/scripts`
   - **Linux:** `~/maya/scripts`
3. **Add a shelf button** for quick access:
   - Open Maya and go to a shelf tab.
   - **Right-click** the shelf → **New Shelf Button**.
   - In the Python tab, paste:

     ```
     import Scene_cleaner as script
     import imp
     imp.reload(script)
     ```

   - Set the icon to the included `scene_cleaner_icon.png` (found in the repo).

---

## License

MIT License — feel free to use, modify, and share!

---

## Author

Made by [Raluca Cocos](https://github.com/raluca-cocos) — check out my other work on [ArtStation](https://www.artstation.com/ralucacocos)!

---

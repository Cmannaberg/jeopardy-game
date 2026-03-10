# Jeopardy Game (Flask)

A customizable Jeopardy-style game built with Flask.

## Features

- Theme/category question board
- Multi-player score tracking
- Photo clue support with auto-generated thumbnails
- JSON-based question database for easy editing
- CLI helper tools for adding/removing clues and refreshing thumbnails

## Project Structure

- `flask_app.py` - main Flask web app
- `questions_db.json` - question database
- `photos/` - original full-size images
- `thumbnails/` - generated thumbnail images
- `templates/` - HTML templates
- `manage_questions.py` - CLI utility for question/media management

## Requirements

- Python 3.10+
- macOS, Linux, or Windows
- Python packages in [requirements.txt](requirements.txt)

## Quick Start

1. Clone repository:

```bash
git clone https://github.com/Cmannaberg/jeopardy-game.git
cd jeopardy-game/jeopardy
```

2. Create and activate virtual environment:

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run app:

```bash
python flask_app.py
```

5. Open browser:

- http://127.0.0.1:5000

## Managing Questions and Photos

### List clues in a category (with indices)

```bash
python manage_questions.py list-category "Level I" "Photo Clues"
```

### Add a photo clue

Copies the image into `photos/`, adds the clue to JSON, and generates a matching thumbnail.

```bash
python manage_questions.py add-photo-clue "Level I" "Photo Clues" \
  --source "/full/path/to/image.jpeg" \
  --clue "What object is shown here?" \
  --difficulty 2
```

### Remove a photo clue and optionally delete files

```bash
python manage_questions.py remove-photo-clue "Level I" "Photo Clues" --index 2 --delete-files
```

### Refresh thumbnails

Refresh all:

```bash
python manage_questions.py refresh-thumbnails
```

Refresh one:

```bash
python manage_questions.py refresh-thumbnails --filename "kippah.jpeg"
```

## Notes

- Keep original images in `photos/`.
- Thumbnails in `thumbnails/` are generated from `photos/`.
- If you edit `questions_db.json`, restart the app if it is already running.

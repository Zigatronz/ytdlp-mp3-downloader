import re, pathlib, os

# Characters that should be normalized to a dash when found in titles
REPLACE_WITH_DASH = r'[◉•●○▪–—·••]'

# Broad emoji pattern to strip common emoji codepoints
EMOJI_PATTERN = re.compile("["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+", flags=re.UNICODE)

def clean_title(text: str) -> str:
    # 1. Remove anything inside round, square, or curly brackets
    text = re.sub(r'[\(\[\{].*?[\)\]\}]', '', text)
    
    # 2. Remove hashtags and all connected characters up to a space
    text = re.sub(r'#\S+', '', text)
    
    # 2.1 Normalize some common bullet/special symbols to a single dash
    text = re.sub(REPLACE_WITH_DASH, '-', text)

    # 2.2 Remove emoji characters to keep filenames clean
    text = re.sub(EMOJI_PATTERN, '', text)
    
    # 3. Collapse multiple spaces into a single space
    text = re.sub(r'\s+', ' ', text)
    
    # 4. Remove characters that are not allowed in filenames (Windows-safe)
    # Replace path-unfriendly characters with a dash so the title remains readable
    text = re.sub(r'[<>:\\"/\\|\?\*\x00-\x1f]', '-', text)

    # 5. Collapse multiple spaces and dashes into a single space/dash
    text = re.sub(r'[ \t\r\n]+', ' ', text)
    text = re.sub(r'-{2,}', '-', text)
    text = re.sub(r'\s*-\s*', ' - ', text)  # normalize dash spacing

    # 6. Strip extra spaces, dots, and leading/trailing dashes
    return text.strip().strip('-').strip().strip('.')

def better_filename(original_path: str) -> str:
    base_name = pathlib.Path(original_path).stem
    cleaned_name = clean_title(base_name)
    extension = pathlib.Path(original_path).suffix

    new_filename = f"{cleaned_name}{extension}"
    new_path = os.path.join(pathlib.Path(original_path).parent, new_filename)

    return new_path

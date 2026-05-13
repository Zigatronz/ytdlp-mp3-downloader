import re, pathlib, os

def clean_title(text: str) -> str:
    # 1. Remove anything inside round, square, or curly brackets
    text = re.sub(r'[\(\[\{].*?[\)\]\}]', '', text)
    
    # 2. Remove hashtags and all connected characters up to a space
    text = re.sub(r'#\S+', '', text)
    
    # 3. Collapse multiple spaces into a single space
    text = re.sub(r'\s+', ' ', text)
    
    # 4. Strip extra spaces, trailing/leading dashes, and clean edges again
    return text.strip().strip('-').strip()

def better_filename(original_path: str) -> str:
    base_name = pathlib.Path(original_path).stem
    cleaned_name = clean_title(base_name)
    extension = pathlib.Path(original_path).suffix

    new_filename = f"{cleaned_name}{extension}"
    new_path = os.path.join(pathlib.Path(original_path).parent, new_filename)

    return new_path

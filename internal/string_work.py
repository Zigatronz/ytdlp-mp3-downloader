
import re

def _remove_brackets(text: str, start: str, end: str) -> tuple:
    """
    Removes any content within specified brackets from the input string.
    Returns the cleaned text and a list of removed bracket contents.
    
    Args:
        text (str): The input string to process.
        start (str): The starting bracket character (e.g., '(', '[').
        end (str): The ending bracket character (e.g., ')', ']').
    
    Returns:
        tuple: (cleaned_text, list_of_removed_items)
    """
    # Escape the start and end characters for regex if they are special characters
    start_escaped = re.escape(start)
    end_escaped = re.escape(end)
    
    # Find all matches
    matches = re.findall(rf'{start_escaped}.*?{end_escaped}', text)
    
    # Remove content within the specified brackets, including the brackets themselves
    cleaned_text = re.sub(rf'{start_escaped}.*?{end_escaped}', '', text)
    return cleaned_text.strip(), matches

def remove_parentheses_brackets(text: str) -> tuple:
    """
    Removes any content within parentheses '()' and square brackets '[]' from the input string.
    Returns the cleaned text and a list of removed items.
    
    Args:
        text (str): The input string to process.
    Returns:
        tuple: (cleaned_text, list_of_removed_items)
    """
    text, popped_paren = _remove_brackets(text, '(', ')')
    text, popped_square = _remove_brackets(text, '[', ']')
    return text.strip(), popped_paren + popped_square

def remove_square_brackets(text: str) -> tuple:
    """
    Removes any content within square brackets '[]' from the input string.
    Returns the cleaned text and a list of removed items.
    
    Args:
        text (str): The input string to process.
    
    Returns:
        tuple: (cleaned_text, list_of_removed_items)
    """
    return _remove_brackets(text, '[', ']')

def remove_curly_braces(text: str) -> tuple:
    """
    Removes any content within curly braces '{}' from the input string.
    Returns the cleaned text and a list of removed items.
    
    Args:
        text (str): The input string to process.
    Returns:
        tuple: (cleaned_text, list_of_removed_items)
    """
    return _remove_brackets(text, '{', '}')

def remove_angle_brackets(text: str) -> tuple:
    """
    Removes any content within angle brackets '<>' from the input string.
    Returns the cleaned text and a list of removed items.
    
    Args:
        text (str): The input string to process.
    Returns:
        tuple: (cleaned_text, list_of_removed_items)
    """
    return _remove_brackets(text, '<', '>')

def remove_hashtags(text: str) -> tuple:
    """
    Removes all hashtags (words starting with #) from the input string.
    Returns the cleaned text and a list of removed hashtags.
    
    Args:
        text (str): The input string to process.
    
    Returns:
        tuple: (cleaned_text, list_of_hashtags)
    """
    hashtags = [word for word in text.split() if word.startswith('#')]
    cleaned = ' '.join(word for word in text.split() if not word.startswith('#')).strip()
    return cleaned, hashtags

def remove_emojis(text: str) -> tuple:
    """
    Removes all emojis from the input string.
    Returns the cleaned text and a list of removed emojis.
    
    Args:
        text (str): The input string to process.
    Returns:
        tuple: (cleaned_text, list_of_emojis)
    """
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+",
        flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    cleaned = emoji_pattern.sub(r'', text).strip()
    return cleaned, emojis

def remove_extra_whitespace(text: str) -> tuple:
    """
    Removes extra whitespace from the input string, leaving only single spaces between words.
    Returns the cleaned text and a list of removed whitespace sequences.
    
    Args:
        text (str): The input string to process.
    Returns:
        tuple: (cleaned_text, list_of_removed_whitespace)
    """
    extra_whitespace = re.findall(r'\s{2,}', text)
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned, extra_whitespace



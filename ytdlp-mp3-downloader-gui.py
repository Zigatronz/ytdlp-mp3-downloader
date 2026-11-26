import sys
from internal.gui import gui
from internal.logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Launching YTDLP MP3 Downloader Desktop Environment...")
    
    try:
        app_gui = gui()
        app_gui.init_ui()
        
    except Exception as e:
        logger.error(f"Critical application failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

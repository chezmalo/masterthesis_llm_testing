import os, logging
from rich.console import Console
from rich.logging import RichHandler

LOG_FILE = "outputs/llm_tests.log"

def setup(level: str = "INFO", write_file: bool = True) -> logging.Logger:
    lvl = getattr(logging, level.upper(), logging.INFO)

    # Konsole mit Rich
    console = Console()
    handlers = [RichHandler(console=console, show_time=True, markup=True)]

    # Optional zusätzlich Datei-Log (Append = Standard)
    if write_file:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8", delay=True)
        fh.setLevel(lvl)
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        handlers.append(fh)

    # Einmalig am Programmanfang aufrufen
    logging.basicConfig(level=lvl, format="%(message)s", handlers=handlers)
    return logging.getLogger("llm_tests")

logger = setup()
import logging

logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# File handler — always writes INFO and above
_fh = logging.FileHandler("app.log")
_fh.setLevel(logging.INFO)
_fh.setFormatter(_fmt)

# Console handler — shows DEBUG and above so you see everything while running
_ch = logging.StreamHandler()
_ch.setLevel(logging.DEBUG)
_ch.setFormatter(_fmt)

logger.addHandler(_fh)
logger.addHandler(_ch)
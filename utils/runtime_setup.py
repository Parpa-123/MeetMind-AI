import logging
import os
import warnings


def configure_runtime() -> None:
    # Reduce noisy advisory logs from transformers dynamic modules.
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    logging.getLogger("transformers").setLevel(logging.ERROR)

    warnings.filterwarnings(
        "ignore",
        message=r".*Accessing `__path__` from `\.models\..*",
    )

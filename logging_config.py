import logging


def configure_vfe_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.

    :param verbose: Whether to enable verbose logging.
    """
    level = logging.INFO if verbose else logging.WARNING

    logging.basicConfig(
        level=level,
        format="[VFE] %(message)s",
        handlers=[logging.StreamHandler()]
    )

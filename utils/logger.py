#!/usr/bin/env python3
"""Logging setup for NightX."""
import logging

def setup_logger(level: int = logging.WARNING):
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("nightx")

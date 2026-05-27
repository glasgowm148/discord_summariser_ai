#!/usr/bin/env python3
"""Main entry point for Discord chat summarisation."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.app_config import AppConfig
from services.summary_workflow import SummaryWorkflow
from utils.logging_config import setup_logging


async def main() -> None:
    setup_logging()
    config = AppConfig.load()
    config.require_core_summary()
    await SummaryWorkflow(config).run()


if __name__ == "__main__":
    asyncio.run(main())

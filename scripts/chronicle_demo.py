import sys
import os
import asyncio
import json
import argparse
from typing import List

# Add src and project root to path for cross-script and package imports
script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(script_dir) # Add current dir for local imports (like sync_to_obsidian)
sys.path.append(os.path.abspath(os.path.join(script_dir, '../src'))) # Add src for framework packages
sys.path.append(os.path.abspath(os.path.join(script_dir, '..'))) # Add root for others
File unchanged since last read. The content from the earlier read_file result in this conversation is still current — refer to that instead of re-reading.
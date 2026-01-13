# search_core.py

"""
注意：
此文件并无实际内容，仅展示源文件结构，直接下载 github release 中的exe文件使用此工具即可
"""


import os
import sys
import json
import sqlite3
import matplotlib
from import_from_api import main as update_db
from ui_code import explore_plans_ui
import traceback
from dataclasses import dataclass, field
from typing import FrozenSet, List, Dict, Tuple, Optional, Set, Mapping, Literal

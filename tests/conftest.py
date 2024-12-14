import sys
import os

# Add the 'src' directory to sys.path so that tests can find the source code
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)
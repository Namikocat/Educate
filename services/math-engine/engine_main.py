"""PyInstaller entry point for the bundled math-engine sidecar."""
import multiprocessing

from unilearn_math.server import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

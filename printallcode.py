#!/usr/bin/env python3
import os

def concatenate_files_and_directories(file_paths, output_file):
    """
    Concatenates the contents of specific files and all files inside given directories
    into a single output file. Adds a comment with the file path before the content of each file.
    Skips __pycache__ directories.
    """
    try:
        with open(output_file, 'w', encoding='utf-8', errors='replace') as outfile:
            for path in file_paths:
                if os.path.isdir(path):
                    # If the path is a directory, walk through it recursively
                    for dirpath, dirnames, filenames in os.walk(path):
                        # Skip __pycache__ directories
                        dirnames[:] = [d for d in dirnames if d != '__pycache__']
                        for filename in filenames:
                            file_path = os.path.join(dirpath, filename)
                            # Add the file path as a comment
                            outfile.write(f"# File: {file_path}\n")
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                                    outfile.write(infile.read())
                                    outfile.write("\n\n")  # Add spacing between files
                                print(f"Added {file_path} to {output_file}")
                            except Exception as e:
                                print(f"Error reading file {file_path}: {e}")
                elif os.path.isfile(path):
                    # If the path is a file, add it directly with the file path as a comment
                    outfile.write(f"# File: {path}\n")
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as infile:
                            outfile.write(infile.read())
                            outfile.write("\n\n")  # Add spacing between files
                        print(f"Added {path} to {output_file}")
                    except Exception as e:
                        print(f"Error reading file {path}: {e}")
                else:
                    print(f"Path {path} not found.")
    except Exception as e:
        print(f"Error concatenating files: {e}")

def main():
    # File and directory paths for frontend
    frontend_paths = [
        "/home/jack/ayyaihome/frontend/src/components",
        "/home/jack/ayyaihome/frontend/src/hooks",
        "/home/jack/ayyaihome/frontend/src/services",
        "/home/jack/ayyaihome/frontend/src/App.js",
        "/home/jack/ayyaihome/frontend/src/MessageLogic.js",
        "/home/jack/ayyaihome/frontend/tailwind.config.js",
        "/home/jack/ayyaihome/frontend/src/index.css"
    ]

    # File and directory paths for backend
    backend_paths = [
        "/home/jack/ayyaihome/backend/endpoints",
        "/home/jack/ayyaihome/backend/services",
        "/home/jack/ayyaihome/backend/app.py",
        "/home/jack/ayyaihome/backend/init.py",
        "/home/jack/ayyaihome/backend/websocket_manager.py"
    ]

    # Output file paths
    frontend_output = "/home/jack/ayyaihome/allfrontendcode.txt"
    backend_output = "/home/jack/ayyaihome/allbkndcode.txt"

    # Concatenate frontend files and directories
    concatenate_files_and_directories(frontend_paths, frontend_output)

    # Concatenate backend files and directories, skipping __pycache__
    concatenate_files_and_directories(backend_paths, backend_output)

if __name__ == "__main__":
    main()

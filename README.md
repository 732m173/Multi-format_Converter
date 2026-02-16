# Multi-Format Media Converter

A powerful and modular **multi-format converter** built with **Python**, leveraging professional-grade libraries and **FFmpeg** for high-quality processing.

---

## Overview
This tool is designed to handle complex media and data transformations. By combining the flexibility of Python with the raw power of **FFmpeg**, it provides a robust solution for developers needing reliable conversions.

## Requirements & Dependencies

To run this converter, you need the following:

### 1. Python Libraries
Install the necessary modules via pip:
pip install -r requirements.txt

### 2. FFmpeg.exe
For Windows, place FFmpeg.exe in the folders

### 3. Compilation
run the command (no console) : PyInstaller --noconsole --onefile --add-data "ffmpeg.exe;." --hidden-import=docx2pdf convert.py
run the command : PyInstaller --onefile --add-data "ffmpeg.exe;." --hidden-import=docx2pdf convert.py

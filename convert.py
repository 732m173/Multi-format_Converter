import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import subprocess
import threading
import os
import sys
import cv2
import ezdxf
import numpy as np
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from docx2pdf import convert as convert_doc

FORMATS = {
    'image': {
        'inputs': ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.ico'],
        'outputs': ['jpg', 'png', 'webp', 'pdf', 'ico', 'bmp', 'dxf']
    },
    'video': {
        'inputs': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm'],
        'outputs': ['mp4', 'avi', 'mkv', 'mp3 (Audio)', 'gif']
    },
    'audio': {
        'inputs': ['.mp3', '.wav', '.aac', '.flac', '.ogg'],
        'outputs': ['mp3', 'wav', 'flac']
    },
    'document': {
        'inputs': ['.docx'],
        'outputs': ['pdf']
    }
}

def resourcePath(relativePath):
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")
    return os.path.join(basePath, relativePath)

def detectCategory(extension):
    ext = extension.lower()
    for cat, data in FORMATS.items():
        if ext in data['inputs']:
            return cat
    return None

# Moteurs de conversion

def processImage(inputPath, outputExt):
    print(f"DEBUG: Processing Image -> {outputExt}")
    outputPath = os.path.splitext(inputPath)[0] + "_converti." + outputExt
    
    if outputExt.lower() == 'dxf':
        img_array = np.fromfile(inputPath, np.uint8)
        img_cv = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
        if img_cv is None:
            raise ValueError("Impossible de lire l'image pour la vectorisation.")
            
        edges = cv2.Canny(img_cv, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        h = img_cv.shape[0]
        
        for contour in contours:
            points = [(pt[0][0], h - pt[0][1]) for pt in contour]
            if len(points) >= 2:
                msp.add_lwpolyline(points, close=True)
                
        doc.saveas(outputPath)
        return outputPath

    img = Image.open(inputPath)
    
    # Enlève la transparence pour les formats qui ne la supportent pas
    if outputExt.lower() in ['jpg', 'jpeg', 'pdf', 'bmp']:
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if len(img.split()) == 4:
                background.paste(img, mask=img.split()[3])
            img = background
            
    if outputExt.lower() == 'ico':
        img.save(outputPath, format='ICO', sizes=[(32, 32)])
    else:
        img.save(outputPath)
        
    return outputPath

def processMedia(inputPath, outputExt):
    print(f"DEBUG: Processing Media -> {outputExt}")
    baseName = os.path.splitext(inputPath)[0]
    

    if "mp3" in outputExt and "Audio" in outputExt:
        finalExt = "mp3"
    else:
        finalExt = outputExt.split(' ')[0]

    outputPath = f"{baseName}_converti.{finalExt}"
    
    ffmpegExe = resourcePath("ffmpeg.exe")
    print(f"DEBUG: ffmpeg path -> {ffmpegExe}")
    
    if not os.path.exists(ffmpegExe):
        raise FileNotFoundError("ffmpeg.exe not found!")

    cmd = [ffmpegExe, '-y', '-i', inputPath]
    
    # Codecs configuration
    if finalExt == 'mp3':
        cmd.extend(['-vn', '-acodec', 'libmp3lame', '-q:a', '2'])
    elif finalExt == 'mp4':
        cmd.extend(['-vcodec', 'libx264', '-acodec', 'aac'])
    
    cmd.append(outputPath)
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    subprocess.run(cmd, check=True, startupinfo=startupinfo)
    return outputPath

def processDoc(inputPath, outputExt):
    print(f"DEBUG: Processing Doc -> {outputExt}")
    if outputExt == 'pdf':
        outputPath = os.path.splitext(inputPath)[0] + ".pdf"
        convert_doc(inputPath, outputPath)
        return outputPath
    return None

# Logique de l'interface

def onFileSelect():
    filename = filedialog.askopenfilename()
    if not filename: return
    
    ext = os.path.splitext(filename)[1]
    cat = detectCategory(ext)
    
    if not cat:
        messagebox.showerror("Error", "File format not supported.")
        return
    
    lbl_file['text'] = filename
    lbl_cat['text'] = f"Type : {cat.upper()}"
    
    combo_format['values'] = FORMATS[cat]['outputs']
    combo_format.current(0)
    
    root.currentCategory = cat

def runConversion():
    inputPath = lbl_file['text']
    targetFormat = combo_format.get()
    
    if inputPath == "..." or not targetFormat:
        messagebox.showwarning("Warning", "Please select a file and a format.")
        return
    
    cleanFormat = targetFormat.split(' ')[0] # "mp3 (Audio)" -> "mp3"
    
    btn_convert['state'] = 'disabled'
    lbl_status['text'] = "Work in progress..."
    
    def threadTarget():
        try:
            cat = root.currentCategory
            out = None
            
            if cat == 'image':
                out = processImage(inputPath, cleanFormat)
            elif cat in ['video', 'audio']:
                out = processMedia(inputPath, targetFormat)
            elif cat == 'document':
                out = processDoc(inputPath, cleanFormat)
            
            if out:
                lbl_status['text'] = f"Success : {os.path.basename(out)}"
                messagebox.showinfo("Success", "Conversion finished!")
            
        except Exception as e:
            lbl_status['text'] = "Error"
            print(e)
            messagebox.showerror("Error", str(e))
        finally:
            btn_convert['state'] = 'normal'
            
    threading.Thread(target=threadTarget).start()

# GUI

root = tk.Tk()
root.title("Universal Converter")
root.geometry("500x350")

tk.Label(root, text="Multi-format Converter", font=("Arial", 16, "bold")).pack(pady=10)

tk.Button(root, text="1. Choose a file", command=onFileSelect).pack()
lbl_file = tk.Label(root, text="...", fg="blue", wraplength=450)
lbl_file.pack(pady=5)

lbl_cat = tk.Label(root, text="", font=("Arial", 10, "bold"))
lbl_cat.pack()

tk.Label(root, text="2. Output format :").pack(pady=(20, 5))
combo_format = ttk.Combobox(root, state="readonly")
combo_format.pack()

btn_convert = tk.Button(root, text="3. CONVERT", command=runConversion, bg="green", fg="white", font=("Arial", 12, "bold"))
btn_convert.pack(pady=20)

lbl_status = tk.Label(root, text="Ready")
lbl_status.pack()

root.currentCategory = None
root.mainloop()

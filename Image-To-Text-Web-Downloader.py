#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🖼️  IMAGE TO TEXT & WEB IMAGE DOWNLOADER               ║
║     Complete Standalone Tool - NO External Modules Needed   ║
║     Works with Python Built-in Libraries Only               ║
║                                                              ║
║     Developed by: CHOWDHURY-VAI                             ║
║     Version: 4.1.0 - Ultimate Standalone Edition            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import re
import time
import json
import shutil
import hashlib
import base64
import threading
import platform
import tempfile
import subprocess
import ssl
import html
import urllib.request
import urllib.parse
import urllib.error
import http.client
import socket
import struct
import zlib
import gzip
import io
import math
from pathlib import Path
from io import BytesIO, StringIO
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, OrderedDict
from datetime import datetime

# ==================== TKINTER IMPORT ====================
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️  Tkinter not available. GUI mode will not work.")
    print("📦 Install tkinter: sudo apt-get install python3-tk")

# ==================== CONFIGURATION ====================
class Config:
    """Application Configuration"""
    APP_NAME = "Image To Text & Web Downloader"
    VERSION = "4.1.0"
    DEVELOPER = "CHOWDHURY-VAI"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_images")
    OUTPUT_DIR = os.path.join(BASE_DIR, "text_output")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    
    # Create directories
    for directory in [DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # Settings
    MAX_WORKERS = 10
    TIMEOUT = 30
    CHUNK_SIZE = 8192
    MAX_RETRIES = 3
    
    # Supported image formats
    IMAGE_FORMATS = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.gif': 'GIF',
        '.bmp': 'BMP',
        '.webp': 'WEBP',
        '.ico': 'ICO',
        '.tiff': 'TIFF',
        '.tif': 'TIFF',
        '.svg': 'SVG'
    }
    
    # Languages
    LANGUAGES = {
        'English': 'eng',
        'Bangla (বাংলা)': 'ben',
        'Bangla + English': 'ben+eng',
    }


# ==================== PURE PYTHON IMAGE PROCESSOR ====================
class PureImageProcessor:
    """Image processing using only built-in Python libraries"""
    
    @staticmethod
    def get_image_size(file_path):
        """Get image dimensions without external libraries"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(24)
                
                if len(header) < 2:
                    return None, None, 'UNKNOWN'
                
                # PNG
                if header[:8] == b'\x89PNG\r\n\x1a\n':
                    width, height = struct.unpack('>II', header[16:24])
                    return width, height, 'PNG'
                
                # GIF
                elif header[:6] in (b'GIF87a', b'GIF89a'):
                    width, height = struct.unpack('<HH', header[6:10])
                    return width, height, 'GIF'
                
                # BMP
                elif header[:2] == b'BM':
                    width, height = struct.unpack('<II', header[18:26])
                    return width, abs(height), 'BMP'
                
                # JPEG
                elif header[:2] == b'\xff\xd8':
                    f.seek(0)
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf or ftype in (0xc4, 0xc8, 0xcc):
                        f.seek(size, 1)
                        byte = f.read(1)
                        if not byte:
                            return None, None, 'JPEG'
                        while ord(byte) == 0xff:
                            byte = f.read(1)
                            if not byte:
                                return None, None, 'JPEG'
                        ftype = ord(byte)
                        size_bytes = f.read(2)
                        if len(size_bytes) < 2:
                            return None, None, 'JPEG'
                        size = struct.unpack('>H', size_bytes)[0] - 2
                    f.seek(1, 1)
                    dim_bytes = f.read(4)
                    if len(dim_bytes) < 4:
                        return None, None, 'JPEG'
                    height, width = struct.unpack('>HH', dim_bytes)
                    return width, height, 'JPEG'
                
                else:
                    return None, None, 'UNKNOWN'
                    
        except Exception as e:
            print(f"Error reading image: {e}")
            return None, None, 'ERROR'
    
    @staticmethod
    def get_image_info(file_path):
        """Get comprehensive image information"""
        try:
            if not os.path.exists(file_path):
                return None
            
            file_size = os.path.getsize(file_path)
            width, height, img_format = PureImageProcessor.get_image_size(file_path)
            
            info = {
                'filename': os.path.basename(file_path),
                'size': f"{width}x{height}" if width and height else "Unknown",
                'width': width,
                'height': height,
                'format': img_format,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'extension': os.path.splitext(file_path)[1].lower(),
                'created': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
            }
            return info
            
        except Exception as e:
            print(f"Error getting image info: {e}")
            return None


# ==================== PURE PYTHON WEB SCRAPER ====================
class PureWebScraper:
    """Web scraper using only built-in libraries"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,bn;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def validate_url(self, url):
        """Validate and normalize URL"""
        if not url:
            return False, url
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            result = urlparse(url)
            if result.scheme in ('http', 'https') and result.netloc:
                return True, url
            return False, url
        except:
            return False, url
    
    def fetch_url(self, url, timeout=30, retries=3):
        """Fetch URL content with retries"""
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers=self.headers)
                response = urllib.request.urlopen(
                    req, 
                    timeout=timeout,
                    context=self.ssl_context
                )
                
                content = response.read()
                encoding = response.headers.get('Content-Encoding', '').lower()
                
                if 'gzip' in encoding:
                    try:
                        content = gzip.decompress(content)
                    except:
                        pass
                elif 'deflate' in encoding:
                    try:
                        content = zlib.decompress(content)
                    except:
                        pass
                
                content_type = response.headers.get('Content-Type', '').lower()
                charset = 'utf-8'
                
                if 'charset=' in content_type:
                    try:
                        charset = content_type.split('charset=')[-1].split(';')[0].strip()
                    except:
                        pass
                
                try:
                    text = content.decode(charset, errors='ignore')
                except:
                    text = content.decode('utf-8', errors='ignore')
                
                return text
                
            except Exception as e:
                if attempt == retries - 1:
                    raise Exception(f"Failed to fetch URL: {str(e)}")
                time.sleep(1)
        
        return ""
    
    def extract_images_from_html(self, html_content, base_url):
        """Extract all image URLs from HTML content"""
        image_urls = set()
        
        # Find img tags
        img_pattern = r'<img[^>]+(?:src|data-src|data-lazy-src|data-original)=["\']([^"\']+)["\']'
        matches = re.findall(img_pattern, html_content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            if match and not match.startswith('data:'):
                full_url = urljoin(base_url, match)
                image_urls.add(full_url)
        
        # Find srcset
        srcset_pattern = r'<img[^>]+srcset=["\']([^"\']+)["\']'
        srcset_matches = re.findall(srcset_pattern, html_content, re.IGNORECASE | re.DOTALL)
        for match in srcset_matches:
            urls = re.findall(r'([^\s,]+)\s*(?:\d+[wx])?', match)
            for url in urls:
                url = url.strip()
                if url and not url.startswith('data:'):
                    full_url = urljoin(base_url, url)
                    image_urls.add(full_url)
        
        # Find CSS background images
        css_pattern = r'background(?:-image)?:\s*url\(["\']?([^"\'()]+)["\']?\)'
        css_matches = re.findall(css_pattern, html_content, re.IGNORECASE)
        for match in css_matches:
            if match and not match.startswith('data:'):
                full_url = urljoin(base_url, match)
                image_urls.add(full_url)
        
        # Find og:image
        og_pattern = r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'
        og_matches = re.findall(og_pattern, html_content, re.IGNORECASE)
        for match in og_matches:
            if match:
                full_url = urljoin(base_url, match)
                image_urls.add(full_url)
        
        # Find direct image links
        link_pattern = r'<a[^>]+href=["\']([^"\']+\.(?:jpg|jpeg|png|gif|bmp|webp|svg|ico))["\']'
        link_matches = re.findall(link_pattern, html_content, re.IGNORECASE)
        for match in link_matches:
            if match:
                full_url = urljoin(base_url, match)
                image_urls.add(full_url)
        
        # Filter valid URLs
        valid_urls = []
        for url in image_urls:
            parsed = urlparse(url)
            if parsed.scheme in ('http', 'https') and parsed.netloc:
                path = parsed.path.lower()
                is_image = any(path.endswith(ext) for ext in Config.IMAGE_FORMATS.keys())
                if is_image or self._is_likely_image(url):
                    valid_urls.append(url)
        
        return list(dict.fromkeys(valid_urls))  # Remove duplicates
    
    def _is_likely_image(self, url):
        """Check if URL likely points to an image"""
        image_indicators = ['image', 'img', 'photo', 'pic', 'picture', 'thumb', 'thumbnail']
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in image_indicators)
    
    def get_all_images(self, url):
        """Extract all image URLs from a webpage"""
        try:
            html_content = self.fetch_url(url)
            image_urls = self.extract_images_from_html(html_content, url)
            return image_urls
        except Exception as e:
            raise Exception(f"Error extracting images: {str(e)}")
    
    def download_image(self, url, save_path, quality='high'):
        """Download a single image"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            response = urllib.request.urlopen(
                req,
                timeout=Config.TIMEOUT,
                context=self.ssl_context
            )
            
            with open(save_path, 'wb') as f:
                while True:
                    chunk = response.read(Config.CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
            
            if os.path.getsize(save_path) > 0:
                return True
            else:
                if os.path.exists(save_path):
                    os.remove(save_path)
                return False
                
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def download_all_images(self, url, quality='high'):
        """Download all images from a webpage"""
        try:
            is_valid, normalized_url = self.validate_url(url)
            if not is_valid:
                raise ValueError("Invalid URL. Please enter a valid website URL.")
            
            domain = urlparse(normalized_url).netloc
            safe_domain = re.sub(r'[^\w\-_\.]', '_', domain)
            domain_dir = os.path.join(Config.DOWNLOAD_DIR, safe_domain)
            os.makedirs(domain_dir, exist_ok=True)
            
            print(f"\n🔍 Scanning: {normalized_url}")
            image_urls = self.get_all_images(normalized_url)
            
            if not image_urls:
                return {
                    'success': False,
                    'message': 'No images found on this website. Try a different URL.'
                }
            
            print(f"📸 Found {len(image_urls)} images")
            
            downloaded = []
            failed = []
            total = len(image_urls)
            
            if self.progress_callback:
                self.progress_callback(0, total)
            
            with ThreadPoolExecutor(max_workers=min(Config.MAX_WORKERS, total)) as executor:
                future_to_url = {}
                
                for i, img_url in enumerate(image_urls):
                    ext = os.path.splitext(urlparse(img_url).path)[1]
                    if not ext or ext.lower() not in Config.IMAGE_FORMATS.keys():
                        ext = '.jpg'
                    
                    filename = f"image_{i+1:04d}{ext}"
                    save_path = os.path.join(domain_dir, filename)
                    
                    counter = 1
                    while os.path.exists(save_path):
                        filename = f"image_{i+1:04d}_{counter}{ext}"
                        save_path = os.path.join(domain_dir, filename)
                        counter += 1
                    
                    future = executor.submit(self.download_image, img_url, save_path, quality)
                    future_to_url[future] = (img_url, save_path)
                
                completed = 0
                for future in as_completed(future_to_url):
                    img_url, save_path = future_to_url[future]
                    completed += 1
                    
                    if self.progress_callback:
                        self.progress_callback(completed, total)
                    
                    try:
                        if future.result():
                            downloaded.append(save_path)
                        else:
                            failed.append(img_url)
                    except:
                        failed.append(img_url)
            
            return {
                'success': True,
                'downloaded': len(downloaded),
                'failed': len(failed),
                'total': total,
                'folder': domain_dir,
                'files': downloaded,
                'failed_urls': failed
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }


# ==================== PURE OCR USING TESSERACT CLI ====================
class PureOCR:
    """OCR using Tesseract CLI - no Python module needed"""
    
    def __init__(self):
        self.tesseract_cmd = self._find_tesseract()
    
    def _find_tesseract(self):
        """Find Tesseract installation"""
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/bin/tesseract',
            '/opt/bin/tesseract',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        try:
            result = subprocess.run(['which', 'tesseract'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        
        try:
            result = subprocess.run(['where', 'tesseract'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0].strip()
        except:
            pass
        
        return None
    
    def is_available(self):
        """Check if Tesseract is available"""
        return self.tesseract_cmd is not None
    
    def get_version(self):
        """Get Tesseract version"""
        if not self.tesseract_cmd:
            return None
        
        try:
            result = subprocess.run([self.tesseract_cmd, '--version'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                match = re.search(r'(\d+\.\d+\.\d+)', version_line)
                if match:
                    return match.group(1)
        except:
            pass
        
        return None
    
    def get_languages(self):
        """Get available Tesseract languages"""
        if not self.tesseract_cmd:
            return []
        
        try:
            result = subprocess.run([self.tesseract_cmd, '--list-langs'], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                langs = [lang.strip() for lang in result.stdout.split('\n')[1:] if lang.strip()]
                return langs
        except:
            pass
        
        return []
    
    def extract_text(self, image_path, language='eng+ben'):
        """Extract text from image using Tesseract CLI"""
        if not self.tesseract_cmd:
            return ("⚠️ Tesseract OCR is not installed.\n\n"
                   "To install:\n"
                   "  sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ben\n\n"
                   "Or use: Tools > Install Tesseract in the application menu.")
        
        if not os.path.exists(image_path):
            return "Error: Image file not found."
        
        output_file = None
        try:
            # Create temp output file
            fd, output_base = tempfile.mkstemp(suffix='_ocr')
            os.close(fd)
            
            cmd = [
                self.tesseract_cmd,
                image_path,
                output_base,
                '-l', language,
                '--oem', '3',
                '--psm', '6'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            output_file = output_base + '.txt'
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                
                if text:
                    return text
            
            if result.stdout and result.stdout.strip():
                return result.stdout.strip()
            
            return "No text detected in the image. Try a clearer image."
            
        except subprocess.TimeoutExpired:
            return "Error: OCR process timed out. The image might be too large."
        except Exception as e:
            return f"Error extracting text: {str(e)}"
        finally:
            # Cleanup
            if output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            try:
                if output_base and os.path.exists(output_base + '.txt'):
                    os.remove(output_base + '.txt')
            except:
                pass
    
    def preprocess_and_extract(self, image_path, language='eng+ben'):
        """Extract text from image"""
        text = self.extract_text(image_path, language)
        return text


# ==================== AUTO TESSERACT INSTALLER ====================
class TesseractInstaller:
    """Auto-install Tesseract OCR"""
    
    @staticmethod
    def install():
        """Install Tesseract based on OS"""
        system = platform.system().lower()
        
        print("\n📦 Installing Tesseract OCR...")
        
        try:
            if system == 'linux':
                if os.path.exists('/etc/os-release'):
                    with open('/etc/os-release') as f:
                        content = f.read().lower()
                    
                    if any(d in content for d in ['ubuntu', 'debian', 'kali', 'mint', 'pop']):
                        print("Detected Debian/Ubuntu based system")
                        subprocess.run(['sudo', 'apt-get', 'update'], check=False)
                        subprocess.run([
                            'sudo', 'apt-get', 'install', '-y',
                            'tesseract-ocr', 'tesseract-ocr-eng', 'tesseract-ocr-ben'
                        ], check=False)
                        return True
                    
                    elif any(d in content for d in ['fedora', 'rhel', 'centos']):
                        print("Detected Fedora/RHEL based system")
                        subprocess.run([
                            'sudo', 'dnf', 'install', '-y',
                            'tesseract', 'tesseract-langpack-eng', 'tesseract-langpack-ben'
                        ], check=False)
                        return True
                    
                    elif any(d in content for d in ['arch', 'manjaro']):
                        print("Detected Arch based system")
                        subprocess.run([
                            'sudo', 'pacman', '-S', '--noconfirm',
                            'tesseract', 'tesseract-data-eng', 'tesseract-data-ben'
                        ], check=False)
                        return True
            
            print("\n⚠️  Could not auto-install Tesseract.")
            print("Please install manually:")
            print("  sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ben")
            return False
            
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            return False


# ==================== GUI APPLICATION ====================
if GUI_AVAILABLE:
    class ImageToTextApp:
        """Main GUI Application"""
        
        def __init__(self, root):
            self.root = root
            self.root.title(f"{Config.APP_NAME} v{Config.VERSION}")
            
            # Set window size
            window_width = 1100
            window_height = 750
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            center_x = int(screen_width/2 - window_width/2)
            center_y = int(screen_height/2 - window_height/2)
            
            self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
            self.root.minsize(900, 600)
            
            # Colors
            self.colors = {
                'bg_dark': '#0d1117',
                'bg_medium': '#161b22',
                'bg_light': '#21262d',
                'border': '#30363d',
                'text': '#c9d1d9',
                'text_dim': '#8b949e',
                'accent': '#58a6ff',
                'accent_green': '#3fb950',
                'accent_orange': '#d2991d',
                'accent_red': '#f85149',
                'accent_purple': '#a371f7',
                'button': '#21262d',
                'button_hover': '#30363d',
                'input_bg': '#0d1117',
            }
            
            self.root.configure(bg=self.colors['bg_dark'])
            
            # Initialize components
            self.web_scraper = PureWebScraper(self.update_download_progress)
            self.ocr = PureOCR()
            self.current_image_path = None
            self.processing = False
            
            # Create GUI
            self.setup_menu()
            self.create_widgets()
            self.check_tesseract_status()
        
        def setup_menu(self):
            """Setup menu bar"""
            menubar = tk.Menu(self.root, bg=self.colors['bg_medium'], 
                            fg=self.colors['text'], activebackground=self.colors['bg_light'])
            self.root.config(menu=menubar)
            
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_medium'], fg=self.colors['text'])
            menubar.add_cascade(label="📁 File", menu=file_menu)
            file_menu.add_command(label="📂 Open Image", command=self.open_image)
            file_menu.add_command(label="💾 Save Text", command=self.save_text)
            file_menu.add_separator()
            file_menu.add_command(label="❌ Exit", command=self.root.quit)
            
            # Tools menu
            tools_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_medium'], fg=self.colors['text'])
            menubar.add_cascade(label="🔧 Tools", menu=tools_menu)
            tools_menu.add_command(label="📁 Open Downloads", command=self.open_download_folder)
            tools_menu.add_command(label="📁 Open Output", command=self.open_output_folder)
            tools_menu.add_separator()
            tools_menu.add_command(label="🔧 Install Tesseract", command=self.install_tesseract)
            tools_menu.add_command(label="🗑️ Clear All", command=self.clear_all)
            
            # Help menu
            help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_medium'], fg=self.colors['text'])
            menubar.add_cascade(label="❓ Help", menu=help_menu)
            help_menu.add_command(label="ℹ️ About", command=self.show_about)
            help_menu.add_command(label="📖 How to Use", command=self.show_help)
        
        def create_widgets(self):
            """Create GUI widgets"""
            main_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
            main_container.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Header
            header_frame = tk.Frame(main_container, bg=self.colors['bg_medium'])
            header_frame.pack(fill='x', pady=(0, 10))
            
            title_frame = tk.Frame(header_frame, bg=self.colors['bg_medium'])
            title_frame.pack(pady=(15, 5))
            
            tk.Label(
                title_frame,
                text="🖼️",
                font=('Arial', 30),
                bg=self.colors['bg_medium']
            ).pack(side='left', padx=(0, 10))
            
            tk.Label(
                title_frame,
                text="IMAGE TO TEXT & WEB DOWNLOADER",
                font=('Arial', 18, 'bold'),
                fg=self.colors['accent'],
                bg=self.colors['bg_medium']
            ).pack(side='left')
            
            tk.Label(
                header_frame,
                text=f"Developed by {Config.DEVELOPER} | v{Config.VERSION} | No External Modules",
                font=('Arial', 9),
                fg=self.colors['text_dim'],
                bg=self.colors['bg_medium']
            ).pack(pady=(0, 15))
            
            # Content
            content_frame = tk.Frame(main_container, bg=self.colors['bg_dark'])
            content_frame.pack(fill='both', expand=True, pady=10)
            
            # Left panel
            left_panel = tk.Frame(content_frame, bg=self.colors['bg_dark'])
            left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
            self.create_download_panel(left_panel)
            
            # Right panel
            right_panel = tk.Frame(content_frame, bg=self.colors['bg_dark'])
            right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
            self.create_text_panel(right_panel)
            
            # Status bar
            status_frame = tk.LabelFrame(
                main_container,
                text=" 📊 Status ",
                font=('Arial', 9, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['bg_light'],
                relief='flat',
                bd=0,
                padx=10,
                pady=5
            )
            status_frame.pack(fill='x', pady=(10, 0))
            
            self.status_label = tk.Label(
                status_frame,
                text="✅ Ready | Developed by CHOWDHURY-VAI",
                font=('Arial', 8),
                fg=self.colors['accent_green'],
                bg=self.colors['bg_light'],
                anchor='w'
            )
            self.status_label.pack(fill='x')
        
        def create_download_panel(self, parent):
            """Create download panel"""
            frame = tk.LabelFrame(
                parent,
                text=" 📥 Website Image Downloader ",
                font=('Arial', 11, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['bg_light'],
                relief='flat',
                bd=0,
                padx=15,
                pady=15
            )
            frame.pack(fill='both', expand=True)
            
            # URL Input
            tk.Label(frame, text="Website URL:", font=('Arial', 10), 
                    fg=self.colors['text'], bg=self.colors['bg_light']).pack(anchor='w', pady=(0, 5))
            
            url_frame = tk.Frame(frame, bg=self.colors['bg_light'])
            url_frame.pack(fill='x', pady=(0, 15))
            
            self.url_entry = tk.Entry(url_frame, font=('Arial', 10), bg=self.colors['input_bg'],
                                      fg=self.colors['text'], insertbackground=self.colors['text'],
                                      relief='flat', bd=5)
            self.url_entry.pack(side='left', fill='x', expand=True, ipady=2)
            self.url_entry.insert(0, "https://")
            
            tk.Button(url_frame, text="📋", command=self.paste_url, bg=self.colors['button'],
                     fg=self.colors['text'], relief='flat', cursor='hand2', padx=10).pack(side='left', padx=(5, 0))
            
            # Quality
            tk.Label(frame, text="Image Quality:", font=('Arial', 10),
                    fg=self.colors['text'], bg=self.colors['bg_light']).pack(anchor='w', pady=(0, 5))
            
            quality_frame = tk.Frame(frame, bg=self.colors['bg_light'])
            quality_frame.pack(fill='x', pady=(0, 15))
            
            self.quality_var = tk.StringVar(value="high")
            
            for text, value in [("Original", "original"), ("HD", "high"), 
                               ("Medium", "medium"), ("Low", "low")]:
                tk.Radiobutton(quality_frame, text=text, value=value, variable=self.quality_var,
                             font=('Arial', 9), bg=self.colors['bg_light'], fg=self.colors['accent'],
                             selectcolor=self.colors['input_bg'], activebackground=self.colors['bg_light'],
                             activeforeground=self.colors['accent_green']).pack(side='left', padx=10)
            
            # Progress
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
            self.progress_bar.pack(fill='x', pady=(0, 5))
            
            self.progress_label = tk.Label(frame, text="Ready", font=('Arial', 8),
                                           fg=self.colors['text_dim'], bg=self.colors['bg_light'])
            self.progress_label.pack(anchor='w', pady=(0, 10))
            
            # Download button
            self.download_btn = tk.Button(frame, text="🚀 DOWNLOAD ALL IMAGES", command=self.start_download,
                                         font=('Arial', 11, 'bold'), bg=self.colors['accent_green'],
                                         fg='white', relief='flat', cursor='hand2', pady=8)
            self.download_btn.pack(fill='x', pady=(0, 10))
            
            # Result
            self.download_result = tk.Label(frame, text="", font=('Arial', 9),
                                           fg=self.colors['accent_green'], bg=self.colors['bg_light'],
                                           wraplength=400, justify='left')
            self.download_result.pack(anchor='w')
        
        def create_text_panel(self, parent):
            """Create text extraction panel"""
            frame = tk.LabelFrame(
                parent,
                text=" 📝 Image to Text (OCR) ",
                font=('Arial', 11, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['bg_light'],
                relief='flat',
                bd=0,
                padx=15,
                pady=15
            )
            frame.pack(fill='both', expand=True)
            
            # Image selection
            tk.Label(frame, text="Select Image:", font=('Arial', 10),
                    fg=self.colors['text'], bg=self.colors['bg_light']).pack(anchor='w', pady=(0, 5))
            
            img_frame = tk.Frame(frame, bg=self.colors['bg_light'])
            img_frame.pack(fill='x', pady=(0, 10))
            
            self.image_path_var = tk.StringVar(value="No image selected")
            tk.Label(img_frame, textvariable=self.image_path_var, font=('Arial', 9),
                    fg=self.colors['text_dim'], bg=self.colors['input_bg'],
                    anchor='w', padx=10, pady=5).pack(side='left', fill='x', expand=True)
            
            tk.Button(img_frame, text="📂 Browse", command=self.open_image, bg=self.colors['button'],
                     fg=self.colors['text'], relief='flat', cursor='hand2', padx=10).pack(side='left', padx=(5, 0))
            
            # Language
            tk.Label(frame, text="Language:", font=('Arial', 10),
                    fg=self.colors['text'], bg=self.colors['bg_light']).pack(anchor='w', pady=(0, 5))
            
            self.lang_var = tk.StringVar(value="Bangla + English")
            lang_menu = tk.OptionMenu(frame, self.lang_var, *Config.LANGUAGES.keys())
            lang_menu.config(font=('Arial', 9), bg=self.colors['input_bg'],
                           fg=self.colors['text'], relief='flat', cursor='hand2')
            lang_menu.pack(fill='x', pady=(0, 10))
            
            # Extract button
            self.extract_btn = tk.Button(frame, text="🔍 EXTRACT TEXT", command=self.extract_text_from_image,
                                        font=('Arial', 11, 'bold'), bg=self.colors['accent_purple'],
                                        fg='white', relief='flat', cursor='hand2', pady=8)
            self.extract_btn.pack(fill='x', pady=(0, 10))
            
            # Text display
            text_frame = tk.Frame(frame, bg=self.colors['bg_light'])
            text_frame.pack(fill='both', expand=True)
            
            self.text_display = tk.Text(text_frame, wrap='word', font=('Consolas', 9),
                                       bg=self.colors['input_bg'], fg=self.colors['text'],
                                       insertbackground=self.colors['text'], relief='flat', bd=5,
                                       padx=10, pady=10)
            self.text_display.pack(side='left', fill='both', expand=True)
            
            scrollbar = tk.Scrollbar(text_frame, command=self.text_display.yview)
            scrollbar.pack(side='right', fill='y')
            self.text_display.config(yscrollcommand=scrollbar.set)
            
            # Buttons
            btn_frame = tk.Frame(frame, bg=self.colors['bg_light'])
            btn_frame.pack(fill='x', pady=(10, 0))
            
            tk.Button(btn_frame, text="📋 Copy", command=self.copy_text, bg=self.colors['button'],
                     fg=self.colors['text'], relief='flat', cursor='hand2', padx=15, pady=5).pack(side='left', padx=(0, 5))
            
            tk.Button(btn_frame, text="💾 Save", command=self.save_text, bg=self.colors['button'],
                     fg=self.colors['text'], relief='flat', cursor='hand2', padx=15, pady=5).pack(side='left')
            
            tk.Button(btn_frame, text="🗑️ Clear", command=lambda: self.text_display.delete(1.0, 'end'),
                     bg=self.colors['accent_red'], fg='white', relief='flat', cursor='hand2',
                     padx=15, pady=5).pack(side='right')
        
        # ==================== FUNCTIONALITY ====================
        def check_tesseract_status(self):
            """Check Tesseract status"""
            if self.ocr.is_available():
                version = self.ocr.get_version()
                langs = self.ocr.get_languages()
                
                status = f"✅ Tesseract v{version or '?'} | "
                status += f"Bangla: {'✅' if 'ben' in langs else '⚠️'} | "
                status += f"English: {'✅' if 'eng' in langs else '⚠️'} | "
                status += "Developed by CHOWDHURY-VAI"
                
                self.status_label.config(text=status, fg=self.colors['accent_green'])
            else:
                self.status_label.config(
                    text="⚠️ Tesseract not found | Tools > Install Tesseract | Developed by CHOWDHURY-VAI",
                    fg=self.colors['accent_orange']
                )
        
        def install_tesseract(self):
            """Install Tesseract"""
            response = messagebox.askyesno(
                "Install Tesseract",
                "Do you want to install Tesseract OCR?\n\n"
                "This is required for text extraction.\n"
                "Installation may take a few minutes."
            )
            
            if response:
                self.status_label.config(text="📦 Installing Tesseract...", fg=self.colors['accent_orange'])
                self.root.update()
                
                def install_thread():
                    TesseractInstaller.install()
                    self.root.after(0, self.check_tesseract_status)
                    self.root.after(0, lambda: messagebox.showinfo("Done", "Installation complete!\nPlease restart the app."))
                
                thread = threading.Thread(target=install_thread, daemon=True)
                thread.start()
        
        def paste_url(self):
            """Paste URL"""
            try:
                clipboard = self.root.clipboard_get()
                if clipboard:
                    self.url_entry.delete(0, 'end')
                    self.url_entry.insert(0, clipboard)
            except:
                pass
        
        def update_download_progress(self, current, total):
            """Update progress"""
            if total > 0:
                progress = (current / total) * 100
                self.progress_var.set(progress)
                self.progress_label.config(text=f"Downloading: {current}/{total}")
                self.root.update_idletasks()
        
        def start_download(self):
            """Start download"""
            url = self.url_entry.get().strip()
            
            if not url or url == "https://":
                messagebox.showwarning("Warning", "Please enter a valid URL")
                return
            
            if self.processing:
                messagebox.showwarning("Warning", "Already processing")
                return
            
            self.processing = True
            quality = self.quality_var.get()
            
            self.download_btn.config(state='disabled', text="⏳ Downloading...", bg=self.colors['accent_orange'])
            self.status_label.config(text="📥 Downloading...", fg=self.colors['accent_orange'])
            
            def download_thread():
                try:
                    result = self.web_scraper.download_all_images(url, quality)
                    self.root.after(0, lambda: self.download_complete(result))
                except Exception as e:
                    self.root.after(0, lambda: self.download_error(str(e)))
            
            thread = threading.Thread(target=download_thread, daemon=True)
            thread.start()
        
        def download_complete(self, result):
            """Download complete"""
            self.processing = False
            self.download_btn.config(state='normal', text="🚀 DOWNLOAD ALL IMAGES", bg=self.colors['accent_green'])
            
            if result['success']:
                msg = f"✅ {result['downloaded']}/{result['total']} images\n📁 {result['folder']}"
                self.download_result.config(text=msg, fg=self.colors['accent_green'])
                self.status_label.config(text=f"✅ Downloaded {result['downloaded']} images", fg=self.colors['accent_green'])
                messagebox.showinfo("Success", f"Downloaded {result['downloaded']} images!\n\n{result['folder']}")
            else:
                self.download_result.config(text=f"❌ {result['message']}", fg=self.colors['accent_red'])
                self.status_label.config(text="❌ Failed", fg=self.colors['accent_red'])
                messagebox.showerror("Error", result['message'])
        
        def download_error(self, error_msg):
            """Download error"""
            self.processing = False
            self.download_btn.config(state='normal', text="🚀 DOWNLOAD ALL IMAGES", bg=self.colors['accent_green'])
            messagebox.showerror("Error", f"Download failed:\n{error_msg}")
        
        def open_image(self):
            """Open image"""
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"), ("All", "*.*")]
            )
            if file_path:
                self.current_image_path = file_path
                self.image_path_var.set(f"📷 {os.path.basename(file_path)}")
                
                info = PureImageProcessor.get_image_info(file_path)
                if info:
                    self.status_label.config(
                        text=f"📷 {info['filename']} | {info['size']} | {info['file_size_mb']}MB",
                        fg=self.colors['accent']
                    )
        
        def extract_text_from_image(self):
            """Extract text"""
            if not self.current_image_path:
                messagebox.showwarning("Warning", "Please select an image first!")
                return
            
            if self.processing:
                messagebox.showwarning("Warning", "Already processing")
                return
            
            if not self.ocr.is_available():
                if messagebox.askyesno("Tesseract Not Found", "Install Tesseract now?"):
                    self.install_tesseract()
                return
            
            self.processing = True
            language = Config.LANGUAGES[self.lang_var.get()]
            
            self.extract_btn.config(state='disabled', text="⏳ Extracting...", bg=self.colors['accent_orange'])
            self.status_label.config(text="🔍 Extracting...", fg=self.colors['accent_orange'])
            self.text_display.delete(1.0, 'end')
            self.text_display.insert(1.0, "⏳ Processing... Please wait...")
            
            def extract_thread():
                try:
                    text = self.ocr.preprocess_and_extract(self.current_image_path, language)
                    self.root.after(0, lambda: self.display_text(text))
                except Exception as e:
                    self.root.after(0, lambda: self.extraction_error(str(e)))
            
            thread = threading.Thread(target=extract_thread, daemon=True)
            thread.start()
        
        def display_text(self, text):
            """Display text"""
            self.processing = False
            self.extract_btn.config(state='normal', text="🔍 EXTRACT TEXT", bg=self.colors['accent_purple'])
            
            self.text_display.delete(1.0, 'end')
            self.text_display.insert(1.0, text)
            
            words = len(text.split())
            self.status_label.config(text=f"✅ Extracted: {words} words", fg=self.colors['accent_green'])
            
            if not text.startswith(('Error', '⚠️', 'No text')):
                messagebox.showinfo("Success", f"Text extracted!\nWords: {words}")
        
        def extraction_error(self, error_msg):
            """Extraction error"""
            self.processing = False
            self.extract_btn.config(state='normal', text="🔍 EXTRACT TEXT", bg=self.colors['accent_purple'])
            self.text_display.delete(1.0, 'end')
            self.text_display.insert(1.0, f"❌ Error:\n{error_msg}")
        
        def copy_text(self):
            """Copy text"""
            text = self.text_display.get(1.0, 'end').strip()
            if text and not text.startswith("⏳"):
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.status_label.config(text="📋 Copied!", fg=self.colors['accent_green'])
            else:
                messagebox.showwarning("Warning", "No text to copy!")
        
        def save_text(self):
            """Save text"""
            text = self.text_display.get(1.0, 'end').strip()
            if not text or text.startswith("⏳"):
                messagebox.showwarning("Warning", "No text to save!")
                return
            
            file_path = filedialog.asksaveasfilename(
                title="Save Text",
                defaultextension=".txt",
                filetypes=[("Text", "*.txt"), ("All", "*.*")]
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    self.status_label.config(text=f"💾 Saved: {os.path.basename(file_path)}", fg=self.colors['accent_green'])
                    messagebox.showinfo("Success", f"Saved!\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        
        def open_download_folder(self):
            """Open download folder"""
            if os.path.exists(Config.DOWNLOAD_DIR):
                system = platform.system()
                if system == 'Windows':
                    os.startfile(Config.DOWNLOAD_DIR)
                elif system == 'Darwin':
                    subprocess.run(['open', Config.DOWNLOAD_DIR])
                else:
                    subprocess.run(['xdg-open', Config.DOWNLOAD_DIR])
        
        def open_output_folder(self):
            """Open output folder"""
            if os.path.exists(Config.OUTPUT_DIR):
                system = platform.system()
                if system == 'Windows':
                    os.startfile(Config.OUTPUT_DIR)
                elif system == 'Darwin':
                    subprocess.run(['open', Config.OUTPUT_DIR])
                else:
                    subprocess.run(['xdg-open', Config.OUTPUT_DIR])
        
        def clear_all(self):
            """Clear all"""
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, "https://")
            self.text_display.delete(1.0, 'end')
            self.progress_var.set(0)
            self.download_result.config(text="")
            self.progress_label.config(text="Ready")
            self.image_path_var.set("No image selected")
            self.current_image_path = None
            self.status_label.config(text="🗑️ Cleared | Developed by CHOWDHURY-VAI", fg=self.colors['text_dim'])
        
        def show_about(self):
            """About"""
            about = f"""
╔══════════════════════════════════╗
║   🖼️  IMAGE TO TEXT &          ║
║   WEB IMAGE DOWNLOADER         ║
║                                ║
║   Version: {Config.VERSION}              ║
║   Developer: {Config.DEVELOPER}        ║
║                                ║
║   🔧 NO EXTERNAL MODULES      ║
║   📦 Built-in Libraries Only  ║
║   🌐 Cross-Platform           ║
║                                ║
║   ✅ Download Website Images  ║
║   ✅ Extract Text (OCR)       ║
║   ✅ Bangla + English         ║
║   ✅ Auto Tesseract Install   ║
║                                ║
╚══════════════════════════════════╝
            """
            messagebox.showinfo("About", about)
        
        def show_help(self):
            """Help"""
            help_text = """
📖 HOW TO USE:

📥 WEBSITE IMAGE DOWNLOADER:
1. Enter website URL
2. Select quality
3. Click 'DOWNLOAD ALL IMAGES'
4. Images saved in: downloaded_images/

📝 IMAGE TO TEXT (OCR):
1. Click 'Browse' to select image
2. Select language
3. Click 'EXTRACT TEXT'
4. Copy or Save the text

💡 TIPS:
• Install Tesseract: Tools > Install Tesseract
• Or: sudo apt-get install tesseract-ocr
• Use clear images for best OCR results
• Bangla+English for mixed content

👨‍💻 DEVELOPED BY: CHOWDHURY-VAI
            """
            messagebox.showinfo("Help", help_text)

else:
    # GUI not available - create placeholder
    class ImageToTextApp:
        def __init__(self, *args, **kwargs):
            pass


# ==================== MAIN ====================
def main():
    """Main function"""
    print("\n" + "="*60)
    print("  🖼️  IMAGE TO TEXT & WEB DOWNLOADER")
    print("  v" + Config.VERSION + " - Standalone Edition")
    print("  Developed by " + Config.DEVELOPER)
    print("  NO EXTERNAL MODULES REQUIRED")
    print("="*60)
    
    print(f"\n🐍 Python: {sys.version.split()[0]}")
    print(f"💻 System: {platform.system()} {platform.release()}")
    
    if not GUI_AVAILABLE:
        print("\n❌ GUI mode not available. Tkinter is required.")
        print("📦 Install: sudo apt-get install python3-tk")
        
        # Try to install
        if platform.system().lower() == 'linux':
            print("\n📦 Attempting to install tkinter...")
            try:
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'python3-tk'], check=False)
                print("✅ Please restart the application.")
            except:
                print("❌ Could not install. Please install manually.")
        
        sys.exit(1)
    
    # Check Tesseract
    ocr = PureOCR()
    if ocr.is_available():
        version = ocr.get_version()
        langs = ocr.get_languages()
        print(f"\n✅ Tesseract v{version or '?'} found")
        if langs:
            print(f"📚 Languages: {', '.join(langs)}")
    else:
        print("\n⚠️  Tesseract not found")
        print("   Use Tools > Install Tesseract in the app")
    
    print("\n📁 Downloads:", Config.DOWNLOAD_DIR)
    print("📁 Output:", Config.OUTPUT_DIR)
    print("="*60 + "\n")
    
    try:
        root = tk.Tk()
        app = ImageToTextApp(root)
        print("🚀 Application started!\n")
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

from flask import Flask, request, send_file, render_template_string, jsonify
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from docx import Document
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from pdfminer.high_level import extract_text
import os, uuid, subprocess

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

ALL_FORMATS = {
    'image': ['PDF', 'PNG', 'WEBP'],
    'document': ['PDF', 'TXT', 'PNG'],
    'audio': ['MP3', 'WAV', 'OGG'],
    'video': ['MP4', 'AVI', 'WEBM']
}

CONVERSION_TABLE = {
    'Images': 'JPG, PNG, WEBP → PDF, PNG, WEBP',
    'Documents': 'DOCX, PDF, TXT → PDF, TXT, PNG',
    'Audio': 'MP3, WAV, OGG → MP3, WAV, OGG',
    'Video': 'MP4, AVI, WEBM → MP4, AVI, WEBM'
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html><head>
    <title>Smart File Converter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e2e8f0;
        }
        
        .container { 
            max-width: 800px; 
            margin: 0 auto;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
        }
        
        h1 { 
            font-size: 3rem; 
            font-weight: 700;
            text-align: center;
            margin-bottom: 40px;
            background: linear-gradient(135deg, #06b6d4, #8b5cf6, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }
        
        .upload-area {
            background: rgba(30, 41, 59, 0.6);
            border: 2px dashed rgba(148, 163, 184, 0.3);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-bottom: 40px;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            border-color: #06b6d4;
            background: rgba(30, 41, 59, 0.8);
        }
        
        input[type=file] {
            display: none;
        }
        
        .file-input-label {
            display: inline-block;
            padding: 16px 32px;
            background: linear-gradient(135deg, #06b6d4, #8b5cf6);
            color: white;
            border-radius: 16px;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4);
        }
        
        .file-input-label:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(6, 182, 212, 0.6);
        }
        
        select {
            display: none;
            margin-top: 20px;
            padding: 12px 20px;
            border: 2px solid rgba(148, 163, 184, 0.3);
            border-radius: 16px;
            background: rgba(30, 41, 59, 0.8);
            color: #e2e8f0;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
        }
        
        select:focus {
            border-color: #06b6d4;
            box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.2);
        }
        
        button {
            display: none;
            margin-top: 20px;
            padding: 14px 28px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            border: none;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(16, 185, 129, 0.6);
        }
        
        h2 {
            font-size: 1.8rem;
            font-weight: 600;
            text-align: center;
            margin-bottom: 30px;
            color: #f1f5f9;
            letter-spacing: -0.01em;
        }
        
        .table-container {
            overflow-x: auto;
            border-radius: 20px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(15, 23, 42, 0.8);
            border-radius: 20px;
            overflow: hidden;
        }
        
        th {
            background: linear-gradient(135deg, #06b6d4, #8b5cf6);
            color: white;
            padding: 20px;
            text-align: left;
            font-weight: 600;
            font-size: 1.1rem;
            letter-spacing: -0.01em;
        }
        
        td {
            padding: 18px 20px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            color: #cbd5e1;
            font-weight: 500;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        tr:hover {
            background: rgba(30, 41, 59, 0.6);
        }
        
        #result {
            margin-top: 30px;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-weight: 600;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .success {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2));
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .error {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .loading {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(139, 92, 246, 0.2));
            color: #06b6d4;
            border: 1px solid rgba(6, 182, 212, 0.3);
        }
        
        .download-link {
            display: inline-block;
            margin-left: 12px;
            padding: 8px 16px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        }
        
        .download-link:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
        }
        
        @media (max-width: 768px) {
            .container { padding: 20px; }
            h1 { font-size: 2rem; }
            .upload-area { padding: 20px; }
            th, td { padding: 12px; }
        }
    </style>
</head><body>
<div class="container">
    <h1>Smart File Converter</h1>
    <div class="upload-area">
        <input type="file" id="fileInput">
        <label for="fileInput" class="file-input-label">Choose File</label>
        <select id="formatSelect"></select>
        <button onclick="convert()" id="convertBtn">Convert</button>
    </div>
    <h2>Supported Conversions</h2>
    <div class="table-container">
        <table>
            <tr><th>Type</th><th>Conversions</th></tr>
            {% for key, val in conversion_table.items() %}
            <tr><td>{{ key }}</td><td>{{ val }}</td></tr>
            {% endfor %}
        </table>
    </div>
    <div id="result"></div>
</div>
<script>
const formatMap = {
    image: {{ image_formats|tojson }},
    document: {{ doc_formats|tojson }},
    audio: {{ audio_formats|tojson }},
    video: {{ video_formats|tojson }}
};

function detectType(ext) {
    ext = ext.toLowerCase();
    if (["png","jpg","jpeg","webp"].includes(ext)) return "image";
    if (["pdf","docx","txt"].includes(ext)) return "document";
    if (["mp3","wav","ogg"].includes(ext)) return "audio";
    if (["mp4","avi","webm"].includes(ext)) return "video";
    return null;
}

document.getElementById('fileInput').onchange = function() {
    const file = this.files[0];
    const ext = file.name.split('.').pop();
    const type = detectType(ext);
    if (!type) return alert("Unsupported file type");

    const select = document.getElementById('formatSelect');
    select.innerHTML = formatMap[type].map(f => `<option value="${f}">${f}</option>`).join('');
    select.style.display = 'inline-block';
    document.getElementById('convertBtn').style.display = 'inline-block';
    select.dataset.type = type;
};

function convert() {
    const file = document.getElementById('fileInput').files[0];
    const format = document.getElementById('formatSelect').value;
    const type = document.getElementById('formatSelect').dataset.type;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);

    const result = document.getElementById('result');
    result.innerHTML = 'Converting...';
    result.className = 'loading';

    fetch(`/convert/${type}`, {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            result.innerHTML = `✅ Success! <a href="/download/${data.filename}" class="download-link" download>Download</a>`;
            result.className = 'success';
        } else {
            result.innerHTML = '❌ Error: ' + data.error;
            result.className = 'error';
        }
    });
}
</script>
</body></html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE,
        image_formats=ALL_FORMATS['image'],
        doc_formats=ALL_FORMATS['document'],
        audio_formats=ALL_FORMATS['audio'],
        video_formats=ALL_FORMATS['video'],
        conversion_table=CONVERSION_TABLE)

def save_file(file):
    ext = file.filename.split('.')[-1]
    filename = f"upload_{uuid.uuid4().hex[:8]}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return path

def output_path(extension):
    filename = f"converted_{uuid.uuid4().hex[:8]}.{extension.lower()}"
    return filename, os.path.join(CONVERTED_FOLDER, filename)

@app.route('/convert/image', methods=['POST'])
def convert_image():
    try:
        file = request.files['file']
        out_format = request.form['format'].upper()
        image = Image.open(file.stream)
        fname, path = output_path(out_format)
        if out_format == 'PDF':
            image.convert('RGB').save(path, 'PDF')
        else:
            image.save(path, out_format)
        return jsonify(success=True, filename=fname)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/convert/document', methods=['POST'])
def convert_document():
    try:
        file = request.files['file']
        out_format = request.form['format'].lower()
        in_path = save_file(file)
        fname, out_path = output_path(out_format)
        ext = os.path.splitext(in_path)[1].lower()

        if ext == '.docx':
            doc = Document(in_path)
            text = '\n'.join([p.text for p in doc.paragraphs])
        elif ext == '.pdf':
            text = extract_text(in_path)
        elif ext == '.txt':
            with open(in_path, encoding='utf-8') as f:
                text = f.read()
        else:
            return jsonify(success=False, error='Unsupported input format')

        if out_format == 'txt':
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
        elif out_format == 'pdf':
            pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))
            c = canvas.Canvas(out_path, pagesize=A4)
            width, height = A4
            margin = 40
            max_width = width - 2 * margin
            y = height - margin
            font_size = 14
            c.setFont('DejaVu', font_size)
            for paragraph in text.split('\n'):
                lines = simpleSplit(paragraph, 'DejaVu', font_size, max_width)
                for line in lines:
                    c.drawString(margin, y, line)
                    y -= font_size + 4
                    if y < margin:
                        c.showPage()
                        c.setFont('DejaVu', font_size)
                        y = height - margin
            c.save()
        elif out_format == 'png':
            width, height = 1000, 1400
            margin, line_height = 30, 30
            font = ImageFont.truetype(FONT_PATH, 20)
            lines = text.split('\n')
            pages, y = [], margin
            current_page = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(current_page)
            for line in lines:
                if y > height - margin:
                    pages.append(current_page)
                    current_page = Image.new('RGB', (width, height), 'white')
                    draw = ImageDraw.Draw(current_page)
                    y = margin
                draw.text((margin, y), line[:1000], font=font, fill='black')
                y += line_height
            pages.append(current_page)
            pages[0].save(out_path, save_all=True, append_images=pages[1:] if len(pages) > 1 else [])
        else:
            return jsonify(success=False, error='Unsupported output format')
        return jsonify(success=True, filename=fname)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/convert/audio', methods=['POST'])
def convert_audio():
    try:
        file = request.files['file']
        out_format = request.form['format'].lower()
        in_path = save_file(file)
        sound = AudioSegment.from_file(in_path)
        fname, out_path = output_path(out_format)
        sound.export(out_path, format=out_format)
        return jsonify(success=True, filename=fname)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/convert/video', methods=['POST'])
def convert_video():
    try:
        file = request.files['file']
        out_format = request.form['format'].lower()
        in_path = save_file(file)
        fname, out_path = output_path(out_format)
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', in_path]
        if out_format == 'webm':
            ffmpeg_cmd += ['-c:v', 'libvpx', '-b:v', '1M', '-deadline', 'realtime', '-cpu-used', '5', '-c:a', 'libvorbis']
        elif out_format == 'avi':
            ffmpeg_cmd += ['-c:v', 'mpeg4', '-q:v', '5', '-c:a', 'mp3']
        elif out_format == 'mp4':
            ffmpeg_cmd += ['-c:v', 'libx264', '-c:a', 'aac']
        else:
            return jsonify(success=False, error='Unsupported format')
        ffmpeg_cmd.append(out_path)
        process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if process.returncode != 0:
            return jsonify(success=False, error='FFmpeg conversion failed')
        return jsonify(success=True, filename=fname)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(CONVERTED_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

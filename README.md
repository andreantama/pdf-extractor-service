# PDF Extractor Service

Service API untuk ekstraksi konten dari file PDF dengan arsitektur master-worker menggunakan Python dan Redis queue.

## 🚀 Fitur

- **Master-Worker Architecture**: Satu master app dan multiple worker app untuk processing paralel
- **Multi-Content Extraction**: 
  - Text extraction dari PDF native
  - Table extraction dengan struktur data yang rapi
  - Image extraction dengan OCR (Optical Character Recognition)
- **Scalable Workers**: Dapat menjalankan multiple worker untuk processing yang lebih cepat
- **Queue Management**: Menggunakan Redis untuk task distribution dan result collection
- **Docker Support**: Containerized deployment dengan Docker Compose
- **API REST**: Interface yang mudah digunakan dengan FastAPI
- **Monitoring**: Health check dan status tracking

## 📋 Persyaratan Sistem

### Docker Deployment
- Docker dan Docker Compose
- Minimum 4GB RAM
- 2GB free disk space

### Local Development  
- Python 3.11+ atau 3.12.x
- Redis server
- Tesseract OCR
- Minimum 2GB RAM
- 1GB free disk space

## 📊 Deployment Methods Comparison

| Aspect | Docker Compose | Local Development |
|--------|---------------|-------------------|
| **Setup Complexity** | ⭐⭐⭐ (Medium) | ⭐⭐⭐⭐ (Complex) |
| **Resource Usage** | Higher (containers) | Lower (native) |
| **Isolation** | ✅ Full isolation | ❌ Shared environment |
| **Scalability** | ✅ Easy scaling | ⭐ Manual scaling |
| **Development** | ⭐ Slower rebuilds | ✅ Fast iteration |
| **Debugging** | ⭐ Container logs | ✅ Direct debugging |
| **Production Ready** | ✅ Yes | ❌ Dev only |
| **Dependencies** | ✅ Contained | ❌ System dependent |

### Recommended Usage

- **Docker Compose**: Production, staging, demo environments
- **Local Development**: Development, debugging, testing, learning

## 🏗️ Arsitektur

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│  Client     │───▶│ Master App  │───▶│   Redis     │
│             │    │ (FastAPI)   │    │   Queue     │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │   Result    │◀───│  Worker 1   │
                   │ Collection  │    │             │
                   └─────────────┘    └─────────────┘
                           ▲                   
                           │           ┌─────────────┐
                           └───────────│  Worker 2   │
                                      │             │
                                      └─────────────┘
```

## 🚀 Quick Start

### Metode 1: Docker Compose (Recommended untuk Production)

#### 1. Clone dan Setup
```bash
git clone <repository>
cd pdf-ekstractor-service

# Copy environment file
cp .env.example .env
```

#### 2. Jalankan dengan Docker Compose
```bash
# Build dan jalankan semua services
docker-compose up --build

# Atau jalankan di background
docker-compose up -d --build

# Menggunakan script helper
./start.sh
```

### Metode 2: Local Development Environment

#### 1. Setup Development Environment
```bash
# Setup virtual environment dan dependencies
./setup-dev.sh
```

#### 2. Start Redis Server
Pilih salah satu opsi:

**Option A: Redis Lokal**
```bash
# Install Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Start Redis
redis-server

# Atau sebagai service
sudo systemctl start redis-server
```

**Option B: Redis dengan Docker**
```bash
docker run -d --name redis-local -p 6379:6379 redis:7-alpine
```

#### 3. Jalankan Service Lokal
```bash
# Jalankan semua service (master + 2 workers)
./run-local.sh

# Atau jalankan terpisah untuk development:

# Terminal 1: Master App
./run-master.sh

# Terminal 2: Worker App
./run-worker.sh

# Terminal 3: Worker App kedua (optional)
./run-worker.sh
```

### 3. Test Service

```bash
# Check health
curl http://localhost:8000/health

# Upload PDF untuk processing
curl -X POST "http://localhost:8000/upload-pdf" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample.pdf"

# Atau gunakan script testing
./test.sh
```

## 📖 API Documentation

### Upload PDF

```http
POST /upload-pdf
Content-Type: multipart/form-data

file: [PDF file]
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "total_pages": 25,
  "status": "pending",
  "message": "PDF uploaded successfully. Processing 25 pages."
}
```

### Check Job Status

```http
GET /job-status/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "total_pages": 25,
  "completed_pages": 15,
  "failed_pages": 0,
  "created_at": "2025-10-25T10:00:00",
  "results": []
}
```

### Get Job Result

```http
GET /job-result/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "total_pages": 25,
  "completed_pages": 25,
  "failed_pages": 0,
  "processing_time": 45.5,
  "results": [
    {
      "page_number": 1,
      "content": [
        {
          "content_type": "text",
          "content": "Lorem ipsum dolor sit amet...",
          "bbox": [100, 200, 500, 250],
          "confidence": 1.0,
          "metadata": {
            "font": "Arial",
            "size": 12
          }
        },
        {
          "content_type": "table",
          "content": {
            "table_id": "table_1",
            "headers": ["Name", "Age", "City"],
            "rows": [["John", "25", "Jakarta"]],
            "data": [{"Name": "John", "Age": "25", "City": "Jakarta"}]
          },
          "bbox": [50, 300, 550, 400],
          "confidence": 0.9
        },
        {
          "content_type": "image",
          "content": {
            "image_id": "image_1",
            "width": 200,
            "height": 150,
            "extracted_text": [
              {
                "text": "Medical Report",
                "confidence": 0.95,
                "bbox": [[10, 20], [180, 20], [180, 40], [10, 40]]
              }
            ],
            "has_text": true
          },
          "bbox": [100, 450, 300, 600],
          "confidence": 0.85
        }
      ],
      "processing_time": 2.3,
      "status": "completed"
    }
  ],
  "created_at": "2025-10-25T10:00:00",
  "completed_at": "2025-10-25T10:00:45"
}
```

### Get RAG Knowledge (New! 🧠)

```http
GET /job-knowledge/{job_id}
```

**Description:** Mendapatkan knowledge yang telah diagregasi untuk konsumsi RAG model.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "total_pages": 25,
  "processed_pages": 25,
  "failed_pages": 0,
  "page_knowledge": [
    {
      "page_number": 1,
      "knowledge": "Laporan Keuangan Tahunan 2023. Perusahaan mengalami pertumbuhan revenue sebesar 15%...",
      "status": "completed"
    }
  ],
  "full_document_knowledge": "Page 1:\nLaporan Keuangan Tahunan 2023...\n\nPage 2:\nTabel distribusi penjualan...",
  "knowledge_length": 1543
}
```

**Key Features untuk RAG:**
- `full_document_knowledge`: Complete aggregated text dari seluruh dokumen
- `page_knowledge`: Knowledge per halaman untuk attribution
- Text sudah dinormalisasi dan dibersihkan untuk konsumsi RAG
- Menggabungkan hasil ekstraksi text, table, dan OCR image

## 🧠 RAG Integration

### Knowledge Aggregation

Service ini menyediakan knowledge aggregation yang telah dioptimasi untuk RAG (Retrieval-Augmented Generation) model. Setiap halaman PDF diekstrak dan content-nya digabungkan menjadi knowledge string yang clean dan normalized.

### Format Knowledge

```json
{
  "full_document_knowledge": "Page 1:\nContent from all sources...\n\nPage 2:\n...",
  "page_knowledge": [
    {
      "page_number": 1,
      "knowledge": "Combined text from text extraction + table content + OCR results",
      "status": "completed"
    }
  ],
  "knowledge_length": 1543
}
```

### Knowledge Processing

Knowledge dibuat dengan menggabungkan:
- **Text Extraction**: Teks yang diekstrak langsung dari PDF
- **Table Content**: Data dari tabel yang dikonversi ke teks
- **OCR Results**: Teks dari image yang di-OCR dengan EasyOCR
- **Normalization**: Pembersihan whitespace, karakter khusus, dan formatting

### RAG Integration Example

```python
import requests

# Upload dan proses PDF
upload_response = requests.post("http://localhost:8000/upload-pdf", files={'file': pdf_file})
job_id = upload_response.json()['job_id']

# Tunggu processing selesai
# ... status checking ...

# Ambil knowledge untuk RAG
knowledge_response = requests.get(f"http://localhost:8000/job-knowledge/{job_id}")
knowledge_data = knowledge_response.json()

# Gunakan untuk RAG
rag_input = knowledge_data['full_document_knowledge']
# Feed ke RAG model...
```

### Testing RAG Knowledge

```bash
# Test knowledge aggregation
python3 test-knowledge.py

# Lihat contoh knowledge format
python3 rag-knowledge-example.py
```

## ⚙️ Konfigurasi

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | localhost | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `MASTER_HOST` | 0.0.0.0 | Master app host |
| `MASTER_PORT` | 8000 | Master app port |
| `PAGES_PER_WORKER` | 5 | Jumlah halaman per worker task |
| `MAX_FILE_SIZE` | 104857600 | Max file size (100MB) |
| `LOG_LEVEL` | INFO | Log level |

### Scaling Workers

Untuk menambah jumlah worker:

```bash
# Scale worker menjadi 4 instance
docker-compose up --scale worker1=2 --scale worker2=2

# Atau edit docker-compose.yml dan tambah worker3, worker4, dst.
```

## 🔧 Development

### Setup Local Development

#### Prerequisites
- Python 3.11+ atau 3.12.x
- Redis server (lokal atau Docker)
- Tesseract OCR
- Git

#### Step-by-Step Setup

```bash
# 1. Clone repository
git clone <repository>
cd pdf-ekstractor-service

# 2. Setup development environment
./setup-dev.sh

# 3. Start Redis (pilih salah satu)
# Option A: Local Redis
sudo systemctl start redis-server

# Option B: Docker Redis  
docker run -d --name redis-dev -p 6379:6379 redis:7-alpine

# 4. Activate virtual environment
source venv/bin/activate

# 5. Copy environment untuk development
cp .env.local .env

# 6. Run service
./run-local.sh
```

#### Development Workflow

**Menjalankan Service Terpisah (untuk debugging):**

```bash
# Terminal 1: Start Master App
source venv/bin/activate
./run-master.sh

# Terminal 2: Start Worker App  
source venv/bin/activate
./run-worker.sh

# Terminal 3: Additional Worker (optional)
source venv/bin/activate  
./run-worker.sh
```

**Monitoring dan Debugging:**

```bash
# View logs real-time
tail -f logs/master_app.log
tail -f logs/worker_app.log

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI

# Monitor Redis queues
redis-cli monitor
```

### Install Dependencies Manual

Jika `./setup-dev.sh` gagal, install manual:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ind \
    libgl1-mesa-glx \
    libglib2.0-0 \
    redis-server

# Create directories
mkdir -p uploads temp logs
```

### Environment Configuration untuk Development

File `.env.local` berisi konfigurasi yang dioptimalkan untuk development:

```bash
# Konfigurasi Redis lokal
REDIS_HOST=localhost
REDIS_PORT=6379

# Log level untuk debugging  
LOG_LEVEL=DEBUG

# Halaman per worker lebih kecil untuk testing
PAGES_PER_WORKER=3

# Host master untuk development
MASTER_HOST=127.0.0.1
```

### 📁 Directory Structure & Paths

Project menggunakan **absolute paths** untuk konsistensi:

```bash
pdf-ekstractor-service/
├── uploads/              # 📂 Uploaded PDF files (AUTO-CREATED)
├── temp/                 # 📂 Temporary files (AUTO-CREATED)  
├── logs/                 # 📂 Application logs (AUTO-CREATED)
├── master_app/           # 📱 Master application
├── worker_app/           # 👷 Worker application
└── shared/               # 🔧 Shared modules
```

**Important**: File paths sekarang menggunakan project root sebagai base directory, bukan working directory saat menjalankan aplikasi.

**Check paths status:**
```bash
./check-paths.sh  # Lihat status direktori dan path configuration
```

**Upload file location:**
- Files disimpan di: `{project_root}/uploads/{job_id}.pdf`
- Contoh: `/path/to/pdf-ekstractor-service/uploads/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf`

### Struktur Project

```
pdf-ekstractor-service/
├── shared/                    # Shared modules
│   ├── config.py             # Configuration settings
│   ├── models.py             # Pydantic models
│   ├── redis_queue.py        # Redis queue management
│   └── __init__.py
├── master_app/               # Master application
│   ├── main.py              # FastAPI master app
│   └── __init__.py
├── worker_app/               # Worker application
│   ├── main.py              # Worker processing app
│   └── __init__.py
├── Dockerfile.master         # Master app Dockerfile
├── Dockerfile.worker         # Worker app Dockerfile
├── docker-compose.yml        # Docker Compose configuration
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .env.local               # Local development environment
├── .gitignore               # Git ignore rules
├── README.md                # Documentation
├── setup-dev.sh             # Setup development environment
├── start.sh                 # Start Docker Compose services
├── run-local.sh             # Run all services locally
├── run-master.sh            # Run only master app
├── run-worker.sh            # Run only worker app
├── stop-local.sh            # Stop all local services
├── check-paths.sh           # Check directory paths and status
├── test-datetime.py         # Test datetime serialization fix
└── test.sh                  # Test service functionality
```

### Available Scripts

| Script | Description | Usage |
|--------|-------------|-------|
| `setup-dev.sh` | Setup development environment | `./setup-dev.sh` |
| `start.sh` | Start Docker Compose services | `./start.sh` |
| `run-local.sh` | Run all services in local Python | `./run-local.sh` |
| `run-master.sh` | Run only master app locally | `./run-master.sh` |
| `run-worker.sh` | Run only worker app locally | `./run-worker.sh` |
| `stop-local.sh` | Stop all local services | `./stop-local.sh` |
| `check-paths.sh` | Check directory paths and status | `./check-paths.sh` |
| `test-datetime.py` | Test datetime serialization fix | `./test-datetime.py` |
| `test.sh` | Test service functionality | `./test.sh` |

**Script Usage Examples:**

```bash
# First time setup
./setup-dev.sh

# Development - run all services locally  
./run-local.sh

# Development - run services separately
# Terminal 1:
./run-master.sh

# Terminal 2:  
./run-worker.sh

# Stop semua services
./stop-local.sh

# Production - run with Docker
./start.sh

# Testing
./test.sh
```

## 📊 Monitoring

### Service Health

- Master app health: `http://localhost:8000/health`
- Redis Commander (optional): `http://localhost:8081`

### Logs

```bash
# View logs
docker-compose logs -f master
docker-compose logs -f worker1
docker-compose logs -f redis

# Log files (jika menggunakan volume mount)
tail -f logs/master_app.log
tail -f logs/worker_app.log
```

## 🧪 Testing

### Test dengan sample PDF

```bash
# Upload PDF
curl -X POST "http://localhost:8000/upload-pdf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test.pdf"

# Akan return job_id, kemudian check status
curl "http://localhost:8000/job-status/{job_id}"

# Ambil hasil setelah selesai
curl "http://localhost:8000/job-result/{job_id}"
```

## 🐛 Troubleshooting

### Docker Issues

1. **Redis Connection Failed**
   ```bash
   # Check Redis container
   docker-compose logs redis
   ```

2. **OCR Not Working**
   ```bash
   # Check tesseract installation
   docker exec -it pdf-extractor-worker1 tesseract --version
   ```

3. **Memory Issues**
   ```bash
   # Increase Docker memory limit atau reduce PAGES_PER_WORKER
   ```

4. **File Upload Issues**
   ```bash
   # Check file size limit dan permissions
   ```

### Local Development Issues

1. **Virtual Environment Issues**
   ```bash
   # Remove dan recreate virtual environment
   rm -rf venv
   ./setup-dev.sh
   ```

2. **Redis Connection Failed**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # Start Redis server
   redis-server
   
   # Atau gunakan Docker
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **Import Errors**
   ```bash
   # Pastikan virtual environment aktif
   source venv/bin/activate
   
   # Check Python path
   echo $PYTHONPATH
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Tesseract OCR Issues**
   ```bash
   # Install Tesseract (Ubuntu/Debian)
   sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind
   
   # macOS
   brew install tesseract
   
   # Check installation
   tesseract --version
   ```

5. **Permission Errors**
   ```bash
   # Fix script permissions
   chmod +x *.sh
   
   # Fix directory permissions
   sudo chown -R $USER:$USER uploads temp logs
   ```

6. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Kill process
   sudo kill -9 <PID>
   
   # Atau ubah port di .env
   MASTER_PORT=8001
   ```

7. **Module Not Found Errors**
   ```bash
   # Add current directory to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   
   # Atau jalankan dengan
   python -m master_app.main
   python -m worker_app.main
   ```

7. **DateTime Serialization Errors**
   ```bash
   # Error: Object of type datetime is not JSON serializable
   
   # Test datetime serialization fix
   ./test-datetime.py
   
   # Jika masih error, check Redis connection
   redis-cli ping
   
   # Restart Redis jika perlu
   sudo systemctl restart redis-server
   ```

8. **PIL.Image.ANTIALIAS Error (Pillow 10.0.0+)**
   ```bash
   # Error: module 'PIL.Image' has no attribute 'ANTIALIAS'
   
   # Quick fix dengan script otomatis
   python3 fix-pil-antialias.py
   
   # Manual fix - install Pillow versi kompatibel
   pip uninstall -y Pillow
   pip install Pillow==10.3.0
   pip install --upgrade easyocr==1.7.1
   
   # Atau gunakan Pillow versi lama
   pip install Pillow==9.5.0
   
   # Test fix
   python3 -c "from PIL import Image; print('✅ PIL working')"
   ```

9. **JSON Serialization Error (int64/numpy types)**
   ```bash
   # Error: Object of type int64 is not JSON serializable
   
   # Test fix dengan script otomatis
   python3 test-int64-fix.py
   
   # Manual check - test numpy/pandas serialization
   python3 -c "
   import json
   import numpy as np
   from shared.redis_queue import DateTimeEncoder
   data = {'test': np.int64(123)}
   result = json.dumps(data, cls=DateTimeEncoder)
   print('✅ int64 serialization working')
   "
   
   # Jika masih error, restart service
   ./stop-local.sh
   ./run-local.sh
   ```

### Common Development Fixes

**Reset Development Environment:**
```bash
# Stop semua process
./stop-local.sh  # jika ada

# Clean up
rm -rf venv logs/* uploads/* temp/*

# Reset setup
./setup-dev.sh
```

**Debug Worker Issues:**
```bash
# Jalankan worker dengan debug mode
cd worker_app
python -c "
import main
worker = main.PDFWorker()
worker.run()
"
```

**Monitor Redis Queues:**
```bash
# Connect ke Redis CLI
redis-cli

# Monitor queue
LLEN pdf_processing_queue
LLEN pdf_result_queue

# View queue content
LRANGE pdf_processing_queue 0 -1
```

## 📝 Performance Tips

1. **Optimasi Worker**: Sesuaikan `PAGES_PER_WORKER` berdasarkan ukuran halaman PDF
2. **Memory Management**: Monitor penggunaan memory untuk PDF besar
3. **Scaling**: Tambah worker sesuai dengan CPU cores available
4. **Redis Tuning**: Sesuaikan Redis configuration untuk throughput tinggi

## 🔐 Security

- Validasi file type dan size di master app
- Sanitize input untuk mencegah path traversal
- Set proper file permissions pada upload directory
- Use environment variables untuk sensitive data

## 📚 Dependencies

### Main Libraries

- **FastAPI**: Web framework untuk master app
- **PyMuPDF (fitz)**: PDF processing dan image extraction
- **pdfplumber**: Table extraction
- **EasyOCR**: OCR untuk text dari images
- **Redis**: Queue management
- **Pandas**: Data manipulation untuk tables
- **OpenCV**: Image processing
- **Pillow**: Image handling

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

[Your License Here]

---

**Dibuat untuk keperluan ekstraksi rekam medis dari PDF dengan arsitektur scalable dan robust.**
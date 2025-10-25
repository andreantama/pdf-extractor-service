"""
Test RAG Knowledge Aggregation dengan contoh sederhana
"""

import json

# Contoh data hasil knowledge aggregation
sample_knowledge_result = {
    "job_id": "test-123",
    "status": "completed",
    "total_pages": 3,
    "processed_pages": 3,
    "failed_pages": 0,
    "page_knowledge": [
        {
            "page_number": 1,
            "knowledge": "Laporan Keuangan Tahunan 2023. Perusahaan mengalami pertumbuhan revenue sebesar 15% dibandingkan tahun sebelumnya. Total aset mencapai Rp 500 miliar dengan laba bersih Rp 75 miliar.",
            "status": "completed"
        },
        {
            "page_number": 2,
            "knowledge": "Tabel distribusi penjualan: Produk A (40%), Produk B (35%), Produk C (25%). Grafik menunjukkan tren peningkatan penjualan selama 4 kuartal berturut-turut.",
            "status": "completed"
        },
        {
            "page_number": 3,
            "knowledge": "Proyeksi 2024: Target revenue Rp 1.2 triliun, ekspansi ke 5 kota baru, peluncuran 3 produk inovatif. Strategi fokus pada digitalisasi dan customer experience.",
            "status": "completed"
        }
    ],
    "full_document_knowledge": "Page 1:\nLaporan Keuangan Tahunan 2023. Perusahaan mengalami pertumbuhan revenue sebesar 15% dibandingkan tahun sebelumnya. Total aset mencapai Rp 500 miliar dengan laba bersih Rp 75 miliar.\n\nPage 2:\nTabel distribusi penjualan: Produk A (40%), Produk B (35%), Produk C (25%). Grafik menunjukkan tren peningkatan penjualan selama 4 kuartal berturut-turut.\n\nPage 3:\nProyeksi 2024: Target revenue Rp 1.2 triliun, ekspansi ke 5 kota baru, peluncuran 3 produk inovatif. Strategi fokus pada digitalisasi dan customer experience.",
    "knowledge_length": 543
}

def simulate_rag_query(knowledge_data, query):
    """Simulasi bagaimana RAG model bisa menggunakan knowledge"""
    
    full_knowledge = knowledge_data["full_document_knowledge"]
    
    # Simulasi pencarian dalam knowledge
    query_lower = query.lower()
    relevant_parts = []
    
    for line in full_knowledge.split('\n'):
        if any(keyword in line.lower() for keyword in query_lower.split()):
            relevant_parts.append(line.strip())
    
    return {
        "query": query,
        "relevant_knowledge": relevant_parts,
        "source_pages": len(knowledge_data["page_knowledge"]),
        "total_knowledge_length": knowledge_data["knowledge_length"]
    }

# Test berbagai query
test_queries = [
    "Berapa revenue perusahaan?",
    "Apa strategi untuk tahun 2024?",
    "Bagaimana distribusi penjualan produk?",
    "Berapa laba bersih tahun ini?"
]

print("🧠 RAG Knowledge Aggregation Test")
print("=" * 50)

print("\n📄 Sample Knowledge Data:")
print(json.dumps(sample_knowledge_result, indent=2, ensure_ascii=False))

print("\n🔍 RAG Query Simulation:")
print("-" * 30)

for query in test_queries:
    result = simulate_rag_query(sample_knowledge_result, query)
    print(f"\nQuery: {result['query']}")
    print(f"Relevant Knowledge:")
    for knowledge in result['relevant_knowledge']:
        if knowledge:  # Skip empty lines
            print(f"  - {knowledge}")
    print(f"Source: {result['source_pages']} pages, {result['total_knowledge_length']} chars")

print("\n✅ Knowledge format ready for RAG integration!")
print("\n💡 Integration Tips:")
print("- Use full_document_knowledge for complete context")
print("- Use page_knowledge for specific page attribution")
print("- Knowledge is cleaned and normalized for RAG consumption")
print("- Supports both text extraction and OCR content")
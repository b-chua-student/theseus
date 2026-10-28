import chromadb

client = chromadb.PersistentClient(path="./chroma_data")

for info in client.list_collections():
    collection = client.get_collection(info.name)
    data = collection.get(include=["documents", "metadatas"])

    ids = data["ids"]
    documents = data["documents"] or []
    metadatas = data["metadatas"] or []

    print(f"\n=== {info.name} ({len(ids)} chunks) ===")

    records = sorted(
        zip(ids, documents, metadatas),
        key=lambda r: (str(r[2].get("owner_id", "")), int(r[2].get("ordinal", 0))),
    )

    for chunk_id, text, meta in records:
        print(f"\n[{meta.get('ordinal')}] {chunk_id}")
        print(f"  section: {meta.get('section_id')}")
        print(f"  range:   {meta.get('start_index')}-{meta.get('end_index')}")
        print(f"  status:  {meta.get('status')}  model: {meta.get('model_name')}")
        print(f"  text:    {text!r}")

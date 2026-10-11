from flask import Flask, request, jsonify
from test_database import client
import os
from markdownify import markdownify as md
from chonkie import RecursiveChunker
from dulwich import porcelain

import git_config



app = Flask(import_name=__name__)

@app.post('/api/save')
def save_document() -> tuple:
    print("Received JSON:", request.get_json(silent=True), flush=True)
    print("Files in repo directory:", list(git_config.path.iterdir()), flush=True)
    if not request.is_json:
        return jsonify({"message": "Error: file not saved"}), 400

    raw_json: dict = request.get_json() 
    
    if not raw_json or not isinstance(raw_json, dict):
        return jsonify({"message": "Error: file not saved"}), 400

    document_name = raw_json.get('document_name') or "document.html"
    raw_html = raw_json.get('content')

    if not isinstance(document_name, str) or not raw_html or not isinstance(raw_html, str):
        return jsonify({"message": "Error: file not saved"}), 400

    try:
        file_path = git_config.path / document_name
        print("SAVING TO ABSOLUTE PATH:", file_path.resolve(), flush=True)
        file_path.write_text(raw_html, encoding="utf-8")

        repo_str: str = str(git_config.path)
        porcelain.add(repo_str, paths=[document_name])
        porcelain.commit(repo_str, message=f"Save {document_name}\n".encode('utf-8'))

        markdown_text: str = md(
            raw_html,
            strip=["span", "strong", "em", "code", "blockquote"],
            heading_style="ATX"
        ).replace("\xa0", " ").replace("\u200b", "")

        chunker = RecursiveChunker.from_recipe(
            name="markdown",
            lang="en",
            chunk_size=512
        )
        chunks: list = chunker.chunk(markdown_text)
        print(f"Generated {len(chunks)} chunks with Chonkie.", flush=True)

        collection = client.get_or_create_collection('Collection')
        if chunks:
            ids_list: list[str] = []
            documents_list: list[str] = []
            metadatas_list: list[dict] = []

            for i, chunk in enumerate(chunks):
                ids_list.append(f"{document_name}_chunk_{i}")
                documents_list.append(chunk.text)
                metadatas_list.append({"document_name": document_name})

            collection.upsert(
                ids=ids_list,
                documents=documents_list,
                metadatas=metadatas_list
            )
            print(f"Total items stored in ChromaDB: {collection.count()}", flush=True)

    except Exception as e:
        print(f"Error saving document: {e}", flush=True)
        return jsonify({"message": "Error: file not saved"}), 400
    
    print("Document saved successfully.", flush=True)
    return jsonify({"message": "Document saved successfully."}), 200



if __name__ == '__main__':
    app.run(
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true" # Return true if environment variable value is true, else false.
    )

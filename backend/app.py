from flask import Flask, request, jsonify, Response
from dulwich import porcelain
from test_database import client, collection
from git_config import path, repo

app = Flask(import_name=__name__)

@app.post('/api/rename')
def rename_document() -> tuple[Response, int]:
    data = request.get_json()
    new_name = data.get('document_name')
    old_name = data.get('old_document_name')

    if not new_name or not old_name:
        return jsonify({'message': 'Missing document_name or old_document_name.'}), 400

    old_file_path = path / old_name
    new_file_path = path / new_name

    if new_file_path.exists():
        return jsonify({'message': 'Warning: file already exists.'}), 409

    if not old_file_path.exists():
        return jsonify({'message': 'Original file not found.'}), 404

    try:
        old_file_path.rename(new_file_path)

        index = repo.open_index()

        if old_name.encode('utf-8') in index:
            del index[old_name.encode('utf-8')]
            index.write()

        porcelain.add(str(path), [new_name])

        db_results = collection.get(where={'source_document': old_name})

        if not db_results or not db_results.get('ids'):
            db_results = collection.get(where={'document_name': old_name})

        if db_results and db_results.get('ids'):
            ids_to_update = db_results['ids']
            updated_metadatas = []
            
            for meta in db_results['metadatas']:
                meta['source_document'] = new_name
                meta['document_name'] = new_name
                updated_metadatas.append(meta)

            collection.update(
                ids=ids_to_update,
                metadatas=updated_metadatas
            )
            
        return jsonify({'message': 'Document renamed'}), 200

    except Exception as e:
        if not old_file_path.exists() and new_file_path.exists():
            new_file_path.rename(old_file_path)    
        return jsonify({'message': f'an error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
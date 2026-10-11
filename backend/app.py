from flask import Flask, request, jsonify, Response
from dulwich import porcelain
from test_database import collection
from git_config import path, repo

app = Flask(__name__)


@app.post('/api/rename')
def rename_document() -> tuple[Response, int]:
    data = request.get_json()

    old_name = data.get('old_document_name')
    new_name = data.get('document_name')

    if not old_name or not new_name:
        return jsonify({'message': 'Missing document name.'}), 400

    old_file = path / old_name
    new_file = path / new_name

    if new_file.exists():
        return jsonify({'message': 'Warning: file already exists'}), 409

    if not old_file.exists():
        return jsonify({'message': 'Original file not found.'}), 404

    try:
        old_file.rename(new_file)

        index = repo.open_index()
        old_key = old_name.encode('utf-8')

        if old_key in index:
            del index[old_key]
            index.write()

        porcelain.add(str(path), [new_name])

        db_results = collection.get(
            where={'document_name': old_name}
        )

        if db_results['ids']:
            metadatas = db_results['metadatas']

            for meta in metadatas:
                meta['document_name'] = new_name

            collection.update(
                ids=db_results['ids'],
                metadatas=metadatas
            )

        return jsonify({'message': 'Document renamed'}), 200

    except Exception as e:
        if not old_file.exists() and new_file.exists():
            new_file.rename(old_file)

        return jsonify({'message': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)

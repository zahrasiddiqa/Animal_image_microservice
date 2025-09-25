from flask import Flask, request, jsonify, send_from_directory, render_template_string
import sqlite3
import requests
import random
import datetime
from pathlib import Path

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pictures (
            id INTEGER PRIMARY KEY,
            animal TEXT,
            filename TEXT,
            source_url TEXT,
            saved_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_picture_record(db_path, animal, filename, source_url):
    saved_at = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO pictures (animal, filename, source_url, saved_at) VALUES (?,?,?,?)',
              (animal, filename, source_url, saved_at))
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return {'id': last_id, 'animal': animal, 'filename': filename, 'source_url': source_url, 'saved_at': saved_at}

def get_last_picture(db_path, animal):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, animal, filename, source_url, saved_at FROM pictures WHERE animal=? ORDER BY saved_at DESC LIMIT 1', (animal,))
    row = c.fetchone()
    conn.close()
    if row:
        id, animal, filename, source_url, saved_at = row
        return {'id': id, 'animal': animal, 'filename': filename, 'source_url': source_url, 'saved_at': saved_at, 'image_url': f'/images/{filename}'}
    return None

def fetch_image(url, dest_path):
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception:
        pass
    return False

def image_source_url(animal):
    w = random.randint(200, 600)
    h = random.randint(200, 600)
    if animal == 'cat':
        return f'https://placekitten.com/{w}/{h}'
    if animal == 'dog':
        return f'https://place.dog/{w}/{h}'
    if animal == 'bear':
        return f'https://placebear.com/{w}/{h}'
    raise ValueError('Unknown animal')

def create_app(config=None):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    base_dir = Path(__file__).parent
    app.config['DATABASE'] = str(base_dir / 'db.sqlite3')
    app.config['IMAGES_DIR'] = str(base_dir / 'images')
    if config:
        app.config.update(config)

    Path(app.config['IMAGES_DIR']).mkdir(parents=True, exist_ok=True)
    init_db(app.config['DATABASE'])

    INDEX_HTML = """
    <!doctype html>
    <html>
    <head><meta charset="utf-8"><title>Animal Fetcher</title></head>
    <body>
    <h1>Animal Picture Fetcher</h1>
    <form id="fm">
      <label>Animal:
        <select id="animal">
          <option>cat</option>
          <option>dog</option>
          <option>bear</option>
        </select>
      </label>
      <label>Count: <input id="count" type="number" value="1" min="1" max="10" /></label>
      <button type="submit">Fetch & Save</button>
      <button id="lastBtn" type="button">Fetch Last Saved</button>
    </form>
    <div id="result"></div>
    <script>
    const form = document.getElementById('fm');
    const lastBtn = document.getElementById('lastBtn');
    const result = document.getElementById('result');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const animal = document.getElementById('animal').value;
      const count = document.getElementById('count').value;
      const res = await fetch(`/api/fetch?animal=${animal}&count=${count}`, { method: 'POST' });
      const data = await res.json();
      showImages(data.saved);
    });

    lastBtn.addEventListener('click', async () => {
      const animal = document.getElementById('animal').value;
      const res = await fetch(`/api/last?animal=${animal}`);
      const data = await res.json();
      if (data.error) {
        result.textContent = data.error;
      } else {
        showImages([data]);
      }
    });

    function showImages(list) {
      result.innerHTML = '';
      if (list && list.length) {
        list.forEach(s => {
          const div = document.createElement('div');
          div.style.marginBottom = '20px';
          div.innerHTML = `<p><strong>${s.animal}</strong> saved at ${s.saved_at}</p>
                           <img src="${s.image_url}" style="max-width:320px; display:block;"/>
                           <p>source: <a href="${s.source_url}" target="_blank">${s.source_url}</a></p>`;
          result.appendChild(div);
        });
      } else {
        result.textContent = 'No images found.';
      }
    }
    </script>
    </body>
    </html>
    """

    @app.route('/')
    def index():
        return render_template_string(INDEX_HTML)

    @app.route('/api/fetch', methods=['POST', 'GET'])
    def api_fetch():
        animal = (request.args.get('animal') or
                  (request.json.get('animal') if request.is_json and request.json else None))
        count = (request.args.get('count') or
                 (request.json.get('count') if request.is_json and request.json else None))
        if not animal:
            return jsonify({'error': 'missing animal (cat|dog|bear)'}), 400
        animal = animal.lower()
        try:
            count = int(count) if count else 1
        except Exception:
            count = 1
        saved = []
        for i in range(count):
            try:
                src = image_source_url(animal)
            except ValueError:
                return jsonify({'error': 'unknown animal'}), 400
            filename = f"{animal}_{int(datetime.datetime.utcnow().timestamp())}_{random.randint(1000,9999)}.jpg"
            dest = Path(app.config['IMAGES_DIR']) / filename
            ok = fetch_image(src, str(dest))
            if not ok:
                continue
            rec = save_picture_record(app.config['DATABASE'], animal, filename, src)
            rec['image_url'] = f"/images/{filename}"
            saved.append(rec)
        return jsonify({'saved': saved})

    @app.route('/api/last', methods=['GET'])
    def api_last():
        animal = request.args.get('animal')
        if not animal:
            return jsonify({'error': 'missing animal parameter'}), 400
        rec = get_last_picture(app.config['DATABASE'], animal.lower())
        if not rec:
            return jsonify({'error': 'no picture found'}), 404
        return jsonify(rec)

    @app.route('/images/<path:filename>')
    def images(filename):
        return send_from_directory(app.config['IMAGES_DIR'], filename)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

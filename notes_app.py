from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

class NotesHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>My Notes</title>
                <style>
                    body { font-family: Arial; padding: 20px; }
                    .note { background: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    .note h3 { margin-top: 0; }
                    .delete { background: red; color: white; border: none; padding: 5px 10px; cursor: pointer; }
                </style>
            </head>
            <body>
                <h1> Note Taking App</h1>
                
                <form action="/add" method="POST">
                    <input type="text" name="title" placeholder="Note title" required><br><br>
                    <textarea name="content" rows="4" cols="50" placeholder="Note content"></textarea><br><br>
                    <button type="submit">Save Note</button>
                </form>
                
                <hr>
                <h2>Your Notes:</h2>
                <div id="notes"></div>
                
                <script>
                    fetch('/api/notes')
                        .then(r => r.json())
                        .then(notes => {
                            const container = document.getElementById('notes');
                            container.innerHTML = '';
                            
                            notes.forEach(note => {
                                const div = document.createElement('div');
                                div.className = 'note';
                                div.innerHTML = `
                                    <h3>${note.title}</h3>
                                    <p>${note.content}</p>
                                    <button class="delete" onclick="deleteNote(${note.id})">Delete</button>
                                `;
                                container.appendChild(div);
                            });
                        });
                    
                    function deleteNote(id) {
                        fetch(`/delete/${id}`, {method: 'POST'})
                            .then(() => location.reload());
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        elif self.path == '/api/notes':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            notes = load_notes()
            self.wfile.write(json.dumps(notes).encode())
    
    def do_POST(self):
        if self.path == '/add':
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(post_data)
            
            notes = load_notes()
            new_id = max([n['id'] for n in notes], default=0) + 1
            
            notes.append({
                'id': new_id,
                'title': params['title'][0],
                'content': params['content'][0]
            })
            
            save_notes(notes)
            
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        
        elif self.path.startswith('/delete/'):
            note_id = int(self.path.split('/')[-1])
            notes = load_notes()
            notes = [n for n in notes if n['id'] != note_id]
            
            save_notes(notes)
            
            self.send_response(200)
            self.end_headers()

def load_notes():
    try:
        with open('notes.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_notes(notes):
    with open('notes.json', 'w') as f:
        json.dump(notes, f, indent=2)

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8001), NotesHandler)
    print('✅ Notes app running at http://localhost:8001')
    server.serve_forever()
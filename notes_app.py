from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import os
from datetime import datetime

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
                    /* Modern Reset */
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        padding: 40px 20px;
                        color: #333;
                    }
                    
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        overflow: hidden;
                    }
                    
                    .header {
                        background: linear-gradient(135deg, #4a90e2, #357ae8);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }
                    
                    .header h1 {
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                        font-weight: 600;
                    }
                    
                    .header p {
                        opacity: 0.9;
                        font-size: 1.1rem;
                    }
                    
                    .main-content {
                        padding: 40px;
                    }
                    
                    .form-section {
                        background: #f8f9fa;
                        padding: 30px;
                        border-radius: 15px;
                        margin-bottom: 40px;
                        border: 1px solid #e9ecef;
                    }
                    
                    .form-group {
                        margin-bottom: 20px;
                    }
                    
                    label {
                        display: block;
                        margin-bottom: 8px;
                        font-weight: 600;
                        color: #495057;
                        font-size: 0.95rem;
                    }
                    
                    input[type="text"], textarea {
                        width: 100%;
                        padding: 14px;
                        border: 2px solid #e0e0e0;
                        border-radius: 10px;
                        font-size: 16px;
                        transition: all 0.3s;
                        background: white;
                    }
                    
                    input[type="text"]:focus, textarea:focus {
                        outline: none;
                        border-color: #4a90e2;
                        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
                    }
                    
                    textarea {
                        min-height: 150px;
                        resize: vertical;
                        font-family: inherit;
                    }
                    
                    .btn {
                        display: inline-block;
                        padding: 14px 28px;
                        border: none;
                        border-radius: 10px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s;
                        text-decoration: none;
                    }
                    
                    .btn-primary {
                        background: linear-gradient(135deg, #4a90e2, #357ae8);
                        color: white;
                    }
                    
                    .btn-primary:hover {
                        background: linear-gradient(135deg, #357ae8, #2a65c4);
                        transform: translateY(-2px);
                        box-shadow: 0 10px 20px rgba(74, 144, 226, 0.3);
                    }
                    
                    .btn-danger {
                        background: linear-gradient(135deg, #ff6b6b, #ee5a52);
                        color: white;
                        padding: 8px 16px;
                        font-size: 14px;
                    }
                    
                    .btn-danger:hover {
                        background: linear-gradient(135deg, #ee5a52, #d64545);
                        transform: translateY(-1px);
                    }
                    
                    .notes-section h2 {
                        color: #2c3e50;
                        margin-bottom: 25px;
                        font-size: 1.8rem;
                        border-bottom: 2px solid #f0f0f0;
                        padding-bottom: 10px;
                    }
                    
                    .notes-grid {
                        display: grid;
                        gap: 20px;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    }
                    
                    .note-card {
                        background: white;
                        border-radius: 15px;
                        padding: 25px;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                        border: 1px solid #e8e8e8;
                        transition: all 0.3s;
                        position: relative;
                    }
                    
                    .note-card:hover {
                        transform: translateY(-5px);
                        box-shadow: 0 15px 30px rgba(0,0,0,0.12);
                    }
                    
                    .note-card h3 {
                        color: #2c3e50;
                        margin-bottom: 15px;
                        font-size: 1.3rem;
                        font-weight: 600;
                        line-height: 1.4;
                    }
                    
                    .note-card p {
                        color: #555;
                        line-height: 1.6;
                        margin-bottom: 20px;
                        white-space: pre-wrap;
                    }
                    
                    .note-meta {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-top: 15px;
                        padding-top: 15px;
                        border-top: 1px solid #eee;
                    }
                    
                    .note-date {
                        font-size: 0.85rem;
                        color: #7f8c8d;
                    }
                    
                    .empty-state {
                        text-align: center;
                        padding: 60px 20px;
                        color: #95a5a6;
                    }
                    
                    .empty-state h3 {
                        font-size: 1.5rem;
                        margin-bottom: 10px;
                        color: #7f8c8d;
                    }
                    
                    .empty-state p {
                        font-size: 1.1rem;
                    }
                    
                    .form-actions {
                        display: flex;
                        gap: 15px;
                        margin-top: 25px;
                    }
                    
                    .btn-secondary {
                        background: #6c757d;
                        color: white;
                    }
                    
                    .btn-secondary:hover {
                        background: #5a6268;
                    }
                    
                    @media (max-width: 768px) {
                        .container {
                            border-radius: 15px;
                        }
                        
                        .header {
                            padding: 20px;
                        }
                        
                        .main-content {
                            padding: 20px;
                        }
                        
                        .notes-grid {
                            grid-template-columns: 1fr;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>My Notes</h1>
                        <p>Keep your thoughts organized and accessible</p>
                    </div>
                    
                    <div class="main-content">
                        <div class="form-section">
                            <h2 style="color: #2c3e50; margin-bottom: 20px;">Add New Note</h2>
                            <form id="noteForm">
                                <div class="form-group">
                                    <label for="title">Title</label>
                                    <input type="text" id="title" name="title" placeholder="Enter note title" required>
                                </div>
                                
                                <div class="form-group">
                                    <label for="content">Content</label>
                                    <textarea id="content" name="content" placeholder="Write your note here..."></textarea>
                                </div>
                                
                                <div class="form-actions">
                                    <button type="submit" class="btn btn-primary">Save Note</button>
                                    <button type="button" onclick="clearForm()" class="btn btn-secondary">Clear</button>
                                </div>
                            </form>
                        </div>
                        
                        <div class="notes-section">
                            <h2>Your Notes</h2>
                            <div id="notes" class="notes-grid"></div>
                        </div>
                    </div>
                </div>
                
                <script>
                    function formatDate(dateString) {
                        if (!dateString) return '';
                        try {
                            const date = new Date(decodeURIComponent(dateString));
                            return date.toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        } catch {
                            return dateString;
                        }
                    }
                    
                    function escapeHtml(text) {
                        const div = document.createElement('div');
                        div.textContent = text;
                        return div.innerHTML;
                    }
                    
                    function loadNotes() {
                        fetch('/api/notes')
                            .then(r => r.json())
                            .then(notes => {
                                const container = document.getElementById('notes');
                                container.innerHTML = '';
                                
                                if (notes.length === 0) {
                                    container.innerHTML = `
                                        <div class="empty-state">
                                            <h3>No Notes Yet</h3>
                                            <p>Create your first note using the form above.</p>
                                        </div>
                                    `;
                                    return;
                                }
                                
                                // Sort notes by ID (newest first)
                                notes.sort((a, b) => b.id - a.id);
                                
                                notes.forEach(note => {
                                    const noteCard = document.createElement('div');
                                    noteCard.className = 'note-card';
                                    noteCard.innerHTML = `
                                        <h3>${escapeHtml(note.title)}</h3>
                                        <p>${escapeHtml(note.content).replace(/\\n/g, '<br>')}</p>
                                        <div class="note-meta">
                                            <span class="note-date">${formatDate(note.created)}</span>
                                            <button class="btn btn-danger" onclick="deleteNote(${note.id})">
                                                Delete
                                            </button>
                                        </div>
                                    `;
                                    container.appendChild(noteCard);
                                });
                            })
                            .catch(err => {
                                console.error('Error loading notes:', err);
                                document.getElementById('notes').innerHTML = `
                                    <div class="empty-state">
                                        <h3>Error Loading Notes</h3>
                                        <p>Please refresh the page.</p>
                                    </div>
                                `;
                            });
                    }
                    
                    function deleteNote(id) {
                        if (confirm('Are you sure you want to delete this note?')) {
                            fetch(`/delete/${id}`, {method: 'POST'})
                                .then(response => {
                                    if (response.ok) {
                                        showMessage('Note deleted successfully!', 'success');
                                        loadNotes();
                                    } else {
                                        showMessage('Error deleting note', 'error');
                                    }
                                })
                                .catch(err => {
                                    showMessage('Error deleting note', 'error');
                                    console.error(err);
                                });
                        }
                    }
                    
                    function clearForm() {
                        document.getElementById('noteForm').reset();
                        showMessage('Form cleared', 'info');
                    }
                    
                    function showMessage(message, type) {
                        // Remove existing message
                        const existingMsg = document.querySelector('.message');
                        if (existingMsg) existingMsg.remove();
                        
                        const messageDiv = document.createElement('div');
                        messageDiv.className = `message message-${type}`;
                        messageDiv.textContent = message;
                        messageDiv.style.cssText = `
                            position: fixed;
                            top: 20px;
                            right: 20px;
                            padding: 15px 25px;
                            border-radius: 10px;
                            color: white;
                            font-weight: 600;
                            z-index: 1000;
                            animation: slideIn 0.3s ease;
                            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                        `;
                        
                        if (type === 'success') {
                            messageDiv.style.background = 'linear-gradient(135deg, #4CAF50, #45a049)';
                        } else if (type === 'error') {
                            messageDiv.style.background = 'linear-gradient(135deg, #ff6b6b, #ee5a52)';
                        } else {
                            messageDiv.style.background = 'linear-gradient(135deg, #2196F3, #1976D2)';
                        }
                        
                        document.body.appendChild(messageDiv);
                        
                        setTimeout(() => {
                            messageDiv.style.animation = 'slideOut 0.3s ease';
                            setTimeout(() => messageDiv.remove(), 300);
                        }, 3000);
                    }
                    
                    // Add animation styles
                    const style = document.createElement('style');
                    style.textContent = `
                        @keyframes slideIn {
                            from { transform: translateX(100%); opacity: 0; }
                            to { transform: translateX(0); opacity: 1; }
                        }
                        @keyframes slideOut {
                            from { transform: translateX(0); opacity: 1; }
                            to { transform: translateX(100%); opacity: 0; }
                        }
                    `;
                    document.head.appendChild(style);
                    
                    // Form submission
                    document.getElementById('noteForm').addEventListener('submit', function(e) {
                        e.preventDefault();
                        
                        const formData = new FormData(this);
                        const title = document.getElementById('title').value.trim();
                        
                        if (!title) {
                            showMessage('Please enter a title', 'error');
                            return;
                        }
                        
                        fetch('/add', {
                            method: 'POST',
                            body: new URLSearchParams(formData)
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                showMessage('Note saved successfully!', 'success');
                                this.reset();
                                loadNotes();
                            } else {
                                showMessage('Error saving note', 'error');
                            }
                        })
                        .catch(err => {
                            showMessage('Error saving note', 'error');
                            console.error(err);
                        });
                    });
                    
                    // Load notes when page loads
                    document.addEventListener('DOMContentLoaded', loadNotes);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        elif self.path == '/api/notes':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            notes = load_notes()
            self.wfile.write(json.dumps(notes).encode())
        
        elif self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-type', 'image/x-icon')
            self.end_headers()
            # Return a minimal favicon
            self.wfile.write(b'')
    
    def do_POST(self):
        if self.path == '/add':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                params = urllib.parse.parse_qs(post_data)
                
                if 'title' not in params or not params['title'][0].strip():
                    self.send_response(400)
                    self.end_headers()
                    return
                
                notes = load_notes()
                new_id = max([n['id'] for n in notes], default=0) + 1
                
                notes.append({
                    'id': new_id,
                    'title': params['title'][0].strip(),
                    'content': params.get('content', [''])[0].strip(),
                    'created': datetime.now().isoformat()
                })
                
                save_notes(notes)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'id': new_id}).encode())
                
            except Exception as e:
                print(f"Error adding note: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
        
        elif self.path.startswith('/delete/'):
            try:
                note_id = int(self.path.split('/')[-1])
                notes = load_notes()
                original_count = len(notes)
                notes = [n for n in notes if n['id'] != note_id]
                
                if len(notes) < original_count:
                    save_notes(notes)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            except ValueError:
                self.send_response(400)
                self.end_headers()
            except Exception as e:
                print(f"Error deleting note: {e}")
                self.send_response(500)
                self.end_headers()
    
    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

def load_notes():
    """Load notes from JSON file"""
    try:
        if os.path.exists('notes.json'):
            with open('notes.json', 'r', encoding='utf-8') as f:
                notes = json.load(f)
                # Convert old format to new format
                for note in notes:
                    if 'created' not in note:
                        note['created'] = datetime.now().isoformat()
                return notes
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading notes: {e}")
    return []

def save_notes(notes):
    """Save notes to JSON file"""
    try:
        with open('notes.json', 'w', encoding='utf-8') as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving notes: {e}")
        return False

if __name__ == '__main__':
    # Create initial notes file if it doesn't exist
    if not os.path.exists('notes.json'):
        with open('notes.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    PORT = 8000
    HOST = '0.0.0.0'  # Changed to allow access from other devices
    
    try:
        server = HTTPServer((HOST, PORT), NotesHandler)
        print("=" * 50)
        print("📝 NOTES APPLICATION")
        print("=" * 50)
        print(f"🌐 Server running at: http://{HOST}:{PORT}")
        print(f"💾 Notes saved in: notes.json")
        print("\n📱 Access from:")
        print(f"   • This computer: http://localhost:{PORT}")
        print(f"   • Other devices: http://[YOUR-IP]:{PORT}")
        print("\n🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

# Store tasks in a JSON file
TODO_FILE = 'todo.json'

class TodoHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            # Serve HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Todo App</title>
                <style>
                    body { font-family: Arial; max-width: 500px; margin: 0 auto; padding: 20px; }
                    .todo-form { display: flex; margin-bottom: 20px; }
                    input[type="text"] { flex: 1; padding: 10px; font-size: 16px; }
                    button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
                    button:hover { background: #0056b3; }
                    .task { display: flex; justify-content: space-between; padding: 10px; margin: 5px 0; background: #f5f5f5; }
                    .completed { text-decoration: line-through; color: #888; }
                    .delete-btn { background: #dc3545; color: white; border: none; padding: 5px 10px; cursor: pointer; }
                </style>
            </head>
            <body>
                <h1> My  Todo List</h1>
                
                <form class="todo-form" action="/add" method="POST">
                    <input type="text" name="task" placeholder="Enter new task..." required>
                    <button type="submit">Add Task</button>
                </form>
                
                <h2>Tasks:</h2>
                <div id="tasks">
                    <!-- Tasks will be loaded here -->
                </div>
                
                <script>
                    // Load tasks on page load
                    fetch('/api/tasks')
                        .then(r => r.json())
                        .then(tasks => {
                            const container = document.getElementById('tasks');
                            container.innerHTML = '';
                            
                            tasks.forEach(task => {
                                const taskDiv = document.createElement('div');
                                taskDiv.className = `task ${task.completed ? 'completed' : ''}`;
                                taskDiv.innerHTML = `
                                    <span>${task.text}</span>
                                    <div>
                                        <button onclick="toggleTask(${task.id})">
                                            ${task.completed ? 'Undo' : 'Complete'}
                                        </button>
                                        <button class="delete-btn" onclick="deleteTask(${task.id})">
                                            Delete
                                        </button>
                                    </div>
                                `;
                                container.appendChild(taskDiv);
                            });
                        });
                    
                    function toggleTask(id) {
                        fetch(`/toggle/${id}`, {method: 'POST'})
                            .then(() => location.reload());
                    }
                    
                    function deleteTask(id) {
                        fetch(`/delete/${id}`, {method: 'POST'})
                            .then(() => location.reload());
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        elif self.path == '/api/tasks':
            # Return tasks as JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            tasks = load_tasks()
            self.wfile.write(json.dumps(tasks).encode())
    
    def do_POST(self):
        if self.path == '/add':
            # Add new task
            length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(post_data)
            
            task_text = params['task'][0]
            tasks = load_tasks()
            
            new_id = max([t['id'] for t in tasks], default=0) + 1
            tasks.append({'id': new_id, 'text': task_text, 'completed': False})
            
            save_tasks(tasks)
            
            # Redirect to home
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        
        elif self.path.startswith('/toggle/'):
            # Toggle task completion
            task_id = int(self.path.split('/')[-1])
            tasks = load_tasks()
            
            for task in tasks:
                if task['id'] == task_id:
                    task['completed'] = not task['completed']
                    break
            
            save_tasks(tasks)
            
            self.send_response(200)
            self.end_headers()
        
        elif self.path.startswith('/delete/'):
            # Delete task
            task_id = int(self.path.split('/')[-1])
            tasks = load_tasks()
            tasks = [t for t in tasks if t['id'] != task_id]
            
            save_tasks(tasks)
            
            self.send_response(200)
            self.end_headers()

def load_tasks():
    try:
        with open(TODO_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_tasks(tasks):
    with open(TODO_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

if __name__ == '__main__':
    # Initialize with sample tasks if empty
    tasks = load_tasks()
    if not tasks:
        tasks = [
            {'id': 1, 'text': 'Learn Python', 'completed': False},
            {'id': 2, 'text': 'Build a web app', 'completed': False},
            {'id': 3, 'text': 'Deploy online', 'completed': False}
            
        ]
        save_tasks(tasks)
    
    server = HTTPServer(('localhost', 8000), TodoHandler)
    print('✅ Todo app running at http://localhost:8000')
    print('📁 Tasks saved in todo.json')
    server.serve_forever()
    # kjfsldkfjds
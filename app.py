from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory store — simple list of todos
todos = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book",   "done": False},
]
next_id = 3

@app.route("/todos", methods=["GET"])
def get_todos():
    return jsonify(todos), 200

@app.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if todo is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(todo), 200

@app.route("/todos", methods=["POST"])
def add_todo():
    global next_id
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title is required"}), 400
    todo = {"id": next_id, "title": data["title"], "done": False}
    todos.append(todo)
    next_id += 1
    return jsonify(todo), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

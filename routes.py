from flask import request, jsonify, Blueprint, current_app
from models import User, TodoItem
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime



register_bp = Blueprint('register_bp', __name__)
login_bp = Blueprint('login_bp', __name__)
create_todo_bp = Blueprint('create_todo', __name__)
update_todo_bp = Blueprint('update_todo', __name__)
delete_todo_bp = Blueprint('delete_todo', __name__)
get_todos_bp = Blueprint('get_todos', __name__)

def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Unathorized!'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


@register_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'message': 'User already exists!'}), 400
    
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=16)

    new_user = User(name=data['name'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    token = jwt.encode({'id': new_user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, current_app.config['SECRET_KEY'])
    return jsonify({'token': token})


@login_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password, data['password']):
        token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, current_app.config['SECRET_KEY'])
        return jsonify({'token': token}), 200
    return jsonify({'message': 'Invalid email or password'}), 401

@create_todo_bp.route('/todos', methods=['POST'])
@token_required  
def create_todo(current_user):
    data = request.get_json()
    new_todo = TodoItem(title=data['title'], description=data['description'], user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'id': new_todo.id, 'title': new_todo.title, 'description': new_todo.description}), 201

@update_todo_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@token_required
def update_todo(current_user, todo_id):
    todo = TodoItem.query.get(todo_id)
    if not todo or todo.user_id != current_user.id:
        return jsonify({'message': 'Forbidden'}), 403
    data = request.get_json()
    todo.title = data['title']
    todo.description = data['description']
    db.session.commit()
    return jsonify({'id': todo.id, 'title': todo.title, 'description': todo.description})

@delete_todo_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@token_required
def delete_todo(current_user, todo_id):
    todo = TodoItem.query.get(todo_id)
    if not todo or todo.user_id != current_user.id:
        return jsonify({'message': 'Forbidden'}), 403
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo deleted successfully'}), 200

@get_todos_bp.route('/todos', methods=['GET'])
@token_required
def get_todos(current_user):
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    todos = TodoItem.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=limit)
    return jsonify({
        'data': [{'id': todo.id, 'title': todo.title, 'description': todo.description} for todo in todos.items],
        'page': todos.page,
        'limit': todos.per_page,
        'total': todos.total,
    })
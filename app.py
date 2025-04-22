from database import db
from create_app import create_app
from routes import register_bp, login_bp, create_todo_bp, update_todo_bp, delete_todo_bp, get_todos_bp

app = create_app()


db.init_app(app)

app.register_blueprint(register_bp)
app.register_blueprint(login_bp)
app.register_blueprint(create_todo_bp)
app.register_blueprint(update_todo_bp)
app.register_blueprint(delete_todo_bp)
app.register_blueprint(get_todos_bp)  

if __name__ == '__main__':
    with app.app_context():  
        db.create_all()
    app.run(debug=True)
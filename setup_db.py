from app import db, app

def setup_database():
    with app.app_context():
        # Create database and tables
        db.create_all()
        print("Database and tables created successfully!")

if __name__ == "__main__":
    setup_database()

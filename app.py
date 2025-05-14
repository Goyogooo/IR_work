from app import create_app,db
from database.models import User, SearchHistory, UserSnapshot 
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)

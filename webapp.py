from flask import Flask
from app.web.routes import web
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(
        BASE_DIR,
        "templates"
    ),
    static_folder=os.path.join(
        BASE_DIR,
        "static"
    )
)

app.register_blueprint(web)


if __name__ == "__main__":
    app.run(debug=True)
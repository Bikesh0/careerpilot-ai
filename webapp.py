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

# Caps request body size (mainly the CV upload route) at 10MB, well
# above any real CV but enough to reject an accidental/abusive huge
# upload before it's fully read into memory.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

app.register_blueprint(web)


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    app.run(debug=debug)
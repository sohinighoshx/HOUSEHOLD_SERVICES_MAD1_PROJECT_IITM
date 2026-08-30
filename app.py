from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

import config

app.config.from_object(config.Config)

import models
import routes


if __name__ == "__main__":
    app.run(debug=True, port=5001)
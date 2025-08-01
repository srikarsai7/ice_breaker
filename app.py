# app.py

import json
from flask import Flask, render_template, request, Response
from dotenv import load_dotenv
from ice_breaker import ice_break_with_generator

load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["GET"])
def process():

    name = request.args.get("name", "")
    
    def stream_process(name_to_process: str):
        for event in ice_break_with_generator(name=name_to_process):
            sse_event = f"data: {json.dumps(event)}\n\n"
            yield sse_event
            

    return Response(stream_process(name), mimetype='text/event-stream')


if __name__ == "__main__":
    # The 'threaded=True' is crucial for streaming to work without blocking.
    app.run(host="0.0.0.0", debug=True, threaded=True)
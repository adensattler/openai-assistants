# from flask import Flask, render_template, request, jsonify, Response, stream_with_context
# from openai import OpenAI
# import os
# import json
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/api/assistants/threads', methods=['POST'])
# def create_thread():
#     thread = client.beta.threads.create()
#     return jsonify({"threadId": thread.id})

# @app.route('/api/assistants/threads/<thread_id>/messages', methods=['GET', 'POST'])
# def handle_messages(thread_id):
#     if request.method == 'POST':
#         data = request.json
#         client.beta.threads.messages.create(
#             thread_id=thread_id,
#             role="user",
#             content=data['content']
#         )

#     run = client.beta.threads.runs.create(
#         thread_id=thread_id,
#         assistant_id=ASSISTANT_ID
#     )

#     def generate():
#         while True:
#             run_status = client.beta.threads.runs.retrieve(
#                 thread_id=thread_id,
#                 run_id=run.id
#             )
#             if run_status.status == 'completed':
#                 messages = client.beta.threads.messages.list(thread_id=thread_id)
#                 for message in messages.data:
#                     if message.role == "assistant":
#                         for content in message.content:
#                             if content.type == 'text':
#                                 yield f"data: {json.dumps({'event': 'message', 'content': content.text.value})}\n\n"
#                 break
#             elif run_status.status == 'failed':
#                 yield f"data: {json.dumps({'event': 'error', 'content': 'Run failed'})}\n\n"
#                 break

#         yield f"data: {json.dumps({'event': 'done'})}\n\n"

#     return Response(stream_with_context(generate()), content_type='text/event-stream')


# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from openai import OpenAI
import os
import re
from dotenv import load_dotenv
from markdown2 import Markdown

app = Flask(__name__)

# Initialize OpenAI client
load_dotenv()   # Load environment variables from .env file

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
ASSISTANT_ID = os.environ.get("OPENAI_ASSISTANT_ID")

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_message = data['message']
    thread_id = data.get('threadId')

    if not thread_id:
        thread = client.beta.threads.create()
        thread_id = thread.id
    else:
        thread = client.beta.threads.retrieve(thread_id)

    # Add user message to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message,
    )

    # Run the thread
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )

    if run.status == "failed":
        return jsonify({"error": f"Run failed: {run.last_error}"}), 500

    # Retrieve the messages in the thread and get the most recent response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_response = messages.data[0].content[0].text.value

    # Use re.sub() to remove the matched source tags from the API response
    # pattern = r'【\d+†source】'
    # cleaned_response = re.sub(pattern, '', new_response)
    # Remove the source tags and trailing newlines
    cleaned_response = re.sub(r'【\d+[:†]\d+†source】', '', new_response)
    cleaned_response = cleaned_response.strip()
    print(cleaned_response)

    return jsonify({"response": cleaned_response, "threadId": thread_id})

if __name__ == '__main__':
    app.run(debug=True)


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
from dotenv import load_dotenv

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

    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message,
    )

    def generate():
        try:
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=ASSISTANT_ID,
            )

            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                
                if run.status == "failed":
                    yield f"data: {{\"event\": \"error\", \"content\": \"{run.last_error.message}\"}}\n\n"
                    break
                
                if run.status == "completed":
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    assistant_message = next((msg for msg in messages if msg.role == "assistant"), None)
                    if assistant_message:
                        content = assistant_message.content[0].text.value
                        yield f"data: {{\"event\": \"message\", \"content\": \"{content}\", \"threadId\": \"{thread_id}\"}}\n\n"
                    break

        except Exception as e:
            print(f"Error: {str(e)}")
            yield f"data: {{\"event\": \"error\", \"content\": \"{str(e)}\"}}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)



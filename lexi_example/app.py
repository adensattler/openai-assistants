from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
)
import openai
from flask_cors import CORS

client = openai.OpenAI()

app = Flask(__name__)
CORS(app)

chat_history = [
    {"role": "system", "content": "You are a helpful assistant."},
]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", chat_history=chat_history)


@app.route("/chat", methods=["POST"])
def chat():
    content = request.json.get("message")
    chat_history.append({"role": "user", "content": content})
    return jsonify(success=True)



@app.route("/stream", methods=["GET"])
def stream():
    def generate():
        assistant_response_content = ""
        finished = False
        with client.chat.completions.create(
            model="gpt-4-turbo",
            messages=chat_history,
            stream=True,
        ) as stream:
            for chunk in stream:
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    assistant_response_content += content
                    data = chunk.choices[0].delta.content.replace('\n', ' <br> ')
                    yield f"data: {data}\n\n"


                if chunk.choices[0].finish_reason == "stop":
                    finished = True
                    break

        yield f"data: finish_reason: stop\n\n"
        chat_history.append({"role": "assistant", "content": assistant_response_content})
        if finished:
            return

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# BACKUP
# @app.route("/stream", methods=["GET"])
# def stream():
#     user_message = request.args.get('message')
#     thread_id = request.args.get('threadId')

#     if not thread_id:
#         thread = client.beta.threads.create()
#         thread_id = thread.id
#     else:
#         thread = client.beta.threads.retrieve(thread_id)

#     # Add user message to thread
#     client.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content=user_message,
#     )


#     # https://platform.openai.com/docs/api-reference/runs/createRun
#     def event_generator():
#         finished = False
#         with client.beta.threads.runs.create(
#             thread_id=thread_id,
#             assistant_id=ASSISTANT_ID,
#             stream=True
#         ) as stream:
#             for event in stream:
#                 if event.event == "thread.message.delta":
#                     for content in event.data.delta.content:
#                         if content.type == 'text':
#                             # Personal Implementation
#                             # yield f"data: {json.dumps({'type': 'content', 'content': content.text.value})}\n\n"

#                             # LexiStream Integration
#                             data = content.text.value.replace('\n', ' <br> ')
#                             yield f"data: {data}\n\n"
                
#                 # handle all the status events (will get printed out on the server side for debugging)
#                 # elif event.event == "thread.run.created":
#                 #     yield f"data: {json.dumps({'type': 'status', 'content': 'run_created'})}\n\n"
#                 # elif event.event == "thread.run.queued":
#                 #     yield f"data: {json.dumps({'type': 'status', 'content': 'run_queued'})}\n\n"
#                 # elif event.event == "thread.run.in_progress":
#                 #     yield f"data: {json.dumps({'type': 'status', 'content': 'run_in_progress'})}\n\n"
#                 # elif event.event == "thread.run.completed":
#                 #     yield f"data: {json.dumps({'type': 'status', 'content': 'run_completed'})}\n\n"
#                 # elif event.event == "thread.run.failed":
#                 #     yield f"data: {json.dumps({'type': 'status', 'content': 'run_failed'})}\n\n"
#                 elif event.event == "done":
#                     # Generic Integration
#                     # yield f"data: {json.dumps({'type': 'status', 'content': 'done'})}\n\n"
#                     # break

#                     # LexiStream Implementation:
#                     finished = True
#                     break  
        
#         yield f"data: finish_reason: stop\n\n"
#         if finished:
#             return


    # generic implementation
    # return Response(event_generator(), mimetype="text/event-stream")

    # LexiStream Implementation:
    return Response(stream_with_context(event_generator()), mimetype="text/event-stream")

    


@app.route("/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = [{"role": "system", "content": "You are a helpful assistant."}]
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(port=5000)
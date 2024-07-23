"""
Module Name: assistant.py

DOES NOT USE STREAMING
"""

import shelve
import json
import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI
from openai.types.beta.threads import Text, TextDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta


load_dotenv()   # Load environment variables from .env file
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Create the OpenAI client for API interactions
# NOTE: You MUST set your OPENAI_API_KEY in a .env file or this will error out!
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# FUNCTIONS
# -----------------------------------------------------------------------------------------------------
# Creates an assistant tied to your OpenAI account
def create_assistant():
    vector_store = create_vector_store()        # create the vector store for the assistant

    assistant = client.beta.assistants.create(
        name="Saucy's Advisor",
        instructions="""You are a helpful assistant""",
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    return assistant

def create_vector_store():
    # Create a vector store
    vector_store = client.beta.vector_stores.create(name="Saucy Docs")

    # Ready the files for upload to OpenAI
    file_paths = ["menu.pdf",]
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    
    # You can print the status and the file counts of the batch to see the result of this operation.
    print(file_batch.status)
    print(file_batch.file_counts)

    return vector_store

# Upload file-like object that can be used across various endpoints. returns an OpenAI File object.
def upload_data(data: dict):
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=True) as temp_file:
        # Write the JSON data to the temporary file
        temp_file.write(json.dumps(data).encode("utf-8"))
        
        # Reset file pointer to the beginning
        temp_file.seek(0)
        
        # Create the file using the name of the temporary file
        file = client.files.create(
            file=open(temp_file.name, 'rb'),
            purpose="assistants"
        )
    return file



# Get a response to a message!
def generate_response(message_body, thread):
    try:
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_body,
        )
        
        # Run the thread! The 'create and poll' SDK helper only returns after the run it terminates (i.e. manages api polling)
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
        )

        if run.status == "failed":
            raise Exception(f"Run failed: {run.last_error}")
        

        # Retrieve the the messages in the thread and get the most recent response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        new_response = messages.data[0].content[0].text.value

        return new_response

        
    except Exception as e:
        print(f"{str(e)}")
    


def main():
    thread = client.beta.threads.create()
    
    print("Starting a new conversation. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
        else:
            response = generate_response(user_input, thread)
            print(f"Assistant: {response}")
            # No need to print the response here as it's already printed in the event handler

    print("Conversation ended.")

if __name__ == "__main__":
    main()


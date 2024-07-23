"""
Module Name: assistant.py

NOTE: This uses v2 of the Assistants API
migration guide: https://platform.openai.com/docs/assistants/migration/what-has-changed 

Description:
This module contains functions for setting up and interacting with a GENERIC assistant. 
For more information on Assistants API, refer to the documentation: 
https://platform.openai.com/docs/assistants/overview

For setting up your OpenAI Key, please follow the instructions at: 
https://platform.openai.com/docs/quickstart/step-2-set-up-your-api-key

In our application there is ONE Assistant with many different threads (or conversations) tied to that assistant.
Each thread represents a conversation about a specific property. 
The references to these conversations are stored in threads_db since this functionality is not built in to the Assistants API.

Functions:
- upload_data(data): Uploads a file-like object to be used across various endpoints and returns an OpenAI File object.
- create_assistant(): Creates a Real Estate assistant tied to your OpenAI account.
- check_if_thread_exists(zpid): Checks if there's an existing thread for a given Zillow Property ID (ZPID).
- store_thread(zpid, thread_id): Stores a ZPID-thread ID pair in the database for thread management.
- generate_response(message_body, zpid): Generates a response to a message about a property, managing threads as needed.
- run_assistant(thread): Runs the assistant thread and returns the response.
- main(): Driver function to test the AI Assistant from the command line.

Usage:
1. Ensure you have set up your OpenAI API key.
2. Use the main() function to interact with the assistant via command line.
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


# Thread Management Functions
# --------------------------------------------------------------------------------------------------
# DESC: These functions utilize the "shelve" library.
# Think of a shelf as a dictionary that persists on a filesystem
# We are using shelve to store the {zpid : thread_id} pair so we can "remember" current conversations.
# Note that thread creation is handled when generating a response.

# Returns thread_id from threads_db or None if DNE
def check_if_thread_exists(zpid):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(zpid, None)

# Adds a (zpid : thread_id) pair to threads_db
def store_thread(zpid, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[zpid] = thread_id


# Get a response to a message!
def generate_response(message_body, thread):
    
    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_body,
    )

    # RUN THE THREAD AND RETURN ITS RESPONSE
    response = run_assistant(thread)
    if not response:
        response = "An error occured! If you are a developer please check the server logs. Users can submit a bug report through the about page."
    return response


def run_assistant(thread):
    try:
        # Run the thread! The 'create and poll' SDK helper only returns after the run it terminates (i.e. manages api polling)
        # run = client.beta.threads.runs.create_and_poll(
        #     thread_id=thread.id,
        #     assistant_id=ASSISTANT_ID,
        # )

        # if run.status == "failed":
        #     raise Exception(f"Run failed: {run.last_error}")

        # # Retrieve the the messages in the thread and get the most recent response
        # messages = client.beta.threads.messages.list(thread_id=thread.id)
        # new_response = messages.data[0].content[0].text.value

        # Use re.sub() to remove the matched source tags from the API response
        # pattern = r'【\d+†source】'
        # cleaned_response = re.sub(pattern, '', new_response)

        # return new_response

        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()

        
    except Exception as e:
        print(f"{str(e)}")



# https://github.com/openai/openai-python/blob/main/helpers.md

# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
class EventHandler(AssistantEventHandler):
  @override
  def on_text_created(self, text: Text) -> None:
    print(f"Assistant: ", end="", flush=True)

  @override
  def on_text_delta(self, delta: TextDelta, snapshot: Text):
    print(delta.value, end="", flush=True)

  @override
  def on_tool_call_created(self, tool_call: ToolCall):
    print(f"Assistant: {tool_call.type}\n", flush=True)

  @override
  def on_tool_call_delta(self, delta: ToolCallDelta, snapshot: ToolCall):
    if delta.type == "code_interpreter" and delta.code_interpreter:
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)



def main():
    thread = client.beta.threads.create()
    
    print("Starting a new conversation. Type 'exit' to quit.")
    while True:
        user_input = input("\n\nYou: ")
        if user_input.lower() == 'exit':
            break
        else:
            response = generate_response(user_input, thread)
            # No need to print the response here as it's already printed in the event handler

    print("Conversation ended.")

if __name__ == "__main__":
    main()


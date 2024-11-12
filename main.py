import re
import json
import os
import datetime
from typing import Dict

import dotenv
import requests

from utils import process_answer_references

dotenv.load_dotenv()
base_url = os.getenv("MYSCALEKB_BASE_URL")
api_key = os.getenv("MYSCALEKB_API_KEY")


def main():
    if not base_url or not api_key:
        raise ValueError("base_url and api_key must be set")

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }

    # List KnowledgeBases
    kb_url = f"{base_url}/kbs"
    response = requests.get(kb_url, headers=headers)
    response.raise_for_status()
    print(f"Request {kb_url}, response: \n", response.json())

    # Use KnowledgeBase to create conversation
    target_kb_type = "general"
    target_kb_id = "ceb25e7f-3159-4338-b740-e315d474bd4a"
    payload = {
        "knowledge_scopes": {
            "kb_and_docs": [{
                "kb_type": target_kb_type,
                "kb_id": target_kb_id,
                "doc_ids": None
            }],
            "collection_ids": None
        },
        "model": "gpt-4o",
    }
    conversation_url = f"{base_url}/conversations"
    response = requests.post(conversation_url, json=payload, headers=headers)
    response.raise_for_status()
    print(f"Request {conversation_url}, response: \n", response.json())
    # Get conversation_id from response
    conversation_id = response.json()["id"]

    # Use conversation to maintain a chat, run the simplest query
    payload = {
        "conversation_id": conversation_id,
        "message": {
            "role": "user",
            "content": "Who are you?"
        }
    }
    chat_url = f"{base_url}/chat"""
    response = requests.post(chat_url, json=payload, headers=headers, stream=True)
    response.raise_for_status()
    model_answer = ""
    for line in response.iter_lines():
        print(line)
        response_message = json.loads(line)
        # collection model answer in ResponseMessage
        if response_message["content_type"] == "model_stream" and response_message["is_final"]:
            model_answer += response_message["content"]
    print("Model answer:", model_answer)

    # Process the stream ResponseMessage, handle document references
    payload = {
        "conversation_id": conversation_id,
        "message": {
            "role": "user",
            "content": "什么是机器学习的三要素？"
        }
    }
    response = requests.post(chat_url, json=payload, headers=headers, stream=True)
    response.raise_for_status()
    retrieved_docs = {}
    model_answer = ""
    for line in response.iter_lines():
        print(line)
        response_message = json.loads(line)
        if response_message["content_type"] == "retriever_output":
            retrieved_docs = response_message["content"]
        if response_message["content_type"] == "model_stream" and response_message["is_final"]:
            model_answer += response_message["content"]
    process_answer_references(model_answer, retrieved_docs)

    # List the conversation history messages
    messages_url = f"{base_url}/conversations/{conversation_id}/messages"
    response = requests.get(messages_url, headers=headers)
    response.raise_for_status()
    print(f"Request {conversation_url}, response: \n", response.json())

    # Monitor token usage
    usage_url = f"{base_url}/usage/token"
    end_time = datetime.datetime.now()
    begin_time = end_time - datetime.timedelta(days=1)
    response = requests.get(usage_url, params={"begin_time": begin_time, "end_time": end_time}, headers=headers)
    response.raise_for_status()
    print(f"Request {usage_url}, response: \n", response.json())


if __name__ == "__main__":
    main()

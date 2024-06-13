from flask import Flask, render_template, request, jsonify
from src.helper import download_embedding

from langchain_pinecone import PineconeVectorStore

from langchain_community.llms import CTransformers # Using ctransfomers since we are using a quantized model

from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from src.prompt import *

load_dotenv()

app = Flask(__name__)

# Download the embedding model
embeddings = download_embedding()

# Use the embeddings the was created with store_index.py
index_name = "medical-chatbot"
vectorstore = PineconeVectorStore(embedding = embeddings, index_name = index_name)
retriever = vectorstore.as_retriever()

# Create the prompt template for the llm to process.
PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", prompt_template), 
        ("human", "{input}")
    ]
)

# Create a ctransformers model of the llm
llm = CTransformers(model = "model/llama-2-7b-chat.ggmlv3.q4_0.bin",
                    model_type = "llama",
                    config = {'max_new_tokens': 512,
                              'temperature': 0.8})

question_answer_chain = create_stuff_documents_chain(llm, PROMPT)
chain = create_retrieval_chain(retriever, question_answer_chain)


@app.route("/")
def home():
    return render_template('chat.html')

@app.route("/get", methods=["POST", "GET"])
def chat():
    msg = request.form['msg']
    input = msg
    print(input)
    result = chain.invoke({"input": input})
    print("Response : ",result["answer"])
    return result["answer"]

if __name__ == '__main__':
    app.run(port = 8080, debug = True)
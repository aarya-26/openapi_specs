from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import yaml
import os
import json

api_key = os.getenv("api_key")

def load_knowledgeBase():
        embeddings=OpenAIEmbeddings(api_key=api_key)
        DB_FAISS_PATH = 'vectorstore/db_faiss'
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        return db
        
#function to load the OPENAI LLM
def load_llm():
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1, api_key=api_key)
        return llm

#creating prompt template using langchain
def load_prompt():
        prompt = """ You are a Senior Software Engineer. You will be provided with questions and related data. Your task is to Answer the question based on the following context:.
        context = {context}
        question = {question}
        
        You are also an expert in understanding provided API specs, including synchronous and asynchronous modes to answer any question related to the specs
        """
        prompt = ChatPromptTemplate.from_template(prompt)
        return prompt


def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

  
from flask import Flask, request, jsonify
from flask_cors import CORS

# RESPONSE_DIR = 'final_generated'
# os.makedirs(RESPONSE_DIR, exist_ok=True)


# Initialize Flask application
app = Flask(__name__)
CORS(app, origins="*")

# Define a route for the base endpoint

def read_file(path):
    with open(path, 'r') as file:
        content = file.read()
    return content

@app.route('/generate', methods = ["GET", "POST"])
def generate():
    knowledgeBase=load_knowledgeBase()
    llm=load_llm()
    prompt=load_prompt()
    print("reachedd")
    query = request.json.get("query")
    
    if(query):
        #getting only the chunks that are similar to the query for llm to produce the output
        similar_embeddings=knowledgeBase.similarity_search(query)
        similar_embeddings=FAISS.from_documents(documents=similar_embeddings, embedding=OpenAIEmbeddings(api_key=api_key))
                
        #creating the chain for integrating llm,prompt,stroutputparser
        retriever = similar_embeddings.as_retriever()
        rag_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                        | llm
                        | StrOutputParser()
                    )
                
        response=rag_chain.invoke(query)
        print(response)

        # try:
        #     # Parse the response
        #     response_data = json.loads(response)

        #     # Extract and save sync specs
        #     sync_specs = response_data[0].get('specs(sync)', {})
        #     sync_title = sync_specs.get('info', {}).get('title', 'sync')
        #     sync_yaml_path = os.path.join(RESPONSE_DIR, f"{sync_title}.yaml")
        #     with open(sync_yaml_path, 'w') as sync_file:
        #         yaml.dump(sync_specs, sync_file, sort_keys=False)
        #     print(f"Sync specs saved to {sync_yaml_path}")

        #     # Extract and save async specs
        #     async_specs = response_data[1].get('specs(async)', {})
        #     async_title = async_specs.get('info', {}).get('title', 'async')
        #     async_yaml_path = os.path.join(RESPONSE_DIR, f"{async_title}.yaml")
        #     with open(async_yaml_path, 'w') as async_file:
        #         yaml.dump(async_specs, async_file, sort_keys=False)
        #     print(f"Async specs saved to {async_yaml_path}")

        # except json.JSONDecodeError as e:
        #     print(f"Failed to parse response as JSON: {e}")
        # except Exception as e:
        #     print(f"An unexpected error occurred: {e}")

    return response


# Run the application
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000, debug=True)
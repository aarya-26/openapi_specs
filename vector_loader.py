from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os

api_key = os.getenv("api_key")

if __name__=="__main__":
        DB_FAISS_PATH = 'vectorstore/db_faiss'
        list_data = []
        directory = './files'
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as file:
                    data = file.read()
                    list_data.append(data)
        vectorstore = FAISS.from_texts(texts=list_data, embedding=OpenAIEmbeddings(api_key=api_key))
        vectorstore.save_local(DB_FAISS_PATH)

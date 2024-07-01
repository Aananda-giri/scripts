import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from `langchain`.embeddings import CohereEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.llms import Cohere

# Set Cohere API key
# os.environ["COHERE_API_KEY"] = userdata.get('COHERE_API_KEY')
# from google.colab import userdata
from dotenv import load_dotenv
load_dotenv()

# Load PDF
print('loading PDF...')
loader = PyPDFLoader("1706.03762v7.pdf")
documents = loader.load() # Each document is seperate page of pdf
print(f"Number of documents: {len(documents)}")

# Split text into chunks
print('splitting text...')
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(documents)

# Create embeddings using Cohere
print('creating embedding...')
embeddings = CohereEmbeddings()

# Create vector store
print('creating vector store...')
db = FAISS.from_documents(texts, embeddings)

# Initialize Cohere model
print('initializing Cohere model...')
llm = Cohere(model="command")  # You can also use "command-light" for a smaller model

# Create retrieval-based QA chain
print('creating retrieval-based QA chain...')
qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=db.as_retriever())

# Chat loop
while True:
    query = input("Ask a question about your PDF (or type 'quit' to exit): ")
    if query.lower() == 'quit':
        break
    response = qa_chain.run(query)
    print(response)
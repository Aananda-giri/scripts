# -----------------------------------
# Saving embeddings to pinecone
# -----------------------------------
#Import Python modules
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google.colab import userdata
import os

# Set pinecone api key
os.environ['PINECONE_API_KEY']  = userdata.get('PINECONE_API_KEY')

# Set Gemini API key
#export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
os.environ['GOOGLE_API_KEY']=userdata.get('GEMINI_API_KEY')

index_name = "pdf-index"
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)

#Load the models
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,

    },
)

from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.vectorstores import Chroma

import re

def remove_non_english(text):
    # This pattern keeps English letters, numbers, spaces, and basic punctuation
    pattern = re.compile(r'[^a-zA-Z0-9\s.,!?"-]')
    return pattern.sub('', text)

#Load the models
llm = ChatGoogleGenerativeAI(model="gemini-pro")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

namespace = ["https://arxiv.org/pdf/1706.03762", "art-of-war"]
file_paths = ["/content/1706.03762v7.pdf", "/content/art of war -Sant tuz.pdf"]
for file_path, namespace in zip(file_paths, namespace):
    #Load the PDF and create chunks
    loader = PyPDFLoader(file_path)
    text_splitter = CharacterTextSplitter(
        separator=".",
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    docs = loader.load_and_split(text_splitter) # pages
    for d in docs:
      d.page_content = remove_non_english(d.page_content)


    # Initialize vector store
    vectorstore_from_docs = PineconeVectorStore.from_documents(
            docs,
            index_name=index_name,
            embedding=embeddings,
            namespace=namespace  # namespace to differentiate between two pdfs
    )
    # Add documents
    vectorstore_from_docs.add_documents(docs)

query1 ='what is transformers architecture based on given text?'
query2 ='What are five ways of attacking with fire based on given text?'
'''
# search by source
vectorstore_from_docs.similarity_search(query, k=5, namespace='art-of-war')
# Search by namespace
vectorstore_from_docs.similarity_search(query, k=5, namespace="https://arxiv.org/pdf/1706.03762")
'''


# --------------------
# Inference
# --------------------
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langchain.text_splitter import TokenTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from google.colab import userdata

# Set pinecone api key
os.environ['PINECONE_API_KEY']  = userdata.get('PINECONE_API_KEY')

# Set Gemini API key
#export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
os.environ['GOOGLE_API_KEY']=userdata.get('GEMINI_API_KEY')

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

llm = ChatGoogleGenerativeAI(
    model= "gemini-pro",  # 'gemini-1.5-flash',
    safety_settings={
        HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DEROGATORY: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_TOXICITY: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_VIOLENCE: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUAL: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_MEDICAL: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,

    },
)

# Initialize Pinecone vector store
index_name = 'pdf-index'
vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings,
    pinecone_api_key=userdata.get('PINECONE_API_KEY'),
    namespace='art-of-war'
)

# Set up the retriever with custom search parameters
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Create the prompt template
template = """
You are a helpful AI assistant. Answer based on the context provided.
If the answer cannot be found in the context, say "I don't have enough information to answer that question."

Context: {context}
Question: {input}

Answer:
"""
prompt = PromptTemplate.from_template(template)

# Create the retrieval chain
combine_docs_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

# Chat loop
while True:
    query = input("Ask a question about your PDF (or type 'quit' to exit): ")
    if query.lower() in ['quit', 'q']:
        break

    try:
        response = retrieval_chain.invoke({"input": query})
        print("\nResponse:", response)
        print("\nAnswer:", response["answer"])
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
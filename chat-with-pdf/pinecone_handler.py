#Import Python modules
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import CharacterTextSplitter
from langchain.vectorstores import Chroma
import os
# pip install pinecone-client[grpc]
from pinecone.grpc import PineconeGRPC as Pinecone
import re
import sys

# Load the environment variables
if 'google.colab' in sys.modules:
    # Code is running in google colab
    from google.colab import userdata
    
    # Set pinecone api key
    os.environ['PINECONE_API_KEY']  = userdata.get('PINECONE_API_KEY')    

    # Set Gemini API key
    #export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    os.environ['GOOGLE_API_KEY']=userdata.get('GEMINI_API_KEY')
else:
    # Code is running in local
    from dotenv import load_dotenv
    load_dotenv()

class PineconeHandler:
    def __init__(self, index_name = "pdf-index"):
        self.pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
        self.index_name = index_name
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        #Load the models
        self.llm = ChatGoogleGenerativeAI(
            model = "gemini-pro",  # 'gemini-1.5-flash',
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

        # make space for new documents if vector count is greater than 100,000
        self.clear_pinecone_memory()

    def get_current_vector_count(self):
        index = self.pc.Index(self.index_name)
        stats = index.describe_index_stats()
        current_vector_count = stats['total_vector_count']
        return current_vector_count
    
    def display_stats(self):
        total_capacity = 200000
        index = self.pc.Index(self.index_name)
        stats = index.describe_index_stats()
        print(stats)
        # Current number of vectors
        current_vector_count = stats['total_vector_count']

        # Get the dimension of vectors in your index
        dimension = stats['dimension']
        # Calculate remaining capacity
        remaining_vectors = total_capacity - current_vector_count
        usage_percentage = (current_vector_count / total_capacity) * 100
        print(f"current_vector_count : {current_vector_count}")
        print(f"Remaining vectors: {remaining_vectors}")
        print(f"usage_percentage storage: {usage_percentage:.2f} MB")
    
    def remove_non_english(self, text):
        # This pattern keeps English letters, numbers, spaces, and basic punctuation
        pattern = re.compile(r'[^a-zA-Z0-9\s.,!?"-]')
        return pattern.sub('', text)

    
    def load_and_split_documents(self, file_path, delete_file_afterwords=False):
        #Load the PDF and create chunks
        loader = PyPDFLoader(file_path)
        text_splitter = CharacterTextSplitter(
            separator=".",
            chunk_size=1000,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        docs = loader.load_and_split(text_splitter) # pages
        for d in docs:
            d.page_content = self.remove_non_english(d.page_content)
        
        print(f"Loaded and split {len(docs)} documents from '{file_path}'")
        return docs

        if delete_file_afterwords:
            os.remove(file_path)
    
    def add_docs_to_pinecone(self, docs, index_name, namespace):
        """
        Add all documents to Pinecone index at once.
        
        :param docs: List of documents to add
        :param index_name: Name of the Pinecone index
        :param namespace: Namespace to add documents to
        :return: Number of documents successfully added
        """
        self.namespace = namespace
        index = self.pc.Index(index_name)
        if namespace in index.describe_index_stats()['namespaces']:
            print(f".Namespace '{namespace}' already exists in index '{index_name}'. Skipping...")
            return 0
        
        try:
            # Create embeddings and add all documents at once
            vectorstore = PineconeVectorStore.from_documents(
                documents=docs,
                embedding=self.embeddings,
                index_name=index_name,
                namespace=namespace
            )
            
            docs_added = len(docs)
            print(f"Successfully added {docs_added} documents to namespace '{namespace}' in index '{index_name}'")
            return docs_added
        except Exception as e:
            print(f"Error adding documents to Pinecone: {e}")
            return 0
        # Example usage:
        # docs = [your_documents_here]
        # index_name = "your-index-name"
        # namespace = "your-namespace"
        # added_count = add_docs_to_pinecone(docs, index_name, namespace)
    
    def similarity_search(self, query, k=5, namespace=None):
        """
        Search for similar documents in Pinecone index.
        
        :param query: Query text to search for
        :param k: Number of similar documents to return
        :param namespace: Namespace to search in
        :return: List of k most similar documents
        """

        if namespace:
            self.namespace = namespace
            
        # Initialize Pinecone vector store
        vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            pinecone_api_key=os.environ.get('PINECONE_API_KEY'),
            namespace=self.namespace
            )
        try:
            # Search for similar documents
            results = vectorstore.similarity_search(query, k=k, namespace=namespace)
            return results
        except Exception as e:
            print(f"Error searching for similar documents: {e}")
            return []
    
    def get_retrieval_chain(self, namespace=None):
        """
        RetrievalChain: gets gemini retriever chain
        
        :param namespace: Namespace to search in
        :return: gemini retriever chain
        """

        if namespace:
            self.namespace = namespace
        # Initialize Pinecone vector store
        vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            pinecone_api_key=os.environ.get('PINECONE_API_KEY'),
            namespace=self.namespace
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
        combine_docs_chain = create_stuff_documents_chain(self.llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
        return retrieval_chain

    def chat(self, query, namespace=None):
        """
        Chat with generative AI model with the given text as RAG.
        
        :param query: Query text to search for
        :param namespace: Namespace to search in
        :return: List of similar documents
        """
        
        retrieval_chain = self.get_retrieval_chain(namespace)
        try:
            response = retrieval_chain.invoke({"input": query})
            print("\nResponse:", response)
            print("\nAnswer:", response["answer"])
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
        
    def delete_namespace(self, namespace):
        try:
          index = self.pc.Index(self.index_name)
          index.delete(delete_all=True, namespace=namespace)
          print(f"Successfully deleted namespace '{namespace}'")
        except Exception as e:
          print(f"Error deleting namespace '{namespace}': {e}")
    
    def clear_pinecone_memory(self):
        # delete namespaces till vector_count > 100,000
        print(f'Clearing memory...')
        self.display_stats()

        index = self.pc.Index(self.index_name)
        namespaces = list(index.describe_index_stats()['namespaces'].keys())
        for namespace in namespaces:
            
            if not self.get_current_vector_count() > 50000:
                # stop deleting namespaces if vector count is less than 2000
                break
            
            self.display_stats()
            
            self.delete_namespace(namespace)

            print(f'deleting namepsace: {namespace}')
            self.delete_namespace(namespace)
    
if __name__ == "__main__":
    pinecone_handler = PineconeHandler()
    pinecone_handler.display_stats()
    # pinecone_handler.clear_pinecone_memory()
    # pinecone_handler.delete_namespace('https://arxiv.org/pdf/1706.03762')
    # pinecone_handler.delete_namespace("art-of-war")
    
    
    # # Add documents to Pinecone
    # namespace = ["https://arxiv.org/pdf/1706.03762", "art-of-war"]
    # file_paths = ["/content/1706.03762v7.pdf", "/content/art of war -Sant tuz.pdf"]

    # # upload files to pinecone
    # for file_path, namespace in zip(file_paths, namespace):
    #     docs = pinecone_handler.load_and_split_documents(file_path)
    #     if docs:
    #       added_count = pinecone_handler.add_docs_to_pinecone(docs, "pdf-index", namespace)
    #       print(f"Added {added_count} documents to namespace '{namespace}'")
    #       pinecone_handler.display_stats()

    # pinecone_handler.display_stats()

    # # Perform similarity search
    # query1 ='What are five ways of attacking with fire based on given text?' 
    # query2 ='what is transformers architecture based on given text?'
    
    # # Similarity search
    # results = pinecone_handler.similarity_search(query2, k=5, namespace='art-of-war')
    # print(f'Similar documents for query "{query1}" in namespace:`art-of-war`: {results}')

    # results = pinecone_handler.similarity_search(query2, k=5, namespace='https://arxiv.org/pdf/1706.03762')
    # print(f'Similar documents for query "{query2}" in namespace:`https://arxiv.org/pdf/1706.03762`: {results}')
    
    # # Chat with generative AI model
    # pinecone_handler.chat(query1, namespace='art-of-war')
    # pinecone_handler.chat(query2, namespace='https://arxiv.org/pdf/1706.03762')
    pinecone_handler.display_stats()






"""
# references:
1. (forum:get available vector space)[https://community.pinecone.io/t/inquiry-about-storage-consumption-in-pinecone/2359]
2. (forum:free plan limits)[https://community.pinecone.io/t/limit-of-vectors-on-free-plan/3821]

from [2] you get approximately 100,000 vectors with 1536-dimensional embeddings .
we are using 768 dimensional embeddings. So we get 200,000 vectors in pinecone
"""

'''
# search by source
vectorstore_from_docs.similarity_search(query, k=5, namespace='art-of-war')
# Search by namespace
vectorstore_from_docs.similarity_search(query, k=5, namespace="https://arxiv.org/pdf/1706.03762")
'''
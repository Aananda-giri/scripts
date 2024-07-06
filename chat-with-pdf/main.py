# %%writefile main.py
from download_functions import download_pdf, download_google_drive_file, is_google_drive_link
from pinecone_handler import PineconeHandler

def chat(pdf_url, file_name):
    '''
    Chat
        Chat with pdf.
        :param pdf_url: google_drive_file or other pdf link
        :return: List of k most similar documents
    
    Pseudo code:
        1. Download pdf
        2. Extract text from pdf
        3. Upload text to pinecone
        4. Search similar documents
        5. User query, similar documents to chat with pdf
    '''
    is_drive_link, drive_file_id = is_google_drive_link(pdf_url)
    if is_drive_link:
        print("Downloading google drive file")
        downloaded = download_google_drive_file(drive_file_id, file_name)
        if not downloaded: return
    else:
        download_pdf(pdf_url, file_name)
    pinecone_handler = PineconeHandler()

    # Add documents to Pinecone
    namespace = pdf_url
    file_path = file_name

    # upload files to pinecone
    docs = pinecone_handler.load_and_split_documents(file_path)
    added_count = pinecone_handler.add_docs_to_pinecone(docs, "pdf-index", namespace)
    print(f"Added {added_count} documents to namespace '{namespace}'")
    pinecone_handler.display_stats()
    
    retrieval_chain = pinecone_handler.get_retrieval_chain(namespace)
    while True:
        query = input("\nAsk me anything about pdf:\n q to quit\n input: ")
        if query.lower() == "q":
            break
        try:
            response = retrieval_chain.invoke({"input": query})
            print("\nResponse:", response)
            print("\nAnswer:", response["answer"])
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
    # # Chat with generative AI model
    # pinecone_handler.chat(query1, namespace='art-of-war')
    # pinecone_handler.chat(query2, namespace='https://arxiv.org/pdf/1706.03762')
    pinecone_handler.display_stats()
        
if __name__ == "__main__":
    # (Google Drive pdf) Example usage
    url = "https://drive.google.com/file/d/1neonffR5MRU3Rm8UbKHuLAkTLN3C-Om2/view"
    output_path = "of_studies.pdf"

    chat(url, output_path)

    # # (Normal pdf) Example usage
    # url = "https://abhashacharya.com.np/wp-content/uploads/2017/12/Spot-Speed-Study.pdf"
    # save_path = "Spot-Speed-Study.pdf"

    # chat(url, save_path)
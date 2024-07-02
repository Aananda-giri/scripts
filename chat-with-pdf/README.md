# References:
* [Generative AI Course](https://www.youtube.com/watch?v=mEsleV16qdo&t=53561s)
* [colab code](https://colab.research.google.com/drive/1SRg7A_J_uaNMY44ZjSXvixruzldPpUNn?authuser=4#scrollTo=8wYOBaQYPNdH&uniqifier=1)
* [pinecone-langchain docs](https://docs.pinecone.io/integrations/langchain)
* [langchain-docs](https://python.langchain.com/v0.1/docs/integrations/chat/google_generative_ai/)


# Pseudocode:
* [ ] download pdf from google drive or url
* [ ] if it does not exists in vector store:
        split into chunks
        get embeddings
        add embeddings, source_url to vector store
* [ ] Perform similarity search to get chunks with text similar to query
* [ ] use llm(similar_chunks, query) to get response

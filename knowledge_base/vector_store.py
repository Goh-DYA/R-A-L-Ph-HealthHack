# Module for connecting to and querying the vector database.

# from langchain.embeddings.openai import OpenAIEmbeddings   # deprecated
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_iris import IRISVector
from config import IRIS_CONNECTION_STRING, IRIS_COLLECTION_NAME


class KnowledgeBase:
    """
    Handles interactions with the IRIS vector database.
    """
    
    def __init__(self):
        """Initialize the knowledge base with embeddings and database connection."""
        # Initialize embedding model
        self.embeddings = OpenAIEmbeddings()
        
        # Connect to the database
        self.db = IRISVector(
            embedding_function=self.embeddings,
            dimension=1536,
            collection_name=IRIS_COLLECTION_NAME,
            connection_string=IRIS_CONNECTION_STRING,
        )
    
    def get_document_count(self):
        """
        Get the number of documents in the vector store.
        
        Returns:
            int: Number of documents
        """
        return len(self.db.get()['ids'])
    
    def search(self, query, top_docs=5):
        """
        Search knowledge base for relevant documents.
        
        Args:
            query (str): The search query
            top_docs (int): Number of top documents to return
            
        Returns:
            tuple: (xml_content, metadata_list, score_list)
        """
        # Run similarity search
        docs_with_score = self.db.similarity_search_with_score(query, top_docs)
        
        # Prepare results
        metadata_list = []
        score_list = []
        xml_content = ""
        
        # Format results as XML
        for i, (doc, score) in enumerate(docs_with_score):
            metadata_list.append(doc.metadata)
            score_list.append(score)
            xml_content += f'<content id="{i}">\n{doc.page_content}\n</content>\n\n'
            
        return xml_content, metadata_list, score_list
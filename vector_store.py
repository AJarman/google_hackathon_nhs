# stdlib
import os
from string import Template
from typing import Type


# langchain stuff for embdeddings/ vector store
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import GCSFileLoader

from google.cloud import storage


# display
from IPython.display import display, Markdown

from typing import Optional, Union, Dict, List
import getpass
from google.cloud import storage



GCP_BUCKET = "vectorstore_hackathon"
GCP_PROJECT = "AI in Health Hackathon-6309"
FAISS_DIRECTORY = "opcs4-faiss"


class VectorStoreWrapper:
    """
    Base class for Vector Store Wrappers
    """


    def __init__(self, loader=None):

        # Chroma db placeholder
        self.db:Optional[FAISS] = None
        # determines if embeddedings created
        self.created=False
        self.loader = loader
        return

    def create_embeddings(self, docs:list=None)->Type["VectorStoreWrapper"]:
        """
        Use the vertex ai embeddings model to create and store the embeddings.
        Note returns itself (sort of like sklearn .fit())
        """


        embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004")
        if docs is None:
            docs = self.loader.load()

        self.db = FAISS.from_documents(docs, embeddings)
        self.created=True
        return self

    def retrieve(self, query, k=1):
      if self.created:
        # TODO: Need to tune number retreived
        return self.db.as_retriever(search_type="mmr", k=k).invoke(query)
      else:
          raise ValueError("Vertex ai embeddings are not yet created, call ")

    #todo
    def __save_to_directory(self, directory_path=FAISS_DIRECTORY):
          self.db.save_local(directory_path)
          return
     #todo
    def __load_from_directory(self, directory_path=FAISS_DIRECTORY):
            # load file and save to db attribute
            # extract filename data from documents metadata
            #
            self.db = FAISS.load_local(directory_path,
                                      self.embeddings,
                                      allow_dangerous_deserialization=True)
            return self


    def save_faiss_vectors_from_bucket(self,bucket_name=GCP_BUCKET, project_id=GCP_PROJECT, directory_path=FAISS_DIRECTORY):
        """
        Saves FAISS vectors (assuming IVF index) to a file in a GCP bucket.

        Args:
            bucket_name: Name of the GCP bucket for storage.
            project_id: GCP project ID associated with the bucket.
            directory_path: Local directory path containing serialized FAISS index files.
            index: The FAISS index object to be serialized (optional, for validation).
        """
        self.__save_to_directory(directory_path=directory_path)

        # Create a storage client
        client = storage.Client(project=project_id)

        # Get the bucket object
        bucket = client.bucket(bucket_name)

        # Upload all files within the directory
        for filename in os.listdir(directory_path):
            # Construct full local and remote paths
            local_file = os.path.join(directory_path, filename)
            remote_file = os.path.join(directory_path, filename)  # Remote path mirrors local structure

            # Upload the file
            blob = bucket.blob(remote_file)
            blob.upload_from_filename(local_file)

        print(f"FAISS vectors (IVF index) saved to gs://{bucket_name}/{directory_path}")


    def load_vectors(self,
                     bucket_name=GCP_BUCKET, 
                     project_id=GCP_PROJECT, 
                     directory_path=FAISS_DIRECTORY):
        """
        Loads FAISS vectors from the GCP bucket and assigns them to the `db` attribute.
        """

        # Validation (optional)
        if self.db is not None:
            raise ValueError("FAISS vectors already loaded in this instance.")

        # Create a storage client
        client = storage.Client(project=project_id)

        # Get the bucket object
        bucket = client.bucket(bucket_name)
        
        # make directory in filepath
        os.makedirs(directory_path, exist_ok=True)

        # find all files in directory in the bucket
        blobs = bucket.list_blobs(prefix=directory_path)

        # Download all files within the directory
        for blob in blobs:
            # Download the file
            blob.download_to_filename(blob.name)
            print(f"downloading {bucket}/{blob.name}")

        self.db = FAISS.load_local(directory_path, 
                                   embeddings=GoogleGenerativeAIEmbeddings(
                                       model="models/text-embedding-004"), 
                                   allow_dangerous_deserialization=True)
        
        self.created = True

        print(f"FAISS vectors loaded from gs://{bucket_name}/{directory_path}")
        return self

class GCPCSVLoader:
    def __init__(self):
        self.gcp_loader = GCSFileLoader(
            bucket="vectorstore_hackathon",
            blob="OPCS4_Filtered - OPCS4_Filtered.csv",
            project_name='AI in Health Hackathon-6309',
            loader_func=self.__csv_loader,)

    def load(self):
        docs = self.gcp_loader.load()

        #delete useless information
        for i in range(len(docs)):
            del docs[i].metadata["source"]
            del docs[i].metadata["row"]

        return docs


    def __csv_loader(self, csv_):
        return CSVLoader(csv_,
                          source_column="OPCS4",
                          metadata_columns=["Description", "Location"])



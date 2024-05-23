from setuptools import setup

setup(
  name="vector_store",
  version="1.0.0",  # Adjust version number as needed
  description="A package for managing vector data",
  py_modules=["langchain-google-genai", 
              "langchain_community",
              "langchain",
              "faiss-cpu", 
              "unstructured",
              "google-cloud-storage",],
)
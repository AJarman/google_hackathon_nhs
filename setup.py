from setuptools import setup

setup(
  name="esneft_hack_vector_store",
  version="1.0.0",  # Adjust version number as needed
  description="A package for managing vector data",
  py_modules=["vector_store"],
  install_requires=["langchain-google-genai", 
              "langchain_community",
              "langchain",
              "faiss-cpu", 
              "unstructured",
              "google-cloud-storage",],
)
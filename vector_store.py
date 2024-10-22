import os
import json
import requests
import zipfile
import io
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DataFrameLoader


def initialize_vector_store():
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
    QDRANT_CLUSTER_URL = os.environ.get("QDRANT_CLUSTER_URL")

    qdrant_client = QdrantClient(url=QDRANT_CLUSTER_URL,
                                 api_key=QDRANT_API_KEY)

    collections = qdrant_client.get_collections()
    collection_names = [
        collection.name for collection in collections.collections
    ]

    if "fda_drugs" not in collection_names:
        print("Collection 'fda_drugs' is not present. Creating...")

        # Download and process FDA drug data
        url = "https://download.open.fda.gov/drug/label/drug-label-0001-of-0012.json.zip"
        response = requests.get(url)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        json_file = zip_file.open(zip_file.namelist()[0])
        data = json.load(json_file)

        df = pd.json_normalize(data['results'])

        metadata_fields = [
            'openfda.brand_name', 'openfda.generic_name',
            'openfda.manufacturer_name', 'openfda.product_type',
            'openfda.route', 'openfda.substance_name', 'openfda.rxcui',
            'openfda.spl_id', 'openfda.package_ndc'
        ]

        text_fields = [
            'description', 'indications_and_usage', 'contraindications',
            'warnings', 'adverse_reactions', 'dosage_and_administration'
        ]

        df[text_fields] = df[text_fields].fillna('')
        df['content'] = df[text_fields].apply(
            lambda x: ' '.join(x.astype(str)), axis=1)

        loader = DataFrameLoader(df, page_content_column='content')
        drug_docs = loader.load()

        for doc, row in zip(drug_docs, df.to_dict(orient='records')):
            metadata = {}
            for field in metadata_fields:
                value = row.get(field)
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value if pd.notna(v))
                elif pd.isna(value):
                    value = 'Not Available'
                metadata[field] = value
            doc.metadata = metadata

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                       chunk_overlap=100)
        split_drug_docs = text_splitter.split_documents(drug_docs)

        qdrant_vectorstore = Qdrant.from_documents(split_drug_docs,
                                                   embedding_model,
                                                   url=QDRANT_CLUSTER_URL,
                                                   api_key=QDRANT_API_KEY,
                                                   collection_name="fda_drugs")
    else:
        print("Collection 'fda_drugs' is present. Loading...")
        qdrant_vectorstore = Qdrant(client=qdrant_client,
                                    collection_name="fda_drugs",
                                    embeddings=embedding_model)

    return qdrant_vectorstore

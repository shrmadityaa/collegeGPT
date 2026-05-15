import pickle
import faiss
import numpy as np

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


class CollegeRetriever:

    def __init__(self):

        self.model = SentenceTransformer(MODEL_NAME)

        self.index = faiss.read_index(
            "vectorstore/collegegpt.index"
        )

        with open(
            "vectorstore/chunks.pkl",
            "rb"
        ) as f:

            self.chunks = pickle.load(f)

    def search(
        self,
        query,
        top_k=5
    ):

        query_embedding = self.model.encode(
            [query]
        )

        distances, indices = self.index.search(
            np.array(query_embedding),
            top_k
        )

        results = []

        for idx in indices[0]:

            results.append(
                self.chunks[idx]
            )

        return results
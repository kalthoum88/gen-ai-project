
import json
import os
import time
from pathlib import Path
from functools import lru_cache
from getpass import getpass

import numpy as np
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import errors


# --------------------------------------------------
# 1. PROJECT PATHS AND SETTINGS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "restaurants.json"

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

MODEL_NAME = "gemini-3.1-flash-lite"


# --------------------------------------------------
# 2. LOAD RESTAURANT DATABASE
# --------------------------------------------------

@lru_cache(maxsize=1)
def load_restaurants():
    with open(DATABASE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_restaurant_id(restaurant_id):
    restaurant_id = restaurant_id.strip().lower().replace(" ", "_")

    if restaurant_id not in load_restaurants():
        raise ValueError(f"Unknown restaurant: {restaurant_id}")

    return restaurant_id


# --------------------------------------------------
# 3. CREATE SEARCHABLE DOCUMENTS
# --------------------------------------------------

@lru_cache(maxsize=1)
def build_documents():
    restaurant_data = load_restaurants()
    documents = []

    for restaurant_id, restaurant in restaurant_data.items():

        general_info = f"""
        Restaurant: {restaurant['name']}
        Opening hours: {restaurant['opening_hours']}
        Delivery zones and prices: {restaurant['delivery_zones']}
        Promotion: {restaurant['promotion']}
        """

        documents.append({
            "text": general_info,
            "restaurant_id": restaurant_id,
            "type": "general"
        })

        for pizza in restaurant["items"]:
            pizza_info = f"""
            Restaurant: {restaurant['name']}
            Pizza: {pizza['name']}
            Prices by size: {pizza['sizes']}
            Ingredients: {pizza['ingredients']}
            Allergens: {pizza['allergens']}
            """

            documents.append({
                "text": pizza_info,
                "restaurant_id": restaurant_id,
                "type": "menu"
            })

    return documents


# --------------------------------------------------
# 4. LOAD EMBEDDING MODEL AND CREATE VECTORS
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


@lru_cache(maxsize=1)
def get_document_embeddings():
    documents = build_documents()
    texts = [doc["text"] for doc in documents]

    model = get_embedding_model()

    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )


# --------------------------------------------------
# 5. RETRIEVE RELEVANT DOCUMENTS
# --------------------------------------------------

def retrieve_documents(question, restaurant_id, top_k=3):

    restaurant_id = normalize_restaurant_id(restaurant_id)

    documents = build_documents()
    embeddings = get_document_embeddings()
    model = get_embedding_model()

    query_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    # Normalized vectors allow cosine similarity
    # to be calculated using the dot product.
    scores = embeddings @ query_embedding

    candidates = [
        index
        for index, document in enumerate(documents)
        if document["restaurant_id"] == restaurant_id
    ]

    best_indices = sorted(
        candidates,
        key=lambda index: scores[index],
        reverse=True
    )[:top_k]

    results = [
        {
            **documents[index],
            "score": float(scores[index])
        }
        for index in best_indices
    ]

    # Include general restaurant information
    # if it was not retrieved among the top results.
    if not any(result["type"] == "general" for result in results):
        general_index = next(
            index
            for index in candidates
            if documents[index]["type"] == "general"
        )

        results.append({
            **documents[general_index],
            "score": float(scores[general_index])
        })

    return results


# --------------------------------------------------
# 6. GEMINI CLIENT AND API RETRIES
# --------------------------------------------------
@lru_cache(maxsize=1)
def get_client():
    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        api_key = getpass("Enter your Google API key: ")

    return genai.Client(api_key=api_key)


def generate_text(prompt, max_retries=4):

    client = get_client()

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            return (response.text or "").strip()

        except errors.APIError as error:
            if error.code in (429, 503) and attempt < max_retries - 1:
                wait = 6 * (attempt + 1)
                print(f"API error {error.code}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# --------------------------------------------------
# 7. MULTILINGUAL QUESTION NORMALIZATION
# --------------------------------------------------

def normalize_question(question):

    prompt = f"""
Translate this customer question into English.

Understand:
- French
- Algerian Darija
- Darija written in Arabic script
- Arabizi (Darija written with Latin letters and numbers)

Rules:
- Preserve restaurant and pizza names.
- Preserve sizes and quantities.
- Do not answer the question.
- Return only the English translation.

Customer question:
{question}

English translation:
"""

    return generate_text(prompt)


# --------------------------------------------------
# 8. BUILD THE GROUNDED ANSWER PROMPT
# --------------------------------------------------

def build_rag_prompt(question, results):

    context = "\n\n".join(
        result["text"] for result in results
    )

    return f"""
You are a helpful multilingual pizza ordering assistant.

Answer using ONLY the information in the context.

LANGUAGE RULES:
1. English question: answer in English.
2. French question: answer in French.
3. Darija in Arabic script: answer in Darija using Arabic script.
4. Arabizi: answer in Arabizi.
5. Do not change the customer's language unnecessarily.

INFORMATION RULES:
1. Never invent prices, ingredients, allergens or restaurant details.
2. If information is missing, say that you do not know.
3. For allergy questions, mention only listed allergens.
4. Explain that cross-contamination cannot be ruled out
   and that allergen safety cannot be guaranteed.
5. Be polite and concise.
6. Write all prices in Algerian dinars (DA).

CONTEXT:
{context}

CUSTOMER QUESTION:
{question}

ANSWER:
"""


# --------------------------------------------------
# 9. COMPLETE RAG QUESTION-ANSWERING FUNCTION
# --------------------------------------------------

def ask_restaurant_assistant(question, restaurant_id, top_k=3):

    restaurant_id = normalize_restaurant_id(restaurant_id)

    # Translate for better multilingual retrieval.
    normalized_question = normalize_question(question)

    results = retrieve_documents(
        normalized_question,
        restaurant_id,
        top_k=top_k
    )

    # Keep the original question so the answer
    # follows the customer's language.
    prompt = build_rag_prompt(question, results)

    return generate_text(prompt)

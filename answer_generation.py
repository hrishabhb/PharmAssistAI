from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.llms.base import LLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Optional, List, Mapping, Any
import requests

# Ensure LLAMA_API_ENDPOINT and llamaapi_request are defined
LLAMA_API_ENDPOINT = "https://n9f72yljeh.execute-api.us-west-2.amazonaws.com/default/llama-hackathon"

def llamaapi_request(prompt, max_tokens=500):
    headers = {"Content-Type": "application/json"}
    data = {"prompt": prompt, "max_tokens": max_tokens}
    try:
        response = requests.post(LLAMA_API_ENDPOINT,
                                 headers=headers,
                                 json=data)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Llama API: {e}")
        return ""

# Custom Llama LLM class
class LlamaLLM(LLM):
    max_tokens: int = 500  # Default max tokens

    def __init__(self, max_tokens: int = 500, **kwargs):
        super().__init__(**kwargs)
        self.max_tokens = max_tokens

    @property
    def _llm_type(self) -> str:
        return "llama"

    def _call(self,
              prompt: str,
              stop: Optional[List[str]] = None,
              **kwargs) -> str:
        response = llamaapi_request(prompt)
        if stop:
            for token in stop:
                response = response.split(token)[0]
        return response

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"max_tokens": self.max_tokens}

    def get_num_tokens(self, text: str) -> int:
        # Simple tokenizer based on whitespace
        return len(text.split())

def generate_related_questions(source_documents, num_questions=3):
    llm = LlamaLLM()

    # Refined prompt to ensure only 3 questions are generated
    prompt_template = """
    You are a helpful assistant for pharmacists and pharmacy students.
    Based on the following context from pharmaceutical documents, generate exactly {num_questions} specific and relevant questions that a pharmacist or pharmacy student might ask, focusing on key details such as indications, contraindications, side effects, and interactions. Do not include explanations or any additional content—just the questions.

    Context: {context}

    Questions:
    """

    # Create the prompt template
    prompt = PromptTemplate(input_variables=["context", "num_questions"],
                            template=prompt_template)
    chain = LLMChain(llm=llm, prompt=prompt)

    # Combine content from source documents
    context = " ".join([doc.page_content for doc in source_documents])

    # Prepare input variables as a dictionary
    input_vars = {"context": context, "num_questions": num_questions}

    # Run the chain to get the result
    result = chain.run(input_vars)

    # Split the result into individual questions, assuming questions are each on a new line
    questions = [q.strip() for q in result.strip().split('\n') if q.strip()]

    # Ensure only the requested number of questions are returned
    return questions[:num_questions]

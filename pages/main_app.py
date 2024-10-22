import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from functools import partial
from answer_generation import generate_related_questions
from pubmed_search import search_related_papers
from vector_store import initialize_vector_store

# LangChain imports
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# Custom evaluators
from langchain.callbacks.tracers.evaluation import EvaluatorCallbackHandler
from langsmith.evaluation import RunEvaluator, EvaluationResult
from custom_eval import PharmAssistEvaluator, HarmfulnessEvaluator, AIDetectionEvaluator
from langsmith.schemas import Run
import datetime
import requests
from datetime import datetime, timezone
import uuid
from langsmith.schemas import Run

# LangSmith for client interaction
from langsmith import Client
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# Load environment variables from a .env file
load_dotenv()

os.environ[
    'LANGSMITH_API_KEY'] = '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'
os.environ['LANGSMITH_ENDPOINT'] = 'https://api.smith.langchain.com/'
os.environ['LANGSMITH_PROJECT'] = 'pharmassist'
os.environ['LANGCHAIN_TRACING_V2'] = 'true'

# Load environment variables from a .env file
langsmith_client = Client(
    api_key='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')

# Set up Llama Amazon Bedrock API endpoint
LLAMA_API_ENDPOINT = "https://n9f72yljeh.execute-api.us-west-2.amazonaws.com/default/llama-hackathon"


def llamaapi_request(prompt, max_tokens=500):
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt":
        prompt,  # Send the prompt as is, without additional stringification
        "max_tokens": max_tokens
    }
    try:
        response = requests.post(LLAMA_API_ENDPOINT,
                                 headers=headers,
                                 json=data)  # Use json parameter
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Llama API: {e}")
        return ""


#Initialize custom evaluators
custom_evaluators = [
    PharmAssistEvaluator(),
    HarmfulnessEvaluator(),
    AIDetectionEvaluator()
]

# Initialize session state
if 'current_question' not in st.session_state:
    st.session_state.current_question = ''
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []
if 'current_card_index' not in st.session_state:
    st.session_state.current_card_index = 0
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'answer' not in st.session_state:
    st.session_state.answer = ''
if 'sources' not in st.session_state:
    st.session_state.sources = []
if 'related_questions' not in st.session_state:
    st.session_state.related_questions = []
if 'related_papers' not in st.session_state:
    st.session_state.related_papers = []
if 'trigger_answer_generation' not in st.session_state:
    st.session_state.trigger_answer_generation = False

st.set_page_config(
    layout="wide",
    page_title="PharmAssistAI - Your Pharmaceutical Research Assistant",
    page_icon="🌿",
    initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp {
            background-color: white;
            color: black;
        }
    </style>
""",
            unsafe_allow_html=True)

# Custom CSS
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

body {
    font-family: 'Inter', sans-serif;
    background-color: #FFFFFF;
}

.stApp {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
    background-color: white;
    color: black;
}

.main-header {
    color: #1E40AF;
    font-weight: 800;
    font-size: 3.5rem;
    margin-bottom: 1rem;
    line-height: 1.2;
    display: flex;
    align-items: center;
}

.beta-badge {
    background-color: #3B82F6;
    color: #FFFFFF;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    margin-left: 1rem;
}

.stTextInput > div > div > input {
    background-color: #F9FAFB;
    border: 1px solid #D1D5DB;
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    color: #1F2937;
    width: 100%;
    box-sizing: border-box;
    font-family: 'Inter', sans-serif;
}

.stButton > button, .flashcard-nav button {
    background-color: #3B82F6;
    color: white;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 600;
    border: none;
    border-radius: 30px;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stButton > button:hover, .flashcard-nav button:hover {
    background-color: #2563EB;
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
}

.stButton > button:active, .flashcard-nav button:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h1, h2, h3 {
    color: #1E3A8A;
    font-weight: 700;
}

p {
    color: #4B5563;
    font-size: 1rem;
}

.section-container {
    background-color: #F9FAFB;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.answer-container {
    background-color: #FFFFFF;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.source-item {
    background-color: #F9FAFB;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
    border-left: 4px solid #3B82F6;
}

.related-question-item {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border-radius: 30px;
    padding: 10px 20px;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    transition: background-color 0.3s ease;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 14px;
    border: none;
    display: inline-block;
    text-align: center;
    line-height: 1.4;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.related-question-item:hover {
    background-color: #1E40AF !important;
    color: #FFFFFF !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.related-paper-item {
    background-color: #FFFFFF;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    transition: all 0.3s ease;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.related-paper-item:hover {
    background-color: #F0F9FF;
    transform: translateY(-2px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-header {
    color: #1E3A8A;
    font-size: 2rem;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

.footer {
    text-align: center;
    padding: 15px;
    color: #4B5563;
    font-size: 0.9rem;
    margin-top: 2rem;
}

.disclaimer {
    background-color: #FEF3C7;
    border-left: 4px solid #F59E0B;
    padding: 1rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
    border-radius: 0.25rem;
    font-size: 1.1rem; 
    color: #92400E;
}

.flashcard {
    background-color: #ffffff;
    border: 2px solid #3B82F6;
    border-radius: 15px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.flashcard:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 20px rgba(0, 0, 0, 0.15);
}

.flashcard h3 {
    color: #3B82F6;
    font-size: 1.5em;
    margin-bottom: 20px;
    text-align: center;
}

.flashcard-content {
    color: #333;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    line-height: 1.6;
    text-align: center;
}

.flashcard-nav {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 20px;
}

.flashcard-buttons {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    width: 100%;
}

.flashcard-buttons [data-testid="column"] {
    display: flex;
    justify-content: center;
    align-items: center;
}

.flashcard-buttons [data-testid="column"]:first-child {
    justify-content: flex-start;
}

.flashcard-buttons [data-testid="column"]:last-child {
    justify-content: flex-end;
}
.flashcard-buttons {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    width: 100%;
}

.flashcard-buttons [data-testid="column"] {
    display: flex;
    justify-content: center;
    align-items: center;
}

.flashcard-buttons [data-testid="column"]:first-child {
    justify-content: flex-start;
}

.flashcard-buttons [data-testid="column"]:last-child {
    justify-content: flex-end;
}

.flashcard-buttons button {
    width: auto;
    min-width: 120px;
    max-width: 200px;
}

/* Center button specific styling */
.flashcard-buttons [data-testid="column"]:nth-child(2) {
    flex-grow: 1;
    display: flex;
    justify-content: center;
}

.flashcard-buttons [data-testid="column"]:nth-child(2) button {
    margin: 0 auto;
    min-width: 150px;  /* Slightly wider than side buttons */
}

/* Ensure consistent styling for all buttons */
.stButton > button {
    height: 38px;
    padding: 0 16px;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    white-space: nowrap;
}

@media (max-width: 768px) {
    .flashcard-buttons {
        flex-direction: column;
        align-items: stretch;
    }

    .flashcard-buttons [data-testid="column"] {
        margin-bottom: 10px;
    }

    .flashcard-buttons button {
        width: 100%;
        max-width: none;
    }
}

.flashcard-counter {
    font-size: 16px;
    color: #4B5563;
    text-align: center;
    margin-top: 10px;
}

.pubmed-badge {
    background-color: #207196;
    color: #FFFFFF;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    margin-left: 0.5rem;
    vertical-align: middle;
}

.section-header-container {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
}

.related-papers-container {
    background-color: #F0F9FF;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.main-title {
    color: #1E40AF;
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}

.ask-question-header {
    color: #1E3A8A;
    font-size: 2rem;
    font-weight: 700;
    margin-top: 2rem;
    margin-bottom: 0.5rem;
}

.main-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

.link-icon {
    vertical-align: middle;
    margin-left: 5px;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSidebar"] {display: none;}
.stDeployButton {display:none;}

/* Media Queries */
@media (max-width: 768px) {
    .stApp {
        padding: 1rem 0.5rem;
    }
    .main-header {
        font-size: 2rem;
        flex-direction: column;
        align-items: flex-start;
    }
    .beta-badge {
        margin-left: 0;
        margin-top: 0.5rem;
    }
    .section-header {
        font-size: 1.5rem;
    }
    .flashcard {
        padding: 20px;
    }
    .flashcard-content {
        font-size: 16px;
    }
    .flashcard-nav button, 
    .center-column button, 
    [data-testid="stHorizontalBlock"] button {
        width: 100%;
        min-width: unset;
        max-width: unset;
        font-size: 14px;
        padding: 10px 16px;
    }
    .flashcard-nav {
        flex-direction: row;
        justify-content: space-between;
        width: 100%;
    }
    [data-testid="column"] {
        width: auto !important;
        flex: 1 !important;
    }
    [data-testid="column"] > div {
        width: 100%;
    }
    [data-testid="column"] button {
        width: 100%;
        min-width: unset;
        max-width: unset;
        font-size: 12px;
        padding: 8px 12px;
    }
    .related-question-item {
        font-size: 12px;
        padding: 8px 16px;
    }
    .answer-container, .source-item {
        padding: 1rem;
    }
}
 </style>

''',
            unsafe_allow_html=True)

# # Set up OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error(
        "OpenAI API key is not set. Please check your environment variables.")
    st.stop()

client = OpenAI(api_key=api_key)

# Initialize vector store
vector_store = initialize_vector_store()


def generate_answer_with_sources(question):
    try:
        docs = vector_store.similarity_search(question, k=4)

        if not docs:
            logging.warning(f"No documents found for question: {question}")
            return "I don't have enough information to answer this question.", [], [], [], [], {}

        context = " ".join([doc.page_content for doc in docs])

        # Prepare the prompt for Llama API
        prompt = f"""
        You are PharmAssistAI, an AI assistant created specifically to help pharmacists and pharmacy students find accurate, relevant information about pharmaceutical and medical topics. 

        When generating an answer, please follow these guidelines:
        - Only answer questions related to pharmaceuticals, medications, medical conditions, and healthcare practices.
        - If the question is not related to these topics, politely inform the user that you can only assist with pharmacy and medical-related inquiries.
        - Carefully review the provided context to identify the most relevant information.
        - Synthesize the information into a clear, concise, and well-structured response.
        - Emphasize key facts, mechanisms of action, indications, contraindications, and other essential pharmacology concepts.
        - If the context does not provide sufficient information to answer the question confidently, state that you don't have enough information and suggest consulting a healthcare professional.
        - Always maintain a professional, objective tone and avoid making judgments or recommendations without clear evidence.
        - Do not answer questions about individuals, current events, or topics unrelated to healthcare and pharmaceuticals.

        Please help me find the most relevant information to answer the following question:

        {question}

        Here is the context from my knowledge base that seems most applicable:

        {context}

        Please provide your answer:
        """

        # Call Llama API
        logging.info(f"Sending request to Llama API for question: {question}")
        answer = llamaapi_request(prompt, max_tokens=500)

        if answer:
            answer = answer.strip()
            flashcards = generate_flashcards(context, question)
            logging.info("Successfully generated answer and flashcards")
        else:
            logging.error("Llama API returned an empty response")
            raise ValueError("Llama API returned an empty response")

        sources = []
        for i, doc in enumerate(docs, 1):
            source = {"number": i, "content": doc.page_content, "metadata": {}}
            if hasattr(doc, 'metadata'):
                source["metadata"] = doc.metadata
                if 'id' in doc.metadata:
                    source["metadata"]["qdrant_point_id"] = doc.metadata['id']
                if 'collection_name' in doc.metadata:
                    source["metadata"][
                        "qdrant_collection_name"] = doc.metadata[
                            'collection_name']
            sources.append(source)

        logging.info("Generating related questions and papers")
        related_questions = generate_related_questions(docs)
        related_papers = search_related_papers(question)

        # Custom evaluation using OpenAI models
        logging.info("Performing custom evaluation")
        evaluation_results = evaluate_answer(question, answer)

        return answer, sources, related_questions, related_papers, flashcards, evaluation_results
    except Exception as e:
        logging.error(
            f"An error occurred in generate_answer_with_sources: {str(e)}",
            exc_info=True)
        return f"An error occurred: {str(e)}", [], [], [], [], {}


def evaluate_answer(question, answer):
    logging.info(f"Starting evaluation for question: {question}")
    current_time = datetime.now(timezone.utc).isoformat()
    mock_run = Run(
        id=str(uuid.uuid4()),
        name="answer_generation",
        inputs={"question": question},
        outputs={"answer": answer},
        start_time=current_time,
        end_time=current_time,
        run_type="llm",
        execution_order=1,
        serialized={},
        session_name="mock_session",
        error=None,
        trace_id=str(uuid.uuid4()),
    )

    evaluators = [
        PharmAssistEvaluator(),
        AIDetectionEvaluator(),
        HarmfulnessEvaluator()
    ]

    evaluation_results = {}
    for evaluator in evaluators:
        try:
            logging.info(f"Running evaluator: {evaluator.__class__.__name__}")
            result = evaluator.evaluate_run(mock_run)
            evaluation_results[evaluator.__class__.__name__] = {
                "score": result.score,
                "comment": result.comment
            }
            logging.info(
                f"Evaluator {evaluator.__class__.__name__} completed successfully"
            )
        except Exception as e:
            logging.error(f"Error in {evaluator.__class__.__name__}: {str(e)}",
                          exc_info=True)
            evaluation_results[evaluator.__class__.__name__] = {
                "score": None,
                "comment": f"Evaluation failed: {str(e)}"
            }

    logging.info("Evaluation completed")
    return evaluation_results


def generate_flashcards(context, question, num_cards=3):
    # Refined prompt to ensure flashcards are generated without numbering
    prompt = f"""
    You are an educational assistant that creates flashcards to help students learn and remember key pharmaceutical concepts. 

    Based on the following context and question, please generate {num_cards} relevant and concise flashcards. Each flashcard should include a clear question and a succinct answer, focusing on key facts like drug indications, contraindications, mechanisms, or side effects.

    Please format each flashcard as follows:
    Question: [question text]
    Answer: [answer text]

    Do not include numbering or any additional labels (like "Flashcard 1", "Flashcard 2").

    Context: {context}

    Question: {question}
    """

    response = llamaapi_request(prompt)

    flashcards = []
    raw_content = response.strip().split('\n\n')

    for card in raw_content:
        parts = card.split('\nAnswer: ')
        if len(parts) == 2:
            question = parts[0].replace('Question: ', '').strip()
            answer = parts[1].strip()
            flashcards.append({"question": question, "answer": answer})

    return flashcards[:num_cards]


def next_card():
    st.session_state.current_card_index = (
        st.session_state.current_card_index + 1) % len(
            st.session_state.flashcards)
    st.session_state.show_answer = False


def prev_card():
    st.session_state.current_card_index = (
        st.session_state.current_card_index - 1) % len(
            st.session_state.flashcards)
    st.session_state.show_answer = False


def toggle_answer():
    st.session_state.show_answer = not st.session_state.show_answer


def display_flashcards():
    if st.session_state.flashcards:
        st.markdown('<h2 class="section-header">Flashcards</h2>',
                    unsafe_allow_html=True)

        current_card = st.session_state.flashcards[
            st.session_state.current_card_index]

        st.markdown(f'''
            <div class="flashcard">
                <h3>{"Answer" if st.session_state.show_answer else "Question"}</h3>
                <p class="flashcard-content">
                    {current_card["answer" if st.session_state.show_answer else "question"]}
                </p>
            </div>
            ''',
                    unsafe_allow_html=True)

        # Use a single row with custom CSS for button layout
        st.markdown('<div class="flashcard-buttons">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.button("◀ Previous", on_click=prev_card, key="prev_button")
        with col2:
            st.button("Show Answer"
                      if not st.session_state.show_answer else "Show Question",
                      on_click=toggle_answer,
                      key="toggle_button",
                      help="Click to reveal or hide the answer")
        with col3:
            st.button("Next ▶", on_click=next_card, key="next_button")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            f"<div class='flashcard-counter'>{st.session_state.current_card_index + 1} / {len(st.session_state.flashcards)}</div>",
            unsafe_allow_html=True)


def on_related_question_click(question):
    # Ensure the question is stored correctly and displayed in the input field
    st.session_state.current_question = question
    st.session_state.user_input = question  # Update the input field
    st.session_state.trigger_answer_generation = True
    st.session_state.update_input = True  # New flag to trigger input update
    st.session_state.dropdown_index = 0  # Reset the dropdown to "Select a question..."


def display_content():
    if st.session_state.answer:
        st.markdown('<h2 class="section-header">Answer</h2>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="answer-container">{st.session_state.answer}</div>',
            unsafe_allow_html=True)

        # Only display additional content if the question is not off-topic
        if not st.session_state.get('is_off_topic', False):
            if st.session_state.sources:
                st.markdown('<h2 class="section-header">Sources</h2>',
                            unsafe_allow_html=True)
                for source in st.session_state.sources:
                    with st.expander(f"Source {source['number']}",
                                     expanded=False):
                        st.markdown(
                            f'<div class="source-item">{source["content"]}</div>',
                            unsafe_allow_html=True)
                        # st.markdown("**Metadata:**")
                        # for key, value in source["metadata"].items():
                        #     st.markdown(f"- {key}: {value}")

            display_flashcards()

            if st.session_state.related_questions:
                st.markdown(
                    '<h2 class="section-header">Related Questions</h2>',
                    unsafe_allow_html=True)
                for related_question in st.session_state.related_questions:
                    if st.button(related_question,
                                 key=f"related_{related_question}",
                                 help="Click to explore this related question",
                                 on_click=on_related_question_click,
                                 args=(related_question, )):
                        pass  # The on_click function will handle the action

            if st.session_state.related_papers:
                st.markdown(
                    '<h2 class="section-header">Related Papers from PubMed</h2>',
                    unsafe_allow_html=True)
                for paper in st.session_state.related_papers:
                    st.markdown(paper, unsafe_allow_html=True)


def handle_question_submission():
    if st.session_state.trigger_answer_generation:
        if st.session_state.current_question:
            # Display disclaimer immediately after clicking submit
            st.markdown(
                '<div class="disclaimer">PharmAssistAI is not a substitute for professional medical advice. Always seek guidance from a healthcare provider.</div>',
                unsafe_allow_html=True)

            # Create a placeholder for the loading animation
            loading_placeholder = st.empty()

            # Display the improved loading animation
            loading_animation = '''
            <style>
            @keyframes pulse {
              0% {
                transform: scale(0.8);
                opacity: 0.5;
              }
              50% {
                transform: scale(1);
                opacity: 1;
              }
              100% {
                transform: scale(0.8);
                opacity: 0.5;
              }
            }

            .loading-container {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 200px;
            }

            .loading-circle {
              width: 80px;
              height: 80px;
              border-radius: 50%;
              background-color: #3B82F6;
              animation: pulse 2s ease-in-out infinite;
            }

            .loading-text {
              margin-top: 20px;
              font-size: 18px;
              color: #4B5563;
              font-weight: 500;
            }
            </style>

            <div class="loading-container">
              <div class="loading-circle"></div>
              <p class="loading-text">Generating answer...</p>
            </div>
            '''
            loading_placeholder.markdown(loading_animation,
                                         unsafe_allow_html=True)

            # Perform the long-running task
            answer, sources, related_questions, related_papers, flashcards, evaluation_results = generate_answer_with_sources(
                st.session_state.current_question)

            # Clear the loading animation
            loading_placeholder.empty()

            # Check if the answer is off-topic
            if "I'm sorry, but I can only" in answer:
                st.session_state.answer = answer
                st.session_state.is_off_topic = True
                # Clear other session state variables for off-topic questions
                st.session_state.sources = []
                st.session_state.related_questions = []
                st.session_state.related_papers = []
                st.session_state.flashcards = []
            else:
                st.session_state.answer = answer
                st.session_state.sources = sources
                st.session_state.related_questions = related_questions
                st.session_state.related_papers = related_papers
                st.session_state.flashcards = flashcards
                st.session_state.current_card_index = 0
                st.session_state.show_answer = False
                st.session_state.is_off_topic = False
        st.session_state.trigger_answer_generation = False


def main():
    # Update the CSS to reduce spacing
    st.markdown("""
    <style>
    .main-title {
        color: #1E40AF;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .beta-badge {
        background-color: #3B82F6;
        color: white;
        font-size: 0.9rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        vertical-align: middle;
    }
    .ask-question-header {
        color: #1E3A8A;
        font-size: 2rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 0.5rem;  /* Reduced bottom margin */
    }
    .stTextInput > div > div > input {
        font-size: 18px;
        padding: 12px 20px;
        border-radius: 25px;
        border: 2px solid #3B82F6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stForm > div > div > div {
        padding-top: 0;  /* Remove top padding from form */
    }
    .stButton > button {
        background-color: #f0f0f0;
        color: #333333;
        font-size: 16px;
        font-weight: 400;
        padding: 8px 16px;
        border-radius: 8px;
        border: 1px solid #d0d0d0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
        margin-top: 0.5rem;  /* Reduced space above the button */
    }
    .stButton > button:hover {
        background-color: #e8e8e8;
        border-color: #c0c0c0;
    }
    .stButton > button:active {
        background-color: #d8d8d8;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    .link-icon {
        vertical-align: middle;
        margin-left: 5px;
    }
    </style>
    """,
                unsafe_allow_html=True)

    # Main container for centering content
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # PharmAssistAI BETA header
    st.markdown(
        '<h1 class="main-title">PharmAssistAI <span class="beta-badge">BETA</span></h1>',
        unsafe_allow_html=True)

    # Add "Ask Your Question" header with link icon
    st.markdown('<h2 class="ask-question-header">Ask Your Question</h2>',
                unsafe_allow_html=True)

    # Initialize session state
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ''
    if 'dropdown_index' not in st.session_state:
        st.session_state.dropdown_index = 0

    # Predefined questions for suggestions
    predefined_questions = [
        "What should I be careful of when taking Metformin?",
        "What are the contraindications of Aspirin?", "How does Januvia work?",
        "Can older people take beta blockers?", "How do beta blockers work?",
        "I am taking Aspirin, is it ok to take Glipizide?",
        "What are the side effects of Lipitor?",
        "How does insulin regulate blood sugar?",
        "What is the recommended dosage for Amoxicillin?",
        "Can pregnant women take Tylenol?"
    ]

    # Combine custom input option with predefined questions
    all_options = ["Select a question..."] + predefined_questions

    # Function to handle selection change
    def on_select_change():
        selected = st.session_state.question_select
        if selected != "Select a question...":
            st.session_state.user_input = selected
            st.session_state.dropdown_index = all_options.index(selected)

    if 'user_input' not in st.session_state:
        st.session_state.user_input = ''

    # Update the session state based on the input value
    def handle_custom_input():
        if st.session_state.user_input and st.session_state.user_input not in predefined_questions:
            st.session_state.dropdown_index = 0
            st.session_state.current_question = st.session_state.user_input  # You could store it here

    # Text input for custom questions
    user_input = st.text_input(
        "",
        value=st.session_state.
        user_input,  # Ensure it's initialized in session state only once
        placeholder="Enter your pharmacy question here...",
        key="user_input",
        on_change=handle_custom_input)

    # Selectbox for suggestions
    st.selectbox("Or choose a suggested question:",
                 options=all_options,
                 key="question_select",
                 index=st.session_state.dropdown_index,
                 on_change=on_select_change)

    # Use the user input or the selected question
    question_to_submit = user_input or st.session_state.user_input

    # Submit button
    if st.button("Submit", key="submit_button"):
        if question_to_submit:
            st.session_state.current_question = question_to_submit
            st.session_state.trigger_answer_generation = True
            # Clear previous results
            st.session_state.answer = ''
            st.session_state.sources = []
            st.session_state.related_questions = []
            st.session_state.related_papers = []
            st.session_state.flashcards = []
        else:
            st.warning(
                "Please enter a question or select a suggestion before submitting."
            )

    st.markdown('</div>', unsafe_allow_html=True)

    handle_question_submission()

    if st.session_state.trigger_answer_generation:
        handle_question_submission()
        st.rerun()

    display_content()

    # Footer
    st.markdown(
        '<div class="footer">© 2024 PharmAssistAI. All rights reserved.</div>',
        unsafe_allow_html=True)


# Add this to the initialization section at the beginning of the script
if 'trigger_answer_generation' not in st.session_state:
    st.session_state.trigger_answer_generation = False

if __name__ == "__main__":
    main()

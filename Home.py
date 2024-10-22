import streamlit as st
from streamlit_lottie import st_lottie
import requests


def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def main():
    st.set_page_config(
        page_title="PharmAssistAI - Your Pharmaceutical Research Assistant",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="collapsed")

    # Custom CSS for Styling
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Poppins', sans-serif;
            background-color: #f0f4f8;
            color: #1a202c;
        }
        h1 {
            font-weight: 700;
            font-size: 3.5rem;
            color: #2c5282;
            margin-bottom: 1rem;
        }
        h2 {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 1.5rem;
        }
        h3 {
            font-weight: 600;
            font-size: 1.8rem;
            color: #2c5282;
        }
        p {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #4a5568;
        }
        .stButton > button {
            background-color: #4299e1;
            color: white;
            font-weight: 600;
            padding: 0.75rem 2rem;
            border-radius: 30px;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #3182ce;
            box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
        }
        .feature-card {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        }
        .divider {
            height: 2px;
            background: linear-gradient(to right, #4299e1, #48bb78);
            margin: 3rem 0;
        }
        .how-it-works {
            padding: 4rem 0;
            margin: 3rem 0;
        }
        .how-it-works h2 {
            color: #2B6CB0;
            margin-bottom: 2rem;
        }
        .testimonial-section {
            padding: 4rem 0;
            margin: 3rem 0;
        }
        .testimonial-section h2 {
            color: #2C7A7B;
            margin-bottom: 2rem;
        }
        .testimonial-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .testimonial-card {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        .testimonial-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        }
        .testimonial-text {
            font-style: italic;
            color: #2d3748;
            margin-bottom: 1rem;
        }
        .testimonial-author {
            font-weight: 600;
            text-align: right;
            color: #2c5282;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }
    </style>
    """,
                unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div style="padding: 1rem 0;">
        <h3 style="margin: 0; color: #4299e1;">🌿 PharmAssistAI</h3>
    </div>
    """,
                unsafe_allow_html=True)

    # Hero Section
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<h1>AI-Powered Pharmaceutical Research</h1>",
                    unsafe_allow_html=True)
        st.markdown("""
        <p>Experience the future of drug information retrieval. PharmAssistAI revolutionizes your research process with cutting-edge AI insights from FDA-approved drug data.</p>
        """,
                    unsafe_allow_html=True)

        if st.button("Start Exploring"):
            st.markdown(
                '<meta http-equiv="refresh" content="0;url=/main_app">',
                unsafe_allow_html=True)

    with col2:
        lottie_url = "https://assets5.lottiefiles.com/packages/lf20_uwWgICKCxj.json"
        lottie_json = load_lottieurl(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=400)
        else:
            st.error("Error loading animation.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Features Section
    st.markdown(
        "<h2 style='text-align: center;'>Unlock the Power of AI in Pharmaceutical Research</h2>",
        unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div style='font-size: 2.5rem; color: #4299e1;'>🤖</div>
            <h3>AI-Powered Insights</h3>
            <p>Our advanced algorithms simplify complex queries, providing clear and accurate answers from FDA drug labels and adverse reactions datasets.</p>
        </div>
        """,
                    unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div style='font-size: 2.5rem; color: #4299e1;'>📚</div>
            <h3>Comprehensive Data</h3>
            <p>Access a vast repository of FDA data, meticulously organized for efficient research on drug compositions, mechanisms of action, and contraindications.</p>
        </div>
        """,
                    unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div style='font-size: 2.5rem; color: #4299e1;'>🎓</div>
            <h3>Smart Learning Tools</h3>
            <p>Enhance your understanding with AI-generated study guides, interactive flashcards, and intuitive analogies for complex pharmaceutical concepts.</p>
        </div>
        """,
                    unsafe_allow_html=True)

    # How It Works Section
    st.markdown("<h2 style='text-align: center;'>How PharmAssistAI Works</h2>",
                unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div style='font-size: 2.5rem; color: #4299e1;'>❓</div>
            <h3>Ask a Question</h3>
            <p>Input your pharmaceutical query or choose from suggested topics.</p>
        </div>
        """,
                    unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div style='font-size: 2.5rem; color: #4299e1;'>🔍</div>
            <h3>AI Analysis</h3>
            <p>Our AI rapidly processes and analyzes vast FDA datasets.</p>
        </div>
        """,
                    unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div style='font-size: 2.5rem; color: #4299e1;'>💡</div>
            <h3>Get Insights</h3>
            <p>Receive comprehensive, cited answers with key information highlighted.</p>
        </div>
        """,
                    unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class='feature-card'>
            <div style='font-size: 2.5rem; color: #4299e1;'>🌐</div>
            <h3>Explore Further</h3>
            <p>Dive deeper with related questions, topics, and interactive learning tools.</p>
        </div>
        """,
                    unsafe_allow_html=True)

    # Testimonial Section
    st.markdown("""
    <div class="testimonial-section">
        <div class="container">
            <h2 style='text-align: center;'>What Our Users Say</h2>
            <div class="testimonial-grid">
                <div class="testimonial-card">
                    <div class="testimonial-text">
                        "PharmAssistAI has revolutionized our research process. It's like having a brilliant pharmacist and an AI expert at your fingertips 24/7. The depth of knowledge and speed of information retrieval have significantly enhanced our capabilities."
                    </div>
                    <p class="testimonial-author">- Dr. Sarah Johnson, Clinical Pharmacist Specialist</p>
                </div>
                <div class="testimonial-card">
                    <div class="testimonial-text">
                        "As a pharmacy student, PharmAssistAI has been an invaluable study aid. It breaks down complex concepts and provides interactive learning tools that have boosted my understanding and retention of pharmaceutical information."
                    </div>
                    <p class="testimonial-author">- Alex Chen, PharmD Candidate</p>
                </div>
                <div class="testimonial-card">
                    <div class="testimonial-text">
                        "The accuracy and comprehensiveness of PharmAssistAI's insights have impressed our entire research team. It's become an essential tool in our drug development process, saving us countless hours of manual research."
                    </div>
                    <p class="testimonial-author">- Dr. Emily Patel, Pharmaceutical Researcher</p>
                </div>
            </div>
        </div>
    </div>
    """,
                unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #4a5568;">
        <p>© 2024 PharmAssistAI. All rights reserved. | Powered by FDA Open Medicine Dataset</p>
    </div>
    """,
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()

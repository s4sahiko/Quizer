import streamlit as st
import json
import requests
import fitz # PyMuPDF for PDF text extraction

#Firebase Imports and Setup
try:
    from firebase_admin import initialize_app, credentials
    from firebase_admin import firestore, auth as firebase_auth
except ImportError:
    class MockFirebase:
        def __init__(self):
            self.db = None
            self.auth = None
            self.user_id = "mock_user"
    mock_firebase = MockFirebase()
    db = mock_firebase.db
    auth = mock_firebase.auth
    userId = mock_firebase.user_id

#  Gemini API Configuration 
API_KEY = st.secrets.get("GEMINI_API_KEY", "")  
if not API_KEY:
    API_KEY = "" 

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

# Custom CSS 
def set_custom_css():
    st.markdown(
        """
        <style>

        /* Main Page Styling */
        .main-header {
            color: white;
            font-size: 5em;
            font-weight: 900;
            text-align: center;
            padding-bottom: 5px;
            
        }

         /* Centered Header Styling */
        .centered-header {
            text-align: center;
            }

        /* process step list */
        .process-steps-list {
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
            font-size: 1.05em; 
            text-align: left; 
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #6A1B9A; 
            }   
        
        /* Sidebar Enhancements */
        div[data-testid="stSidebar"] h2 {
            color: #4B0082;
            border-bottom: 2px solid #EEE;
            padding-bottom: 5px;
            margin-top: 15px;
        }

        /* Question Card Styling */
        .stContainer {
            border: 1px solid #e6e6e6;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            background-color: #FAFAFA;
        }
        
        /* Question Text Styling */
        .question-text {
            font-size: 1.25em;
            font-weight: 500;
            color: white; 
            margin-bottom: 15px;
        }
       
        /* Review Mode Color */
        .option-box {
            margin-bottom: 8px;
            padding: 12px;
            border-radius: 5px;
            border: 1px solid #ddd;
            transition: all 0.2s ease-in-out;
            color: #ffffff; /* perfect contrast */
        }
        
        /* Correct Answer */
        .option-box.correct {
            background-color: lightgreen; 
            color: #155724; 
            border-color: #155724; 
        }
        
        /* Incorrect User Answer */
        .option-box.incorrect {
            background-color: lightcoral; 
            border-color: #721C24;
            color: white !important;
        }

        /* Active Quiz Radio Buttons */
        .stRadio div {
             color: white; /* Make radio option text clearly visible */
        }


        /* GRADIENT BUTTON STYLING */
        .stButton>button {
            width: 100%;
            height: 3.5em; 
            font-size: 1.1em;
            border-radius: 10px;
            border: none;
            background: linear-gradient(90deg, #4B0082 0%, #6A1B9A 100%); 
            color: white;
            font-weight: 700;
            box-shadow: 0 4px 10px rgba(75, 0, 130, 0.4);
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover:enabled {
            background: linear-gradient(90deg, #6A1B9A 0%, #4B0082 100%); 
            box-shadow: 0 6px 15px rgba(75, 0, 130, 0.6);
            transform: translateY(-2px); 
        }
        
        .stButton>button:disabled {
            background: #CCCCCC;
            color: #666666;
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }
        
        div[data-testid="stSidebar"] .stButton>button {
            margin-top: 20px;
        }
        
        .stExpanderHeader {
            background-color: #F0F2F6 !important;
            border-radius: 8px;
        }
        
        </style>
        """,
        unsafe_allow_html=True
    )

# Utility Functions 

def get_pdf_text(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    try:
        pdf_file = uploaded_file.read()
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return None

def set_initial_state():
    """Initializes session state variables."""
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'difficulty_level' not in st.session_state:
        st.session_state.difficulty_level = "Medium"
    if 'render_review' not in st.session_state:
        st.session_state.render_review = False


def generate_quiz(uploaded_file, text_input, num_questions, difficulty):
    """Generates a quiz using the Gemini API."""
    if uploaded_file:
        content_text = get_pdf_text(uploaded_file)
        if not content_text:
            return
    elif text_input:
        content_text = text_input
    else:
        st.error("Please upload a file or paste text content to generate a quiz.")
        return

    if not API_KEY and not st.session_state.get('api_key_injected', False):
          st.error("API Key not found. Please ensure your `secrets.toml` file is configured correctly.")
          return
    
    st.session_state.difficulty_level = difficulty

    # Promt to the Api
    system_prompt = f"""
    You are an expert quiz generator. Your task is to analyze the provided text content
    and generate a quiz of exactly {num_questions} multiple-choice questions.
    The quiz must be of '{difficulty}' difficulty.
    ... [rest of prompt for structure/schema]
    Content for Quiz Generation (Limited to first 20000 characters):
    ---
    {content_text[:20000]}
    ---
    """ 

    # JSON Schema for structured output
    quiz_schema = {
        "type": "OBJECT",
        "properties": {
            "questions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "question": {"type": "STRING"},
                        "answerOptions": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "text": {"type": "STRING"},
                                    "rationale": {"type": "STRING"},
                                    "isCorrect": {"type": "BOOLEAN"}
                                },
                                "propertyOrdering": ["text", "rationale", "isCorrect"]
                            }
                        },
                        "hint": {"type": "STRING"} 
                    },
                    "propertyOrdering": ["question", "answerOptions", "hint"]
                }
            }
        }
    }

    payload = {
        "contents": [{"parts": [{"text": "Generate the quiz based on the instructions."}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": quiz_schema
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    if API_KEY:
          headers['X-Goog-Api-Key'] = API_KEY

    with st.spinner("🧠 Generating your custom quiz with Gemini Flash..."):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status() 
            result = response.json()

            json_text = result['candidates'][0]['content']['parts'][0]['text']
            quiz_data = json.loads(json_text)

            st.session_state.current_quiz = quiz_data['questions']
            st.session_state.quiz_generated = True
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = {i: None for i in range(len(st.session_state.current_quiz))}
            st.session_state.score = 0
            st.session_state.render_review = False
            
            st.toast("Quiz successfully generated!", icon="🎉")
            st.rerun()

        except requests.exceptions.RequestException as e:
            if '403 Client Error: Forbidden' in str(e):
                  st.error("Gemini API Request Error: Access Forbidden (403). Check your API key and permissions.")
            else:
                  st.error(f"Gemini API Request Error: {e}")
        except json.JSONDecodeError:
            st.error("The API returned an invalid JSON response. Please try generating the quiz again.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

def check_quiz():
    """Checks the user's answers and calculates the score."""
    total_questions = len(st.session_state.current_quiz)
    correct_count = 0
    for i, question in enumerate(st.session_state.current_quiz):
        selected_option = st.session_state.user_answers.get(i)
        if selected_option is not None:
            if question['answerOptions'][selected_option]['isCorrect']:
                correct_count += 1

    st.session_state.score = correct_count
    st.session_state.quiz_submitted = True
    st.session_state.render_review = True
    st.toast("Quiz submitted and scored!", icon="✔️")
    st.rerun()

def render_quiz(mode):
    """
    Displays the quiz questions, handles input, and manages the centering layout.
    """
    quiz_questions = st.session_state.current_quiz
    
    quiz_container = st.container()

    with quiz_container:
        with st.form(f"quiz_form_{mode}_{len(quiz_questions)}", clear_on_submit=False): 
            
            # Questions Loop
            for i, q in enumerate(quiz_questions):
                
                with st.container(border=True):
                    
                    # Visibility forced with !important in CSS and strong tag
                    st.markdown(f"**<div class='question-text'>Question {i + 1}: {q['question']}</div>**", unsafe_allow_html=True)
    
                    options = [opt['text'] for opt in q['answerOptions']]
    
                    # QUIZ REVIEW/SUBMITTED MODE
                    if st.session_state.quiz_submitted:
                        correct_index = next(j for j, opt in enumerate(q['answerOptions']) if opt['isCorrect'])
                        user_selection = st.session_state.user_answers.get(i)
    
                        for j, option_text in enumerate(options):
                            is_correct = (j == correct_index)
                            is_user_choice = (j == user_selection)
    
                            css_class = ""
                            icon = "◻️"
                            
                            if is_correct:
                                css_class = "correct"
                                icon = "✅"
                            elif is_user_choice and not is_correct:
                                css_class = "incorrect"
                                icon = "❌"
                            
                            st.markdown(
                                f"<div class='option-box {css_class}'><b>{icon}</b> {option_text}</div>",
                                unsafe_allow_html=True
                            )
    
                        with st.expander("Show Explanation and Hint", expanded=True):
                            st.markdown(f"**Correct Answer Rationale:** {q['answerOptions'][correct_index]['rationale']}")
                            # Safely access the hint
                            st.caption(f"**Study Hint:** {q.get('hint', 'Hint not available for this question.')}")
    
                    # ACTIVE QUIZ MODE
                    else:
                        current_index = st.session_state.user_answers.get(i)
                        initial_index = current_index if current_index is not None and 0 <= current_index < len(options) else None
    
                        selected_value_text = st.radio(
                            "Select your answer:",
                            options=options,
                            index=initial_index,  
                            key=f"q_{i}_radio",
                            help="Select one option."
                        )
                        
                        if selected_value_text is not None:
                            try:
                                new_index = options.index(selected_value_text)
                                st.session_state.user_answers[i] = new_index
                            except ValueError:
                                st.session_state.user_answers[i] = None 
                        else:
                            st.session_state.user_answers[i] = None
                        
                        hint_text = q.get('hint', 'Hint not available.')
                        with st.expander("Get a Hint 💡"):
                            st.caption(hint_text)


            # Submit button only visible in 'active' mode
            st.markdown("---")
            if mode == 'active':
                submit_button = st.form_submit_button("✅ Submit Quiz ", disabled=st.session_state.quiz_submitted)

                if submit_button and not st.session_state.quiz_submitted:
                    for i, q in enumerate(quiz_questions):
                        selected_text = st.session_state.get(f"q_{i}_radio")
                        if selected_text is not None:
                            try:
                                selected_index = [opt['text'] for opt in q['answerOptions']].index(selected_text)
                                st.session_state.user_answers[i] = selected_index
                            except ValueError:
                                st.session_state.user_answers[i] = None
                        else:
                            st.session_state.user_answers[i] = None
                            
                    check_quiz()
            else:
                  st.form_submit_button("Review Mode - Read Only", disabled=True)


def show_results():
    """Displays the final quiz score in a professional layout."""
    total_questions = len(st.session_state.current_quiz)
    percentage = (st.session_state.score / total_questions) * 100
    
    col_score, col_progress, col_feedback = st.columns([1, 2, 2])

    with col_score:
        st.metric(
            label="Final Score", 
            value=f"{st.session_state.score} / {total_questions}",
            delta=f"{percentage:.1f}%"
        )

    with col_progress:
        st.markdown("**Performance Visual**")
        st.progress(percentage / 100)

    with col_feedback:
        st.markdown("**Learning Insight**")
        if percentage >= 80:
            st.success("Mastery Achieved!")
        elif percentage >= 50:
            st.info("Solid Effort!")
        else:
            st.error("Needs Review!")
    
    st.markdown("---") 

# Main Application Logic 

set_initial_state()
st.set_page_config(
    page_title="Gemini Quiz Generator", 
    page_icon="🤖", 
    layout="wide"
)
set_custom_css()

st.markdown('<div class="main-header">AI-Powered Quiz Generator</div>', unsafe_allow_html=True)

# Sidebar Inputs for Generation
with st.sidebar:
    st.subheader("Quiz Control Panel")
    
    #Content Input
    with st.container(border=True):
        st.markdown("## Content Source ")
        uploaded_file = st.file_uploader("Upload PDF document:", type=['pdf'])
        text_input = st.text_area("Or, paste your study notes here (max 20k chars):", height=200)

    # Configuration (Questions and Difficulty separated)
    with st.container(border=True):
        st.markdown("## Quiz Configuration")
        
        # Placing items on separate vertical lines
        num_questions = st.slider("Number of Questions", min_value=1, max_value=20, value=5, help="Number of questions to generate.")
        
        # Separate line
        st.markdown("---") 
        
        difficulty_level = st.selectbox(
            "Difficulty Level",
            ["Easy", "Medium", "Hard"],
            index=1,
            key="difficulty_selector",
            help="Determines the complexity of the questions."
        )

    # Generate Button
    st.markdown("## Generate Quiz")
    if st.button("🚀 Generate New Quiz", use_container_width=True):
        if uploaded_file or text_input:
            st.session_state.quiz_generated = False
            st.session_state.quiz_submitted = False
            generate_quiz(uploaded_file, text_input, num_questions, difficulty_level)
        else:
            st.error("Please provide content.")
    
    st.caption("Tip: Generate a Hard quiz for exam prep!")


# Main Content Area
main_placeholder = st.empty()

if not st.session_state.quiz_generated:
    with main_placeholder.container():
        # Use the custom centered class
        st.caption('<h5 class="centered-header"> Welcome! Use the <b> Quiz Control Panel</b> in the sidebar to create your custom AI quiz.</h5>', unsafe_allow_html=True)
        
        # Use the custom centered class for the Process Overview
        st.markdown("Process Overview:")

        st.markdown("""
        <div class="process-steps-list">
        1. Provide Content:- Upload a document or paste text. <br>
        2. Set Parameters:- Choose the number of questions and the difficulty level (Easy, Medium, or Hard). <br>
        3. Launch:- Click the <b> Generate New Quiz </b> button to launch the AI generator.
        </div>
        """, unsafe_allow_html=True)


elif st.session_state.quiz_generated and not st.session_state.quiz_submitted:
    # ACTIVE QUIZ PLAYGROUND
    with main_placeholder.container():
        
        st.markdown(f'## Active Quiz: {len(st.session_state.current_quiz)} Questions')
        st.markdown(f'**Difficulty Level:** <span style="color:#4B0082; font-weight:bold;">{st.session_state.difficulty_level}</span>', unsafe_allow_html=True)
        st.markdown("---")
        
        render_quiz('active') 

elif st.session_state.quiz_submitted:
    # RESULTS AND REVIEW MODE
    with main_placeholder.container():
        
        # Detailed Answer Review first
        st.markdown("## 🔍 Detailed Answer Review")
        st.markdown("The quiz below shows your selected answer, the correct answer, and a full explanation/hint for each question.")
        
        render_quiz('review')

        st.markdown("---")

        # Score Summary at the very end (as requested)
        st.markdown("## Quiz Results Summary")
        show_results()
import streamlit as st
import constants as const
from xata.client import XataClient
from openai import OpenAI
import pandas as pd
from xata.client import XataClient
import os

site_title = "Model Comparison | Chat-lab.ai"
site_icon = "💬"
st.set_page_config(page_title= site_title, page_icon= site_icon,layout="wide")

# SET APP CONSTANTS

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
PASSKEY = os.environ.get('PASSKEY')
access_key = os.environ.get('S3_ACCESS_KEY')
secret_key = os.environ.get('S3_SECRET_KEY')
DB_KEY = os.environ.get('DB_KEY')
DB_URL = os.environ.get('DB_URL')

xata = XataClient(api_key=DB_KEY, db_url= DB_URL)

error_message = f"""**ERROR:** There was a problem with your API key. Please enter your API key again and click 'Submit API Key' to get started."""

if "gpt3_response" not in st.session_state:
    st.session_state.gpt3_response = None
if "gpt4_response" not in st.session_state:
    st.session_state.gpt4_response = None

if "gpt3_counter" not in st.session_state:
    st.session_state.gpt3_counter = 0
if "gpt4_counter" not in st.session_state:
    st.session_state.gpt4_counter = 0

if 'client' not in st.session_state:
    st.session_state.client = None

if 'first_prompt' not in st.session_state:
    st.session_state.first_prompt = None

if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if 'record_id3' not in st.session_state:
    st.session_state.record_id3 = None

if 'record_id4' not in st.session_state:
    st.session_state.record_id4 = None



# Model Pricing Table
data = {
    'Model': ['gpt-4-1106-preview', 'gpt-3.5-turbo-1106'],
    'Input Price (per 1K Tokens)': ['$0.0100', '$0.0010'],
    'Output Price (per 1K Tokens)': ['$0.0300', '$0.0020']
    }

pricing_table = pd.DataFrame(data, columns=['Model', 'Input Price (per 1K Tokens)', 'Output Price (per 1K Tokens)'])

st.write("#")
const.load_css(const.css_file)
const.footer(const.footer_text, const.footer_link_text)
hide_top_bar_style = """
        <style>
        header {visibility: hidden;}
        </style>
        """
st.markdown(hide_top_bar_style, unsafe_allow_html=True)
const.load_css(const.nav_css)
st.markdown(const.nav_bar_html, unsafe_allow_html=True)

st.markdown(f"""<div style="text-align: center;"><h1>Model Comparison Tool</h1></div>""", unsafe_allow_html=True)

rtcol,midcol,leftcol = st.columns([1,6,1])

with midcol:
    st.markdown("""
        <style>
        .centered-container {
            display: flex;
            justify-content: center;
        }
                """, unsafe_allow_html=True)

    st.markdown(f"""
            <div class="centered-container">
                <div style="background-color: #e7f2fc; border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); padding: 10px 32px; margin: 2rem; text-align: center; display: inline-block; align-items: center; justify-content: center; height: auto;">        
                <p style="font-size: 20px; font-weight: normal; color: #576676; margin: 0">
                Have you ever wondered whether a ChatGPT Plus subscription is worth the 20 bucks a month? 
                <br>
                I know you have. I get asked this question <em>all</em> the time. 😉</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    app_instructions = """
        <p>OpenAI's GPT-4 model is indeed an improvement over GPT-3.5, however, you may not need such advanced language capabilities for every use-case. Therefore, I encourage you to use this tool to compare performance between the free and paid versions of ChatGPT to determine whether upgrading is worthwhile for you. Specifically, this tool queries the latest OpenAI GPT models&mdash; <code>gpt-3.5-turbo-1106</code>, used in the free version of ChatGPT, and <code>gpt-4-1106-preview</code>, available only with a paid ChatGPT subscription .</p>
        <p>However, this tool is also meant to provide researchers with a no-code solution to quickly evaluate which model(s) to employ for textual analysis, information retrieval, and/or other research tasks. To that end, this tool will eventually expand to include other models as well, including open source and private (non-OpenAI) models.</p>
        <p>Finally, this app is still a prototype and <a href="mailto:feedback@chat-lab.ai">your feedback is welcome</a> &mdash;and encouraged!</p>
        <p><strong>Limitations</strong></p>
        <li>Responses in this app do not have memory, so you cannot carry a conversation with this tool and you will need to include all relevant context in your prompt.</li>
        <li>You cannot adjust model parameters, such as <code>temperature</code> or <code>max-tokens</code>, in this lab. However, this feature will be available in the forthocoming <a href="https://chat-lab.ai/completions_placeholder.html">Completions Lab</a>.</li>
        <li>The app only compares the performance of the <em>language models</em> underlying ChatGPT's free and paid versions, it does not support function calling or other advanced features available in ChatGPT Plus, such as <code>code-interpreter</code> or multimodal inputs.</li>
        <em>Minor issues:</em>
            <li style="margin-left: 25px;">Presently, the app has trouble rendering math in the responses. This issue arises from incompatibility with Streamlit custom styling and I'm working on a fix. However, you can see the Markdown/LaTeX for the math present in the responses. In the meantime, if you export your chat history, you can render math locally using the <a href="https://www.mathjax.org/">MathJax</a> library.</li>
            <li style="margin-left: 25px;">For some reason, the first prompt takes a bit longer to generate responses, especially if given a prompt that requires a lengthy response. If it seems like it's taking too long, please be patient, I promise it will work. 😉</li>
        <h3>Instructions</h3>
        <ol>
            <li>Enter your OpenAI API key. If you don't have one, here is a <a href="https://youtu.be/UO_i1GhjElQ?si=ZIJ1l-i_tT4Ohmw6">handy video tutorial</a> on how to get an API key from <a href="https://platform.openai.com/">OpenAI</a>.</li>
            <li>Enter your prompt in the text area below and click generate. The app will query both models and return responses for each, along with other information that might be useful for developing LLM-based workflows, including total tokens (system + prompt + response) and total cost, based on OpenAI's <a href="https://openai.com/pricing">pricing</a>.</li> 
            <li>You can rate the responses from each model and the app will keep track of your ratings . The rating system provides a simple and intuitive way of evaluating model responses for your purposes. The 👍 button adds one to the running score, the 🤷‍♀️ button adds zero, and the 💩 button subtracts one. The total score is displayed for each model.</li> 
            <li>At the bottom of the page, you can also export your session history to a CSV file for further analysis. By default, the app will only display and let you export your chats from the current session, so if you refresh the page, you will lose your chat history.</li> 
            <ul style="margin-left: 25px;">
                <li>If you would like me to retain an extended chat history on this app for your API key, please <a href="mailto:admin@chat-lab.ai">let me know</a>.</li>
            </ul>
            <li>If you find this tool valuable, consider <a href="https://www.buymeacoffee.com/chatlabai">supporting this project</a>.</li>
        </ol>
        """
    st.markdown(f"""<span style="text-align: justify;">{app_instructions}</span>""", unsafe_allow_html=True)
    
# USERS ENTER API KEY
    
    API_KEY = st.text_input("Enter your API key", type="password")
    if API_KEY == PASSKEY:
        API_KEY = OPENAI_API_KEY
    # INITIALIZE OPENAI CLIENT
    if st.button("Submit API Key"):
        st.session_state.gpt3_response = ""
        st.session_state.gpt4_response = ""
        if API_KEY == "":
            st.error(error_message, icon="🚨")
        else:
            try:
                client = OpenAI(api_key=API_KEY)
                print("API KEY = " + API_KEY)
                test = const.api_query(client, "Hello World",'gpt3',"")
                st.session_state.user_id = const.check_or_create_user_key(API_KEY, xata)
                st.success("A new OpenAI connection has been established. You may begin comparing GPT models by entering a prompt below.", icon="👍")
            except:
                st.error(f"**Authentication Error:** Please enter a valid API key", icon="🚨")


    prompt = st.text_area("Enter your prompt here:", height=100)
    
    generate = st.button("Generate Responses")
    if generate:
        st.session_state.gpt3_response = ""
        st.session_state.gpt4_response = ""
        if API_KEY == "":
            st.error(error_message, icon="🚨")
        else:
            if prompt:
                client = OpenAI(api_key=API_KEY)
                user_id = st.session_state.user_id
                st.session_state.gpt3_response = const.api_query(client, prompt, "gpt3", user_id)
                db3 = xata.records().insert("model_compare", st.session_state.gpt3_response)
                st.session_state.record_id3 = db3['id']
                record_id3 = st.session_state.record_id3
                print(f"Add GPT-3 Response to model_compare table:\n {db3}")
                print(f"Record ID: {record_id3}")
                if st.session_state.first_prompt == None:
                    st.session_state.first_prompt = st.session_state.gpt3_response['timestamp']
                print(f"First timestamp: {st.session_state.first_prompt}")
                st.session_state.gpt4_response = const.api_query(client, prompt, "gpt4", user_id)
                db4 = xata.records().insert("model_compare", st.session_state.gpt4_response)
                st.session_state.record_id4 = db4['id']
                record_id4 = st.session_state.record_id4
                print(f"Add GPT-4 Response to model_compare table:\n {db4}")
                print(f"Record ID: {record_id4}")
            else:   
                st.error("Please enter a prompt to generate responses.", icon="🚨")
    
st.divider()
    
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""### GPT-3.5 Response <br><br>""",unsafe_allow_html=True)
    if st.session_state.gpt3_response:
        display_response3 = st.session_state.gpt3_response['response']

        tokens3 = f"<strong>Total Tokens:</strong> {st.session_state.gpt3_response['total_tokens']}" 
        cost3 = f"<strong>API Cost:</strong> ${st.session_state.gpt3_response['total_cost']:.7f}"

        st.markdown(f"""<div class="centered-container">
                <div style="background-color: #f7f7f7; border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); padding: 10px; margin-bottom: 1rem; display: inline-block; align-items: center; justify-content: center; height: auto; width: 100%;">        
                <p style="font-size: 16px; font-weight: normal; color: #576676; margin: 0">
                {display_response3} </p>
                <br>
                {tokens3}
                <br>
                {cost3} 
                </div>
                    """, unsafe_allow_html=True)  
        
        textcol3,goodcol3, blahcol3, badcol3,scorecol3 = st.columns([2,1,1,1,2])
        textcol3.markdown("**Rate this response:**")        
        with goodcol3:
            good = st.button("👍")
            if good:
                st.session_state.gpt3_counter += 1
                st.session_state.gpt3_response['user_rating'] = 1
                rating_db3 = xata.records().update("model_compare", st.session_state.record_id3, {
                                                "user_rating": st.session_state.gpt3_response['user_rating']
                                                })
        with blahcol3:
            blah = st.button("🤷‍♀️")
            if blah:
                st.session_state.gpt3_counter += 0
                st.session_state.gpt3_response['user_rating'] = 0
                rating_db3 = xata.records().update("model_compare", st.session_state.record_id3, {
                                                "user_rating": st.session_state.gpt3_response['user_rating']
                                                })
        with badcol3:
            bad = st.button("💩")
            if bad:
                st.session_state.gpt3_counter -= 1
                st.session_state.gpt3_response['user_rating'] = -1
                rating_db3 = xata.records().update("model_compare", st.session_state.record_id3, {
                                                "user_rating": st.session_state.gpt3_response['user_rating']
                                                })

        gpt3_rating = scorecol3.container()
        with scorecol3:
            gpt3_rating.write(f"**Total Rating: {st.session_state.gpt3_counter}**")   

        user_comment3 = st.text_input("Enter a comment about GPT-3's response:"," ")
        if st.button("Save Comment", key= 'gpt3'):
            comment_db3 = xata.records().update("model_compare", st.session_state.record_id3, {
                                            "user_comment": user_comment3
                                            })
            print(f"Update user_ratings for GPT3 record_id: {st.session_state.record_id3}\n {comment_db3}")   
            
with col2:
    st.markdown(f"""### GPT-4 Response <br><br>""",unsafe_allow_html=True)
    if st.session_state.gpt4_response:
        display_response4 = st.session_state.gpt4_response['response']

        tokens4 = f"<strong>Total Tokens:</strong> {st.session_state.gpt4_response['total_tokens']}" 
        cost4 = f"<strong>API Cost:</strong> ${st.session_state.gpt4_response['total_cost']:.7f}"

        st.markdown(f"""<div class="centered-container">
                <div style="background-color: #f7f7f7; border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); padding: 10px; margin-bottom: 1rem; display: inline-block; align-items: center; justify-content: center; height: auto; width: 100%;">        
                <p style="font-size: 16px; font-weight: normal; color: #576676; margin: 0">
                {display_response4} </p>
                <br>
                {tokens4}
                <br>
                {cost4} 
                </div>
                    """, unsafe_allow_html=True)  

        textcol4,goodcol4, blahcol4, badcol4,scorecol4 = st.columns([2,1,1,1,2])
        textcol4.markdown("**Rate this response:**")
        with goodcol4:
            good = st.button("👍", key=4)
            if good:
                st.session_state.gpt4_counter += 1
                st.session_state.gpt4_response['user_rating'] = 1
                rating_db4 = xata.records().update("model_compare", st.session_state.record_id4, {
                                                "user_rating": st.session_state.gpt4_response['user_rating']
                                                })
        with blahcol4:
            blah = st.button("🤷‍♀️", key= 5)
            if blah:
                st.session_state.gpt4_counter += 0
                st.session_state.gpt4_response['user_rating'] = 0
                rating_db4 = xata.records().update("model_compare", st.session_state.record_id4, {
                                                "user_rating": st.session_state.gpt4_response['user_rating']
                                                })
        with badcol4:
            bad = st.button("💩", key= 6)
            if bad:
                st.session_state.gpt4_counter -= 1
                st.session_state.gpt4_response['user_rating'] = -1
                rating_db4 = xata.records().update("model_compare", st.session_state.record_id4, {
                                                "user_rating": st.session_state.gpt4_response['user_rating']
                                                })
        
        gpt4_rating = scorecol4.container()
        with scorecol4:
            gpt4_rating.write(f"**Total Rating: {st.session_state.gpt4_counter}**")

        user_comment4 = st.text_input("Enter a comment about GPT-4's response:"," ")
        if st.button("Save Comment", key= "gpt4"):
            comment_db4 = xata.records().update("model_compare", st.session_state.record_id4, {
                                            "user_comment": user_comment4
                                            })


if st.session_state.gpt4_response:
    st.divider()
    with st.expander("View/Export Model Comparison Session History"):
        st.markdown(f"""
            ## Model Comparison Session History
            """, unsafe_allow_html=True)
        
        st.markdown(f"""Session Start: {st.session_state.first_prompt}""", unsafe_allow_html=True)
        start_time = pd.to_datetime(st.session_state.first_prompt)

        history = xata.sql().query(f"""
                                    SELECT  *
                                    FROM model_compare
                                    WHERE user_id = '{st.session_state.user_id}'
                                    ORDER BY timestamp;
                                """)
        chat_history = pd.DataFrame(history['records'])
        print(chat_history)
        display_columns = ['timestamp', 'prompt', 'response', 'total_cost', 'model','user_rating', 'user_comment', 'prompt_tokens', 'completion_tokens', 'total_tokens']
        chat_history = chat_history[display_columns]

        chat_history['timestamp'] = pd.to_datetime(chat_history['timestamp'])
        chat_history = chat_history[(chat_history['timestamp'] >= start_time)].sort_values(by=['timestamp'], ascending=False)
        st.dataframe(chat_history, use_container_width=True, hide_index=True)
        cost = chat_history.total_cost.sum()
        st.markdown(f"Total Session API Costs: **${cost:.7f}**")

        st.write("To export your session history to a CSV file, please enter your email address below and click the 'Download Session History' button.")
        user_email = st.text_input("Email address:","")
        if user_email:
            const.update_user_id_and_email(st.session_state.user_id, user_email, xata)
        if st.button("Export Session History"):
            download_url = const.export_compare_history(chat_history, access_key, secret_key, 'model-compare', user_email)
            if download_url:
                st.success("Your session history has successfully exported to a CSV file. Please click the link below to download the file.", icon="🎈")
                button_style = """color: white; background-color: #3b7dac; border: none; padding: 10px 20px; text-align: center; font-size: 1rem; font-weight: 700; line-height: 1.3; display: inline-block; margin: 20px 20px; cursor: pointer; border-radius: 8px; width: 200px; height: 75px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);"""

                download_button_html = f"""
                    <a href="{download_url}" target="_blank">
                        <button style="{button_style}">
                            Download <br>
                            Session History
                        </button>
                    </a>"""
                st.markdown(f"""
                    <div style="display: flex; justify-content: center;">
                    {download_button_html}
                    </div>
                    """, unsafe_allow_html=True)

st.write("#")
st.write("#")
st.divider()
st.markdown(f"""{const.support_banner}""", unsafe_allow_html=True)

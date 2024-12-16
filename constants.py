def hash_function(api_key):
    import hashlib
    h = hashlib.new("sha256")
    h.update(api_key.encode())
    return h.hexdigest()

def os_path(filepath):
    import platform
    current_os = platform.system()
    if current_os == 'Windows':
        return filepath.replace('/', '\\\\')
    else:
        return filepath.replace('\\', '/')


coffee_link = 'https://www.buymeacoffee.com/chatlab.ai'
site_title= "chat-lab.ai"
white_back_logo = 'https://chat-lab-asssets.nyc3.cdn.digitaloceanspaces.com/Chat-lab-bubble-logo-white-background-not-tail.png'


def import_logo(width, height):
    import requests
    from PIL import Image
    from io import BytesIO

    logo_url = 'https://chat-lab-asssets.nyc3.cdn.digitaloceanspaces.com/Chat-lab-bubble-logo-white-background-not-tail.png'

    response = requests.get(logo_url)
    if response.status_code == 200:
        logo_image = Image.open(BytesIO(response.content))
        new_image = logo_image.resize((width, height))
    
    return new_image



def create_new_script(template_path, output_path, replacements):
    if template_path.startswith('https://'):
        import requests
        response = requests.get(template_path)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            content = response.text
            # Normalize newline characters
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            for key, value in replacements.items():
                content = content.replace(f"userInput_{key}", value)

            with open(output_path, 'w', encoding="UTF-8") as file:
                file.write(content)
        else:
            raise Exception(f"Failed to download template: {response.status_code}")
    else:
        with open(template_path, 'r', encoding="UTF-8") as file:
            content = file.read()

        for key, value in replacements.items():
            content = content.replace(f"userInput_{key}", value)

        with open(output_path, 'w', encoding="UTF-8") as file:
            file.write(content)

def generate_filename(email, file_type):
    import random
    import string
    from datetime import datetime

    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    user_part = email.split('@')[0]

    if file_type == 'st':
        return f"{user_part}_{random_part}_{current_time}_streamlit-app.py"
    if file_type == 'csv':
        now = datetime.now()
        return f"{user_part}_{random_part}_{current_time}_model-compare.csv"


def create_and_upload_script(template_url, email, access_key, secret_key, space_name, folder_path, expiration,replacements):
    import boto3
    from botocore.client import Config
    import io
    import requests
    # Fetch the content of the template file from the URL
    response = requests.get(template_url)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        raise Exception(f"Failed to download template: {response.status_code}")

    content = response.text
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    for key, value in replacements.items():
        content = content.replace(f"userInput_{key}", value)

    unique_filename = generate_filename(email, 'st')

    # Create a session using your DigitalOcean Spaces credentials
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name='nyc3',
                            endpoint_url='https://nyc3.digitaloceanspaces.com',
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key)

    # Upload content directly to DigitalOcean Spaces
    file_object = io.BytesIO(content.encode('utf-8'))  # Create a file-like object
    full_path = f"{folder_path}/{unique_filename}"
    client.upload_fileobj(file_object, space_name, full_path)

    # Generate a presigned URL for download with expiration
    url = client.generate_presigned_url('get_object',
                                        Params={'Bucket': space_name, 'Key': full_path},
                                        ExpiresIn=expiration)  
    return url


def export_compare_history(df, access_key, secret_key, bucket_name, email):
    import boto3
    from botocore.client import Config
    from io import StringIO

    file_name = generate_filename(email, 'csv')
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name='nyc3',
                            endpoint_url='https://nyc3.digitaloceanspaces.com',
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key)



    client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

    # Generate a presigned URL for the uploaded CSV file
    url = client.generate_presigned_url('get_object',
                                        Params={'Bucket': bucket_name, 'Key': file_name},
                                        ExpiresIn=3600)

    return url


def check_or_create_user_id(email, db_client):
    import uuid
    id_check = db_client.data().query("chat_builder", {
        "columns": ["user_id", "email"], # the columns we want returned
        "filter": { "email": email }, # optional filters to apply
        }
    )
    print(f"\n    id_check['records'] = {id_check['records']} \n")
    if len(id_check['records']) == 0:
        user_id = str(uuid.uuid4())
        print(f"\n User ID: {user_id} \n")
    else:
        user_id = id_check['records'][0]['user_id']
    return user_id


def update_user_id_and_email(local_user_id, user_email, db_client):
    data = db_client.sql().query(f"""
                        SELECT  *
                        FROM keys
                        WHERE user_id = '{local_user_id}';
                    """)
    if len(data['records']) == 0:
        update_dict = {
            "user_id": local_user_id,
            "email": user_email
        }
        db = db_client.data().insert("keys", update_dict)
    if data['records'][0]['Email'] == "":
        record_id = data['records'][0]['id']
        db = db_client.records().update("keys", record_id, {"Email": user_email})
        

def check_or_create_user_key(api_key, db_client):
    import uuid
    import hashlib
    h = hashlib.new("sha256")
    h.update(api_key.encode())
    hash_key = h.hexdigest()
    print(f"Hash Key: {hash_key}")
    id_check = db_client.data().query("keys", {
        "columns": ["user_id", "api_key_hash"], 
        "filter": { "api_key_hash": hash_key }, 
        }
    )
    print(f"\n    id_check['records'] = {id_check['records']} \n")
    if len(id_check['records']) == 0:
        user_id = str(uuid.uuid4())
        print(f"\n New User ID: {user_id} \n")
    else:
        user_id = id_check['records'][0]['user_id']
        print(f"\n Existing User ID: {user_id} \n")
    return user_id

def cost(model,input,output):
    if model == 'gpt4':
        input_cost = input * (0.01/1000)
        output_cost = output * (0.03/1000)
    if model == 'gpt3':
        input_cost = input * (0.001/1000)
        output_cost = output * (0.002/1000)
    
    total_cost = input_cost + output_cost
    return total_cost


def api_query(client, prompt, llm, user_id):
    if llm == 'gpt3':
        model_choice = "gpt-3.5-turbo-1106"
    else:
        model_choice = "gpt-4-1106-preview"
    response = client.chat.completions.create(
        model=model_choice, 
        messages= [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        )
    dict = {
        'user_id': user_id,
        'chat_id': response.id,
        'model': model_choice,
        'prompt': prompt,
        'response': response.choices[0].message.content,
        'timestamp': created_at(response.created),
        'completion_tokens': response.usage.completion_tokens,
        'prompt_tokens': response.usage.prompt_tokens,
        'total_tokens': response.usage.total_tokens,
        'total_cost': cost(llm,  response.usage.prompt_tokens, response.usage.completion_tokens),
        'user_rating': 0,
        'user_comment': ""
            }
    return dict



def print_query_results(results):
    import pprint
    pprint.pprint(results)


def get_image_as_base64(url):
    import requests
    import base64    
    from PIL import Image
    from io import BytesIO
    response = requests.get(url)
    image_bytes = Image.open(BytesIO(response.content))
    return base64.b64encode(image_bytes).decode()


def bmc_button():
    import base64
    from PIL import Image, ImageOps
    import io

    def resize_image(path, size):
        with Image.open(path) as img:
            # Use Image.Resampling.LANCZOS for high-quality downsampling
            img = img.resize(size, Image.Resampling.LANCZOS)
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')
            return byte_arr.getvalue()

    size = (217, 60)  # Example size, adjust as needed
    resized_image_data = resize_image('/static/bmc-button.png', size)
    coffee_logo_base64 = base64.b64encode(resized_image_data).decode()

    html_string = f"""
                    <html>
                    <a href="https://www.buymeacoffee.com/chatlab.ai" target="_blank">
                    <img src="data:image/png;base64,{coffee_logo_base64}" alt="Buy Me A Coffee">
                    </a>
                    </html>
                    """
    return html_string


def fix_navbar():
    navbar_height = """ 
                    <style> 
                    [data-testid='stSidebarNav'] > ul { min-height: 45svh; } 
                    </style> 
                    """
    return navbar_height


def hide_st():
    hide_st_style = """
                    <style>
                    footer {visibility: hidden;}
                    </style>
                    """
    return hide_st_style


def footer(text1, text2):
    import streamlit as st
    footer_html = f"""
    <style>
    .footer {{
        position: fixed;
        left: 10;
        bottom: 0;
        width: 100%;
        background-color: rgba(241, 241, 241, 0);
        color: rgba(117, 120, 123, 1);
        text-align: left;
    }}
    </style>
    <div class='footer'>
        <p>{text1}<a href = "https://mailynfernandez.com">{text2}</a></p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


footer_text = "Made with 🧡 by "
footer_link_text = "Mailyn"


def read_markdown_file(markdown_file):
    from pathlib import Path
    return Path(markdown_file).read_text()

#css_file = os_path('static/st-style.css')
css_file = 'static/st-style.css'
nav_css = os_path('static/st-nav.css')
def load_css(file_name):
    import streamlit as st
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def created_at(date_string):
    import datetime
    created_at = int(date_string)
    date_time = datetime.datetime.fromtimestamp(created_at)
    return datetime.datetime.strftime(date_time, '%Y-%m-%d %H:%M:%S')

mobile_nav = """
    <script>
    // add classes for mobile navigation toggling
    var CSbody = document.querySelector("body");
    const CSnavbarMenu = document.querySelector("#cs-navigation");
    const CShamburgerMenu = document.querySelector("#cs-navigation .cs-toggle");

    CShamburgerMenu.addEventListener('click', function() {
        CShamburgerMenu.classList.toggle("cs-active");
        CSnavbarMenu.classList.toggle("cs-active");
        CSbody.classList.toggle("cs-open");
        // run the function to check the aria-expanded value
        ariaExpanded();
    });

    // checks the value of aria expanded on the cs-ul and changes it accordingly whether it is expanded or not 
    function ariaExpanded() {
        const csUL = document.querySelector('#cs-expanded');
        const csExpanded = csUL.getAttribute('aria-expanded');

        if (csExpanded === 'false') {
            csUL.setAttribute('aria-expanded', 'true');
        } else {
            csUL.setAttribute('aria-expanded', 'false');
        }
    }

    // mobile nav toggle code
    const dropDowns = Array.from(document.querySelectorAll('#cs-navigation .cs-dropdown'));
        for (const item of dropDowns) {
            const onClick = () => {
            item.classList.toggle('cs-active')
        }
        item.addEventListener('click', onClick)
        }
                                
    </script>
    """

nav_bar_html = """
    <div id="cs-navigation">
        <div class="cs-container">
            <!--Logo and Text-->
            <a href="https://chat-lab.ai" class="cs-logo" aria-label="back to home">
                <img src="https://chat-lab-asssets.nyc3.cdn.digitaloceanspaces.com/chat-lab-navbar-logo.png" alt="logo" width="210" height="29" aria-hidden="true" decoding="async">
            </a>
            <!--Navigation List-->
            <nav class="cs-nav" role="navigation">
                <!--Mobile Nav Toggle-->
                <button class="cs-toggle" aria-label="mobile menu toggle">
                    <div class="cs-box" aria-hidden="true">
                        <span class="cs-line cs-line1" aria-hidden="true"></span>
                        <span class="cs-line cs-line2" aria-hidden="true"></span>
                        <span class="cs-line cs-line3" aria-hidden="true"></span>
                    </div>
                </button>
                <!-- We need a wrapper div so we can set a fixed height on the cs-ul in case the nav list gets too long from too many dropdowns being opened and needs to have an overflow scroll. This wrapper acts as the background so it can go the full height of the screen and not cut off any overflowing nav items while the cs-ul stops short of the bottom of the screen, which keeps all nav items in view no matter how mnay there are-->
                <div class="cs-ul-wrapper">
                    <ul id="cs-expanded" class="cs-ul" aria-expanded="false">
                        <li class="cs-li">
                            <a href="https://chat-lab.ai" class="cs-li-link">
                                Home
                            </a>
                        </li>
                        <!--Copy and paste this cs-dropdown list item and replace any .cs-li with this cs-dropdown group to make a new dropdown and it will work-->
                        <li class="cs-li cs-dropdown" tabindex="0">
                            <span class="cs-li-link">
                                Labs
                                <img class="cs-drop-icon" src="https://csimg.nyc3.cdn.digitaloceanspaces.com/Icons%2Fdown.svg" alt="dropdown icon" width="15" height="15" decoding="async" aria-hidden="true">
                            </span>
                            <ul class="cs-drop-ul">
                                <li class="cs-drop-li">
                                    <a href="https://compare.chat-lab.ai" class="cs-li-link cs-drop-link">Model Comparison</a>
                                </li>
                                <li class="cs-drop-li">
                                    <a href="https://chat-lab.ai/completions_placeholder.html" class="cs-li-link cs-drop-link">Completions</a>
                                </li>
                                <li class="cs-drop-li">
                                    <a href="https://chat-lab.ai/assistants_placeholder.html" class="cs-li-link cs-drop-link">Assistants</a>
                                </li>
                                <li class="cs-drop-li">
                                    <a href="https://builder.chat-lab.ai" class="cs-li-link cs-drop-link">Chat Builder</a>
                                </li>
                            </ul>
                        </li>
                        <li class="cs-li">
                            <a href="https://docs.chat-lab.ai" class="cs-li-link">
                                Documentation
                            </a>
                        </li>
                        <li class="cs-li">
                            <a href="https://chat-lab.ai/blog_placeholder.html" class="cs-li-link">
                                Blog
                            </a>
                        </li>
                        <li class="cs-li">
                            <a href="https://chat-lab.ai/about_placeholder.html" class="cs-li-link">
                                About
                            </a>
                        </li>
                    </ul>
                </div>
            </nav>
            <a href="https://helper.chat-lab.ai" class="cs-button-solid cs-nav-button">Helper Chat</a>
        </div>
    </div>

    <script>
    // add classes for mobile navigation toggling
    var CSbody = document.querySelector("body");
    const CSnavbarMenu = document.querySelector("#cs-navigation");
    const CShamburgerMenu = document.querySelector("#cs-navigation .cs-toggle");

    CShamburgerMenu.addEventListener('click', function() {
        CShamburgerMenu.classList.toggle("cs-active");
        CSnavbarMenu.classList.toggle("cs-active");
        CSbody.classList.toggle("cs-open");
        // run the function to check the aria-expanded value
        ariaExpanded();
    });

    // checks the value of aria expanded on the cs-ul and changes it accordingly whether it is expanded or not 
    function ariaExpanded() {
        const csUL = document.querySelector('#cs-expanded');
        const csExpanded = csUL.getAttribute('aria-expanded');

        if (csExpanded === 'false') {
            csUL.setAttribute('aria-expanded', 'true');
        } else {
            csUL.setAttribute('aria-expanded', 'false');
        }
    }

    // mobile nav toggle code
    const dropDowns = Array.from(document.querySelectorAll('#cs-navigation .cs-dropdown'));
        for (const item of dropDowns) {
            const onClick = () => {
            item.classList.toggle('cs-active')
        }
        item.addEventListener('click', onClick)
        }
                                
    </script>
"""

support_banner = """
        <div id="support" style="text-align: center; font-size: 20px; font: Helvetica, sans-serif; color: white; background-color: #214660; padding-top: 20px; padding-bottom:20px; margin-top: 5rem; width: 100%; margin-left: 0; margin-right: 0; padding-left: 0; padding-right: 0;">
            <h3 style="color: white"> Support this project!</h3>
            <a href="https://www.buymeacoffee.com/chatlab.ai" target="_blank">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: auto; width: 217px;" >
            </a>
            <p style="font-size: 20px; padding-top: 2rem;">You can also support this project by <a style="color: inherit" href="mailto:feedback@chat-lab.ai">sending your feedback</a>.</p>
        </div>     
    """
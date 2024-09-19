import streamlit as st
import requests
import yaml
import json

# Load the custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("OpenAPI Spec Generator")
st.sidebar.header("Provide input for generating specs - ")

# Input fields
request_body = st.sidebar.text_area("Request Body", height=300)
response_body = st.sidebar.text_area("Response Body", height=300)

environment = st.sidebar.selectbox("Select Environment", ["staging", "production"])

server_urls = {
    "staging": ["https://eve.idfystaging.com", "https://api.idfystaging.com"],
    "production": ["https://eve.idfy.com", "https://api.idfy.com"]
}

url_1, url_2 = server_urls[environment]

if st.sidebar.button("Generate OpenAPI Specs"):
    if not request_body or not response_body:
        st.error("Please provide both request and response bodies.")
    else:
        try:
            with st.spinner("Generating..."):

                response_body_dict = json.loads(response_body)
                
                # Extract 'action' and 'type' fields from the parsed response body
                action = response_body_dict.get("action", "")
                task_type = response_body_dict.get("type", "")

                # Check if 'action' and 'type' are present
                if not action or not task_type:
                    st.error("The response body must contain both 'action' and 'type' fields.")
                    with open("response.txt") as res_file:
                        example_response = res_file.read()

                    st.error("Example Response Body:")
                    st.code(example_response, language='json')
                else:
                    # Define paths for sync and async APIs based on extracted values
                    sync_path = f"/v3/tasks/sync/{action}/{task_type}"
                    async_path = f"/v3/tasks/async/{action}/{task_type}"

                    payload = {
                        "query": f"""
                        Please give openapi specs of {sync_path} and {async_path} api in yaml format with nice description.
                        The request body of API is {request_body} and response body is: {response_body}.
                        Mention in the title if it's sync or async in brackets. 
                        Also, the server urls remain the same, don't forget to add these two urls:
                        - url: {url_1}
                        - url: {url_2}
                        For some fields in the request body, the text after // contains the expected data type, condition it should follow, and optional or mandatory field each separated by commas. 
                        Generate API specs considering optional and mandatory request body fields. Try to match the specs and its hierarchy given in the context and give examples.
                        Please give responses for 200, 400, 500. Provide the output in a single JSON file as a list of dictionaries with keys: specs(sync), specs(async).
                        Don't provide any extra text along with output. Give the full and complete output in JSON, not markdown.
                        """
                    }

                    # Send input data to the Flask API
                    api_url = "http://localhost:6000/generate" 

                    response = requests.post(api_url, json=payload)

                    if response.status_code == 200:
                        # Parse the response JSON
                        specs = response.json()
                        sync_specs = specs[0].get('specs(sync)', {})
                        async_specs = specs[1].get('specs(async)', {})

                        # Display the sync specs
                        st.subheader("Sync Specs")
                        st.code(yaml.dump(sync_specs, sort_keys=False), language='yaml')

                        # Display the async specs
                        st.subheader("Async Specs")
                        st.code(yaml.dump(async_specs, sort_keys=False), language='yaml')

                    else:
                        st.error("Failed to generate specs. Please check the backend or inputs.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error("Make sure you provide complete request and response body")

            # Read and display example request and response bodies from files
            try:
                with open("request.txt") as req_file:
                    example_request = req_file.read()
                with open("response.txt") as res_file:
                    example_response = res_file.read()

                st.error("Example Request Body:")
                st.code(example_request, language='json')

                st.error("Example Response Body:")
                st.code(example_response, language='json')

            except FileNotFoundError as fnf_error:
                st.error(f"File not found: {fnf_error}")
            except Exception as file_error:
                st.error(f"Error reading example files: {file_error}")

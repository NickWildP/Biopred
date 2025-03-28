import streamlit as st
import pandas as pd
from PIL import Image
import subprocess
import os
import base64
import pickle

# Molecular descriptor calculator
def desc_calc():
    try:
        # Define paths relative to the script location
        base_path = os.path.dirname(__file__)
        jar_path = os.path.join(base_path, "PaDEL-Descriptor", "PaDEL-Descriptor.jar")
        xml_path = os.path.join(base_path, "PaDEL-Descriptor", "PubchemFingerprinter.xml")
        output_file = os.path.join(base_path, "descriptors_output.csv")
        input_dir = base_path

        # Command to run PaDEL-Descriptor
        bashCommand = (
            f"java -Xms2G -Xmx2G -Djava.awt.headless=true -jar {jar_path} "
            f"-removesalt -standardizenitro -fingerprints -descriptortypes {xml_path} "
            f"-dir {input_dir} -file {output_file}"
        )
        
        # Debug: Show the command being executed
        st.write(f"Running command: {bashCommand}")
        
        # Execute the command
        process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        # Check for errors
        if process.returncode != 0:
            st.error(f"Descriptor calculation failed: {stderr.decode()}")
            return False
        
        # Clean up input file
        smi_file = os.path.join(base_path, "molecule.smi")
        if os.path.exists(smi_file):
            os.remove(smi_file)
        return True
    except Exception as e:
        st.error(f"Error in descriptor calculation: {e}")
        return False

# File download
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download Predictions</a>'
    return href

# Model building
def build_model(input_data):
    try:
        # Load the saved regression model
        base_path = os.path.dirname(__file__)
        model_path = os.path.join(base_path, "telomerase_model_latest.pkl")
        load_model = pickle.load(open(model_path, 'rb'))
        
        # Make predictions
        prediction = load_model.predict(input_data)
        st.header('**Prediction output**')
        prediction_output = pd.Series(prediction, name='pIC50')
        molecule_name = pd.Series(load_data[1], name='molecule_name')
        df = pd.concat([molecule_name, prediction_output], axis=1)
        st.write(df)
        st.markdown(filedownload(df), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error in model prediction: {e}")

# Logo image
try:
    image = Image.open('logo.png')
    st.image(image, use_column_width=True)
except FileNotFoundError:
    st.warning("Logo image not found. Please ensure 'logo.png' is in the repo.")

# Page title
st.markdown("""
# Bioactivity Prediction App (Telomerase Reverse Transcriptase)

This app predicts bioactivity against the `Telomerase Reverse Transcriptase` enzyme, a drug target for cancer.

**Credits**
- Built with `Python` + `Streamlit`
- Descriptors calculated using [PaDEL-Descriptor](http://www.yapcwsoft.com/dd/padeldescriptor/) [[Paper]](https://doi.org/10.1002/jcc.21707).
---
""")

# Sidebar
with st.sidebar:
    st.header('1. Upload your CSV data')
    uploaded_file = st.file_uploader("Upload your input file", type=['txt'])
    st.markdown("[Example input file](example_acetylcholinesterase.txt)")

if st.sidebar.button('Predict'):
    if uploaded_file is None:
        st.error("Please upload a file to proceed.")
    else:
        # Load and save input data
        load_data = pd.read_table(uploaded_file, sep=' ', header=None)
        load_data.to_csv('molecule.smi', sep='\t', header=False, index=False)

        st.header('**Original input data**')
        st.write(load_data)

        with st.spinner("Calculating descriptors..."):
            if desc_calc():
                # Read calculated descriptors
                st.header('**Calculated molecular descriptors**')
                desc = pd.read_csv('descriptors_output.csv')
                st.write(desc)
                st.write(desc.shape)

                # Subset descriptors
                st.header('**Subset of descriptors from previously built models**')
                Xlist = list(pd.read_csv('descriptor_list.csv').columns)
                desc_subset = desc[Xlist]
                st.write(desc_subset)
                st.write(desc_subset.shape)

                # Make predictions
                build_model(desc_subset)
else:
    st.info('Upload input data in the sidebar to start!')

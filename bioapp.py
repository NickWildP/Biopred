import streamlit as st
import pandas as pd
from PIL import Image
import subprocess
import os
import base64
import pickle

# Get absolute paths for important files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JAR_PATH = os.path.join(BASE_DIR, "PaDEL-Descriptor", "PaDEL-Descriptor.jar")
XML_PATH = os.path.join(BASE_DIR, "PaDEL-Descriptor", "PubchemFingerprinter.xml")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
MODEL_PATH = os.path.join(BASE_DIR, "telomerase_model_latest.pkl")

# Debugging: Check paths and working directory
st.write("Current Working Directory:", os.getcwd())
st.write("Files in Base Directory:", os.listdir(BASE_DIR))
if os.path.exists(JAR_PATH):
    st.write("✅ PaDEL-Descriptor.jar found!")
else:
    st.error("❌ PaDEL-Descriptor.jar NOT found!")

# Grant execution permission (needed for Streamlit Cloud)
subprocess.run(["chmod", "+x", JAR_PATH])

# Molecular descriptor calculator
def desc_calc():
    bashCommand = f"java -Xms2G -Xmx2G -Djava.awt.headless=true -jar {JAR_PATH} -removesalt -standardizenitro -fingerprints -descriptortypes {XML_PATH} -dir ./ -file descriptors_output.csv"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    
    # Debugging: Check for Java execution errors
    if error:
        st.error(f"❌ Error Running PaDEL-Descriptor: {error.decode()}")
    else:
        st.write("✅ Molecular descriptors calculated successfully!")

    os.remove('molecule.smi')

# File download function
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download Predictions</a>'
    return href

# Model building function
def build_model(input_data):
    try:
        with open(MODEL_PATH, 'rb') as model_file:
            load_model = pickle.load(model_file)
        prediction = load_model.predict(input_data)

        st.header('**Prediction output**')
        prediction_output = pd.Series(prediction, name='pIC50')
        molecule_name = pd.Series(load_data[1], name='molecule_name')
        df = pd.concat([molecule_name, prediction_output], axis=1)
        st.write(df)
        st.markdown(filedownload(df), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error Loading Model: {str(e)}")

# Display logo
if os.path.exists(LOGO_PATH):
    image = Image.open(LOGO_PATH)
    st.image(image, use_column_width=True)
else:
    st.warning("⚠ Logo image not found!")

# Page title
st.markdown("""
# Bioactivity Prediction App (Telomerase Reverse Transcriptase)

This app allows you to predict the bioactivity towards inhibiting the `Telomerase Reverse Transcriptase` enzyme. `TERT` is a drug target for cancer treatment.

**Credits**
- App built using `Python` + `Streamlit`
- Descriptors calculated using [PaDEL-Descriptor](http://www.yapcwsoft.com/dd/padeldescriptor/)  
[Read the Paper](https://doi.org/10.1002/jcc.21707)
---
""")

# Sidebar for file upload
with st.sidebar.header('1. Upload your CSV data'):
    uploaded_file = st.sidebar.file_uploader("Upload your input file", type=['txt'])
    st.sidebar.markdown("""
[Example input file](example_acetylcholinesterase.txt)
""")

# Predict button logic
if st.sidebar.button('Predict'):
    if uploaded_file is not None:
        load_data = pd.read_table(uploaded_file, sep=' ', header=None)
        load_data.to_csv('molecule.smi', sep='\t', header=False, index=False)

        st.header('**Original input data**')
        st.write(load_data)

        with st.spinner("Calculating descriptors..."):
            desc_calc()

        # Read in calculated descriptors and display
        st.header('**Calculated molecular descriptors**')
        try:
            desc = pd.read_csv('descriptors_output.csv')
            st.write(desc)
            st.write(desc.shape)

            # Read descriptor list from model
            st.header('**Subset of descriptors from previously built models**')
            Xlist = list(pd.read_csv('descriptor_list.csv').columns)
            desc_subset = desc[Xlist]
            st.write(desc_subset)
            st.write(desc_subset.shape)

            # Make predictions
            build_model(desc_subset)
        except Exception as e:
            st.error(f"❌ Error processing descriptors: {str(e)}")
    else:
        st.warning("⚠ Please upload a valid input file!")
else:
    st.info('Upload input data in the sidebar to start!')

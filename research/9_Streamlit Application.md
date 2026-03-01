
# 9. Streamlit Application
streamlit_app = """\"\"\"
Streamlit Demo Application for CNN Image Classification
Features: Interactive UI, batch upload, visualization, model comparison
\"\"\"

import streamlit as st
import requests
import json
from PIL import Image
import io
import base64
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os
from typing import List, Dict, Any

# Page configuration
st.set_page_config(
    page_title="CNN Image Classifier",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown(\"\"\"
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .prediction-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
    .metric-card {
        background-color: #ffffff;
        border-left: 5px solid #1f77b4;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
</style>
\"\"\", unsafe_allow_html=True)

# Constants
API_URL = os.getenv("API_URL", "http://localhost:8000")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class APIClient:
    \"\"\"Client for the inference API\"\"\"
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        \"\"\"Check API health\"\"\"
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def predict(self, image: bytes, top_k: int = 3) -> Dict[str, Any]:
        \"\"\"Send prediction request\"\"\"
        files = {"file": ("image.jpg", image, "image/jpeg")}
        params = {"top_k": top_k}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/predict",
            files=files,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def predict_batch(self, images: List[bytes], top_k: int = 3) -> Dict[str, Any]:
        \"\"\"Send batch prediction request\"\"\"
        files = [("files", (f"image_{i}.jpg", img, "image/jpeg")) 
                 for i, img in enumerate(images)]
        params = {"top_k": top_k}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/predict/batch",
            files=files,
            params=params,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    
    def get_model_info(self) -> Dict[str, Any]:
        \"\"\"Get model information\"\"\"
        response = self.session.get(f"{self.base_url}/model/info")
        return response.json()

# Initialize client
@st.cache_resource
def get_api_client():
    return APIClient(API_URL)

api_client = get_api_client()

def get_confidence_class(confidence: float) -> str:
    \"\"\"Get CSS class based on confidence\"\"\"
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def display_prediction(result: Dict[str, Any]):
    \"\"\"Display prediction result\"\"\"
    prediction = result["prediction"]
    confidence = result["confidence"]
    top_k = result.get("top_k_predictions", [])
    
    # Main prediction
    conf_class = get_confidence_class(confidence)
    st.markdown(f\"\"\"
    <div class="prediction-card">
        <h2>Prediction: {prediction}</h2>
        <h3 class="{conf_class}">Confidence: {confidence:.2%}</h3>
        <p>Inference Time: {result["inference_time_ms"]:.2f} ms</p>
        <p>Model Version: {result["model_version"]}</p>
    </div>
    \"\"\", unsafe_allow_html=True)
    
    # Top-K predictions chart
    if top_k:
        df = pd.DataFrame(top_k)
        fig = px.bar(
            df, 
            x="confidence", 
            y="class",
            orientation='h',
            color="confidence",
            color_continuous_scale="RdYlGn",
            title="Top Predictions"
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Probability distribution
    probs = result.get("probabilities", {})
    if probs:
        prob_df = pd.DataFrame([
            {"Class": k, "Probability": v} 
            for k, v in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:10]
        ])
        
        fig2 = px.pie(
            prob_df, 
            values="Probability", 
            names="Class",
            title="Probability Distribution (Top 10)"
        )
        st.plotly_chart(fig2, use_container_width=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🧠 CNN Image Classifier</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Status
        st.subheader("API Status")
        health = api_client.health_check()
        if health.get("status") == "healthy":
            st.success("✅ API Connected")
            st.json(health)
        else:
            st.error("❌ API Unavailable")
            st.json(health)
        
        # Model Info
        try:
            model_info = api_client.get_model_info()
            st.subheader("Model Information")
            st.json(model_info)
        except:
            st.warning("Could not fetch model info")
        
        # Settings
        st.subheader("Settings")
        top_k = st.slider("Top-K Predictions", 1, 10, 3)
        show_advanced = st.checkbox("Show Advanced Options")
        
        if show_advanced:
            st.text_input("API URL", value=API_URL, key="api_url")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📸 Single Image", "📁 Batch Upload", "📊 Analytics"])
    
    # Tab 1: Single Image
    with tab1:
        st.header("Single Image Classification")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose an image...",
                type=["jpg", "jpeg", "png", "webp"],
                help="Upload an image to classify"
            )
            
            if uploaded_file is not None:
                # Validate file size
                file_size = len(uploaded_file.getvalue())
                if file_size > MAX_FILE_SIZE:
                    st.error(f"File too large. Max size: {MAX_FILE_SIZE/1024/1024:.1f}MB")
                    return
                
                # Display image
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                
                # Predict button
                if st.button("🔍 Classify Image", type="primary"):
                    with st.spinner("Analyzing..."):
                        try:
                            # Reset file pointer
                            uploaded_file.seek(0)
                            result = api_client.predict(
                                uploaded_file.read(), 
                                top_k=top_k
                            )
                            
                            with col2:
                                display_prediction(result)
                                
                                # Download result
                                result_json = json.dumps(result, indent=2)
                                st.download_button(
                                    "📥 Download Result",
                                    result_json,
                                    file_name="prediction.json",
                                    mime="application/json"
                                )
                        except Exception as e:
                            st.error(f"Prediction failed: {e}")
    
    # Tab 2: Batch Upload
    with tab2:
        st.header("Batch Classification")
        
        batch_files = st.file_uploader(
            "Upload multiple images...",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload up to 32 images"
        )
        
        if batch_files:
            st.write(f"Uploaded {len(batch_files)} images")
            
            if len(batch_files) > 32:
                st.error("Maximum 32 images allowed")
            elif st.button("🔍 Classify Batch", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Processing batch..."):
                    try:
                        images = []
                        for i, file in enumerate(batch_files):
                            file.seek(0)
                            images.append(file.read())
                            progress_bar.progress((i + 1) / len(batch_files))
                        
                        start_time = time.time()
                        result = api_client.predict_batch(images, top_k=top_k)
                        elapsed = time.time() - start_time
                        
                        # Display results
                        predictions = result.get("predictions", [])
                        
                        # Summary metrics
                        cols = st.columns(4)
                        cols[0].metric("Total Images", len(predictions))
                        cols[1].metric("Total Time", f"{elapsed:.2f}s")
                        cols[2].metric("Avg Time/Image", f"{elapsed/len(predictions)*1000:.0f}ms")
                        cols[3].metric("Throughput", f"{len(predictions)/elapsed:.1f} img/s")
                        
                        # Results table
                        results_data = []
                        for i, pred in enumerate(predictions):
                            results_data.append({
                                "Image": f"Image {i+1}",
                                "Prediction": pred["prediction"],
                                "Confidence": f"{pred['confidence']:.2%}",
                                "Time (ms)": f"{pred['inference_time_ms']:.2f}"
                            })
                        
                        df_results = pd.DataFrame(results_data)
                        st.dataframe(df_results, use_container_width=True)
                        
                        # Confidence distribution
                        confidences = [p["confidence"] for p in predictions]
                        fig = px.histogram(
                            x=confidences,
                            nbins=20,
                            title="Confidence Distribution",
                            labels={"x": "Confidence", "y": "Count"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Download batch results
                        batch_json = json.dumps(result, indent=2)
                        st.download_button(
                            "📥 Download All Results",
                            batch_json,
                            file_name="batch_predictions.json",
                            mime="application/json"
                        )
                        
                    except Exception as e:
                        st.error(f"Batch prediction failed: {e}")
    
    # Tab 3: Analytics
    with tab3:
        st.header("📊 Analytics Dashboard")
        
        # Placeholder for analytics
        st.info("Analytics features coming soon:")
        st.markdown(\"\"\"
        - **Historical Predictions**: View past predictions and trends
        - **Model Performance**: Track accuracy and latency over time
        - **Data Distribution**: Analyze input image statistics
        - **Confidence Trends**: Monitor prediction confidence patterns
        \"\"\")
        
        # Sample charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Sample latency chart
            latency_data = pd.DataFrame({
                "Time": pd.date_range(start="2024-01-01", periods=24, freq="H"),
                "Latency (ms)": [45 + i*2 + (i%5)*10 for i in range(24)]
            })
            fig = px.line(latency_data, x="Time", y="Latency (ms)", 
                         title="API Latency Over Time")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sample class distribution
            class_data = pd.DataFrame({
                "Class": ["Cat", "Dog", "Bird", "Car", "Tree"],
                "Count": [150, 230, 45, 89, 67]
            })
            fig = px.bar(class_data, x="Class", y="Count", 
                        title="Prediction Class Distribution")
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
"""

with open(f"{project_root}/streamlit_app/main.py", "w") as f:
    f.write(streamlit_app)

print("✅ Streamlit application created")

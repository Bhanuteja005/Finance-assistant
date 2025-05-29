import streamlit as st
import requests
import base64
import io
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
# Add st_audiorec for voice recording
try:
    from st_audiorec import st_audiorec
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Finance Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .voice-section {
        background: #f0f2f6;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
                    color: #111 !important;

    }
    
    .assistant-message {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
        color: #111 !important;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
ORCHESTRATOR_URL = "http://localhost:8000"

class FinanceAssistantApp:
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'last_query_result' not in st.session_state:
            st.session_state.last_query_result = None
        if 'agents_status' not in st.session_state:
            st.session_state.agents_status = {}
    
    def check_orchestrator_health(self):
        """Check if the orchestrator is running."""
        try:
            response = requests.get(f"{ORCHESTRATOR_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_agents_status(self):
        """Get status of all agents."""
        try:
            response = requests.get(f"{ORCHESTRATOR_URL}/agents/status", timeout=10)
            if response.status_code == 200:
                return response.json().get("agents_status", {})
        except:
            pass
        return {}
    
    def send_text_query(self, query: str, query_type: str = None):
        """Send a text query to the orchestrator."""
        try:
            payload = {
                "query": query,
                "query_type": query_type,
                "voice_input": False
            }
            
            response = requests.post(
                f"{ORCHESTRATOR_URL}/query",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def send_voice_query(self, audio_data: bytes):
        """Send a voice query to the orchestrator."""
        try:
            # Encode audio data as base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            payload = {
                "audio_data": audio_base64
            }
            
            response = requests.post(
                f"{ORCHESTRATOR_URL}/voice-query",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def render_header(self):
        """Render the main header."""
        st.markdown('<h1 class="main-header">🎯 Multi-Agent Finance Assistant</h1>', unsafe_allow_html=True)
        st.markdown("---")
    
    def render_sidebar(self):
        """Render the sidebar with system status and controls."""
        with st.sidebar:
            st.header("🔧 System Status")
            
            # Check orchestrator health
            orchestrator_healthy = self.check_orchestrator_health()
            status_color = "🟢" if orchestrator_healthy else "🔴"
            st.write(f"{status_color} Orchestrator: {'Online' if orchestrator_healthy else 'Offline'}")
            
            if orchestrator_healthy:
                # Get agents status
                if st.button("Refresh Agent Status"):
                    st.session_state.agents_status = self.get_agents_status()
                
                if st.session_state.agents_status:
                    st.subheader("Agent Status")
                    for agent, status in st.session_state.agents_status.items():
                        status_emoji = "🟢" if status == "healthy" else "🔴"
                        st.write(f"{status_emoji} {agent.title()}: {status}")
            
            st.markdown("---")
            
            # Quick actions
            st.header("🚀 Quick Actions")
            
            if st.button("Morning Market Brief", use_container_width=True):
                query = "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
                result = self.send_text_query(query, "morning_brief")
                self.add_to_chat_history("user", query)
                self.add_to_chat_history("assistant", result)
                st.session_state.last_query_result = result
                st.rerun()
            
            if st.button("Portfolio Analysis", use_container_width=True):
                query = "Analyze my current portfolio risk and exposure"
                result = self.send_text_query(query, "portfolio_analysis")
                self.add_to_chat_history("user", query)
                self.add_to_chat_history("assistant", result)
                st.session_state.last_query_result = result
                st.rerun()
            
            if st.button("Clear Chat History", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.last_query_result = None
                st.rerun()
    
    def add_to_chat_history(self, role: str, content):
        """Add message to chat history."""
        st.session_state.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def render_voice_interface(self):
        """Render the voice interface with audio upload and playback."""
        st.markdown('<div class="voice-section">', unsafe_allow_html=True)
        st.header("🎤 Voice Interface")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("Upload a WAV or MP3 file with your question to get a spoken market brief!")
            audio_file = st.file_uploader("Upload your voice query (WAV/MP3)", type=["wav", "mp3"])
            if audio_file is not None:
                st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[-1]}')
                if st.button("Send Voice Query"):
                    with st.spinner("Processing voice query..."):
                        audio_bytes = audio_file.read()
                        result = self.send_voice_query(audio_bytes)
                        self.add_to_chat_history("user", "[Voice Query]")
                        self.add_to_chat_history("assistant", result)
                        st.session_state.last_query_result = result
                        # Play TTS response if available
                        if result and isinstance(result, dict) and result.get("voice_response"):
                            tts_audio = base64.b64decode(result["voice_response"])
                            st.audio(tts_audio, format='audio/mp3')
                        st.rerun()
        with col2:
            st.info("💡 **Try asking:**\n\n• What's our Asia tech exposure?\n• Any earnings surprises today?\n• Market sentiment analysis\n• Portfolio risk assessment")
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_text_interface(self):
        """Render the text interface."""
        st.header("💬 Text Interface")
        
        # Text input
        user_query = st.text_input(
            "Ask your finance question:",
            placeholder="e.g., What's our risk exposure in Asia tech stocks today?",
            key="text_query"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📊 Send Query", use_container_width=True):
                if user_query:
                    with st.spinner("Processing query..."):
                        result = self.send_text_query(user_query)
                        self.add_to_chat_history("user", user_query)
                        self.add_to_chat_history("assistant", result)
                        st.session_state.last_query_result = result
                        st.rerun()
        
        with col2:
            if st.button("📈 Morning Brief", use_container_width=True):
                query = "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
                with st.spinner("Generating morning brief..."):
                    result = self.send_text_query(query, "morning_brief")
                    self.add_to_chat_history("user", query)
                    self.add_to_chat_history("assistant", result)
                    st.session_state.last_query_result = result
                    st.rerun()
    
    def render_chat_history(self):
        """Render the chat history."""
        if st.session_state.chat_history:
            st.header("💭 Conversation History")
            
            for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
                role = message["role"]
                content = message["content"]
                timestamp = message["timestamp"]
                
                if role == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {content}</div>', unsafe_allow_html=True)
                else:
                    # Handle assistant response
                    if isinstance(content, dict):
                        if "error" in content:
                            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> ❌ Error: {content["error"]}</div>', unsafe_allow_html=True)
                        elif "brief" in content:
                            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {content["brief"]}</div>', unsafe_allow_html=True)
                        elif "response" in content:
                            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {content["response"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {str(content)}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {content}</div>', unsafe_allow_html=True)
    
    def render_data_visualization(self):
        """Render data visualizations if available."""
        if st.session_state.last_query_result and "data" in st.session_state.last_query_result:
            st.header("📊 Data Insights")
            
            data = st.session_state.last_query_result["data"]
            
            # Portfolio visualization
            if "portfolio" in data and data["portfolio"].get("portfolio_data"):
                st.subheader("Portfolio Exposure")
                
                portfolio_data = data["portfolio"]["portfolio_data"]
                
                # Create DataFrame
                df = pd.DataFrame(portfolio_data)
                
                if not df.empty:
                    # Pie chart for exposure
                    fig_pie = px.pie(
                        df, 
                        values='exposure_percent', 
                        names='symbol',
                        title="Portfolio Allocation by Stock"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Bar chart for performance
                    fig_bar = px.bar(
                        df, 
                        x='symbol', 
                        y='change_percent',
                        title="Daily Performance by Stock",
                        color='change_percent',
                        color_continuous_scale='RdYlGn'
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            # Earnings data
            if "earnings" in data and data["earnings"].get("earnings"):
                st.subheader("Earnings Surprises")
                
                earnings_data = data["earnings"]["earnings"]
                if earnings_data:
                    earnings_df = pd.DataFrame(earnings_data)
                    
                    if not earnings_df.empty and 'surprise_percent' in earnings_df.columns:
                        fig_earnings = px.bar(
                            earnings_df,
                            x='symbol',
                            y='surprise_percent',
                            title="Earnings Surprises (%)",
                            color='surprise_percent',
                            color_continuous_scale='RdYlGn'
                        )
                        st.plotly_chart(fig_earnings, use_container_width=True)
    
    def render_metrics_dashboard(self):
        """Render key metrics dashboard with error handling."""
        if st.session_state.last_query_result and "data" in st.session_state.last_query_result:
            data = st.session_state.last_query_result["data"]
            st.header("📈 Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            # Portfolio metrics
            if "portfolio" in data:
                portfolio = data["portfolio"]
                with col1:
                    asia_tech_exposure = portfolio.get("asia_tech_exposure", 0)
                    st.metric(
                        "Asia Tech Exposure",
                        f"{asia_tech_exposure:.1f}%",
                        delta=f"+{asia_tech_exposure - 18:.1f}%" if asia_tech_exposure > 18 else f"{asia_tech_exposure - 18:.1f}%"
                    )
                with col2:
                    total_value = portfolio.get("total_value", 0)
                    st.metric(
                        "Portfolio Value",
                        f"${total_value:,.0f}",
                        delta="$12,500"
                    )
            # Market metrics
            if "market" in data and "indices" in data["market"]:
                indices = data["market"]["indices"]
                with col3:
                    if "S&P 500" in indices:
                        sp500 = indices["S&P 500"]
                        change_pct = sp500.get("change_percent", 0)
                        st.metric(
                            "S&P 500",
                            f"{sp500.get('current_price', 0):.2f}",
                            delta=f"{change_pct:.2f}%"
                        )
                with col4:
                    if "VIX" in indices:
                        vix = indices["VIX"]
                        vix_value = vix.get("current_price", 0)
                        st.metric(
                            "VIX (Fear Index)",
                            f"{vix_value:.2f}",
                            delta=f"{vix.get('change_percent', 0):.2f}%"
                        )
    
    def run(self):
        """Main application runner."""
        self.render_header()
        self.render_sidebar()
        
        # Check if orchestrator is running
        if not self.check_orchestrator_health():
            st.error("🔴 **Orchestrator is offline!** Please start the orchestrator service first.")
            st.code("python orchestrator/main.py")
            return
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎤 Voice Interface", "💬 Text Chat", "📊 Analytics", "📈 Dashboard"])
        
        with tab1:
            self.render_voice_interface()
        
        with tab2:
            self.render_text_interface()
            st.markdown("---")
            self.render_chat_history()
        
        with tab3:
            self.render_data_visualization()
        
        with tab4:
            self.render_metrics_dashboard()

# Run the application
if __name__ == "__main__":
    app = FinanceAssistantApp()
    app.run()

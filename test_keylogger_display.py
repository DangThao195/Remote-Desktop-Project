"""
Test script to verify keylogger display functionality
"""

def test_input_pdu_structure():
    """Test the INPUT PDU structure"""
    sample_pdu = {
        "type": "input",
        "input": {
            "KeyData": "Hello World",
            "WindowTitle": "Notepad - Untitled",
            "ViewID": "DESKTOP-TEST",
            "LoggedAt": "2025-12-20 10:30:45"
        }
    }
    
    print("✅ Sample INPUT PDU:")
    print(sample_pdu)
    print()
    
    # Test extraction
    input_data = sample_pdu.get('input')
    if input_data:
        print("✅ Extracted data:")
        print(f"  KeyData: {input_data.get('KeyData')}")
        print(f"  WindowTitle: {input_data.get('WindowTitle')}")
        print(f"  ViewID: {input_data.get('ViewID')}")
        print(f"  LoggedAt: {input_data.get('LoggedAt')}")
    else:
        print("❌ Failed to extract input data")

def test_html_formatting():
    """Test HTML formatting for log display"""
    from datetime import datetime
    
    SPOTIFY_GREEN = "#1DB954"
    TEXT_LIGHT = "#FFFFFF"
    
    key_data = "def hello_world():"
    window_title = "Visual Studio Code"
    logged_at = datetime.now().strftime("%H:%M:%S")
    
    log_html = f"""
    <div style='background-color: rgba(255,255,255,0.05); 
                padding: 8px; 
                margin: 5px 0; 
                border-left: 3px solid {SPOTIFY_GREEN};
                border-radius: 4px;'>
        <div style='color: {SPOTIFY_GREEN}; font-weight: bold;'>
            🔴 [{logged_at}]
        </div>
        <div style='color: {TEXT_LIGHT}; margin: 5px 0;'>
            📱 <b>Cửa sổ:</b> {window_title}
        </div>
        <div style='color: yellow; font-family: monospace; margin: 5px 0; padding: 5px; background-color: rgba(0,0,0,0.3);'>
            ⌨️ <b>{key_data}</b>
        </div>
    </div>
    """
    
    print("\n✅ HTML formatted log:")
    print(log_html)

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 KEYLOGGER DISPLAY TEST")
    print("=" * 60)
    print()
    
    test_input_pdu_structure()
    test_html_formatting()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

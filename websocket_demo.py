#!/usr/bin/env python3
"""
Demonstration WebSocket client for HWAgent API.
Shows streaming capabilities and real-time interaction.
"""

import socketio
import sys
import time
import threading
from typing import Any, Dict


class WebSocketDemo:
    """WebSocket client demonstration for HWAgent."""
    
    def __init__(self, server_url: str = "http://127.0.0.1:5000"):
        self.server_url = server_url
        self.sio = socketio.Client()
        self.connected = False
        self.response_received = False
        self.current_response = ""
        
        # Subscribe to events
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Setup WebSocket event handlers."""
        
        @self.sio.event
        def connect():
            print("✅ Connected to WebSocket server")
            self.connected = True
        
        @self.sio.event
        def disconnect():
            print("❌ Disconnected from WebSocket server")
            self.connected = False
        
        @self.sio.event
        def stream_start(data):
            print(f"🚀 Processing started: {data.get('message', '')}")
            self.current_response = ""
        
        @self.sio.event
        def stream_chunk(data):
            if data.get('type') == 'content':
                chunk = data.get('content', '')
                self.current_response += chunk
                # Show response parts in real-time
                print(chunk, end='', flush=True)
        
        @self.sio.event
        def stream_complete(data):
            print(f"\n✅ Processing completed")
            print(f"📝 Full response received ({len(self.current_response)} characters)")
            self.response_received = True
        
        @self.sio.event
        def error(data):
            print(f"❌ Error: {data.get('message', 'Unknown error')}")
            self.response_received = True
        
        @self.sio.event
        def context_cleared(data):
            print("🗑️ Context cleared")
        
        @self.sio.event
        def context_summary(data):
            print(f"📋 Context summary: {data.get('summary', '')}")
    
    def connect_to_server(self) -> bool:
        """Connect to the server."""
        try:
            print(f"🔗 Connecting to {self.server_url}...")
            self.sio.connect(self.server_url)
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                print("✅ WebSocket connection established")
                return True
            else:
                print("❌ Failed to connect within the timeout period")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """Send a message via WebSocket."""
        if not self.connected:
            print("❌ No connection to the server")
            return False
        
        try:
            print(f"\n📤 Sending message: {message}")
            print("=" * 50)
            
            self.response_received = False
            self.sio.emit('send_message', {'message': message})
            
            # Wait for response
            timeout = 60  # 60 seconds for response
            start_time = time.time()
            
            while not self.response_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.response_received:
                print("\n" + "=" * 50)
                return True
            else:
                print(f"\n❌ Response timeout ({timeout} sec)")
                return False
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def clear_context(self):
        """Clear the context."""
        if self.connected:
            print("🗑️ Clearing context...")
            self.sio.emit('clear_context')
            time.sleep(1)
    
    def get_context(self):
        """Get the context."""
        if self.connected:
            print("📋 Requesting context...")
            self.sio.emit('get_context')
            time.sleep(1)
    
    def interactive_mode(self):
        """Interactive communication mode."""
        print("\n🎯 Interactive Mode")
        print("Enter messages to send to the agent.")
        print("Special commands:")
        print("  /clear - clear context")
        print("  /context - show context")
        print("  /quit - exit")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input == "/quit":
                    break
                elif user_input == "/clear":
                    self.clear_context()
                    continue
                elif user_input == "/context":
                    self.get_context()
                    continue
                
                # Send regular message
                self.send_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Exiting interactive mode")
                break
            except Exception as e:
                print(f"❌ Error in interactive mode: {e}")
    
    def demo_messages(self):
        """Demonstration with preset messages."""
        demo_messages_list = [
            "Hello! How are you?",
            "Can you calculate the factorial of 5?",
            "Create a file test.txt with the content 'Hello World'",
            "Explain what machine learning is in simple terms",
        ]
        
        print("\n🎬 Demo Mode - automatic message sending")
        print("=" * 50)
        
        for i, message in enumerate(demo_messages_list, 1):
            print(f"\n📝 Demo message {i}/{len(demo_messages_list)}")
            if self.send_message(message):
                time.sleep(2)  # Pause between messages
            else:
                print("❌ Error sending message, aborting demo")
                break
        
        print("\n🎬 Demo finished")
    
    def disconnect(self):
        """Disconnect from the server."""
        if self.connected:
            print("🔌 Disconnecting from server...")
            self.sio.disconnect()
            self.connected = False

def main():
    """Main function."""
    server_url_val = "http://127.0.0.1:5000"
    if len(sys.argv) > 1:
        server_url_val = sys.argv[1]
    
    print("🌐 HWAgent WebSocket Demo Client")
    print(f"Server: {server_url_val}")
    print("=" * 50)
    
    demo_client = WebSocketDemo(server_url_val)
    
    # Connect
    if not demo_client.connect_to_server():
        print("❌ Failed to connect to the server")
        sys.exit(1)
    
    try:
        # Mode selection
        print("\nSelect mode:")
        print("1. Interactive chat")
        print("2. Demonstration with preset messages")
        
        while True:
            choice = input("\nChoice (1/2): ").strip()
            if choice == "1":
                demo_client.interactive_mode()
                break
            elif choice == "2":
                demo_client.demo_messages()
                break
            else:
                print("❌ Invalid choice, try again")
    
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted by user")
    
    finally:
        demo_client.disconnect()
        print("👋 Goodbye!")


if __name__ == "__main__":
    main() 
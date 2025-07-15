import sys
import select
import threading
import queue
import time

class InputHandler:
    """
    Non-blocking input handler for interactive commands during PID control
    """
    
    def __init__(self):
        self.input_queue = queue.Queue()
        self.input_thread = None
        self.running = False
        
    def start(self):
        """Start the input handler thread"""
        self.running = True
        self.input_thread = threading.Thread(target=self._input_worker)
        self.input_thread.daemon = True
        self.input_thread.start()
        
    def stop(self):
        """Stop the input handler thread"""
        self.running = False
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)
            
    def _input_worker(self):
        """Background worker for input handling"""
        while self.running:
            try:
                # Use select for non-blocking input on Unix systems
                if sys.platform != 'win32':
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        line = sys.stdin.readline().strip()
                        if line:
                            self.input_queue.put(line)
                else:
                    # Windows implementation (basic polling)
                    try:
                        # This is a simplified approach for Windows
                        import msvcrt
                        if msvcrt.kbhit():
                            line = input().strip()
                            if line:
                                self.input_queue.put(line)
                    except ImportError:
                        # Fallback for systems without msvcrt
                        time.sleep(0.1)
                        
            except Exception as e:
                # Ignore input errors and continue
                time.sleep(0.1)
                
    def get_command(self):
        """Get command from input queue (non-blocking)"""
        try:
            return self.input_queue.get_nowait()
        except queue.Empty:
            return None
            
    def has_command(self):
        """Check if there's a command waiting"""
        return not self.input_queue.empty()
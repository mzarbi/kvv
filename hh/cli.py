import signal
from core.server import RemoteObjectServer

def handle_shutdown_signal(signum, frame):
    print("Shutdown signal received. Shutting down the server gracefully.")
    server.shutdown()

if __name__ == "__main__":
    server = RemoteObjectServer()

    # Setup signal handlers to ensure graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    # No need for try-except to catch KeyboardInterrupt
    server.start_server('127.0.0.1', 65432)